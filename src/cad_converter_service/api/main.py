# src/cad_converter_service/api/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from celery.result import AsyncResult
import uuid
import os # <-- Added os import

# --- FIX: Import the task AND the celery_app instance ---
from ..worker.tasks import conversion_task, celery_app
from ..config import UPLOAD_DIR, CONVERTED_DIR

app = FastAPI(title="CAD Conversion Service")

@app.post("/convert", status_code=202)
def start_conversion(file: UploadFile = File(...)):
    """
    Endpoint to upload a file and start the conversion process.
    Returns a task ID to check the status.
    """
    try:
        # Save the uploaded file with a unique name to avoid conflicts
        unique_suffix = uuid.uuid4().hex
        # A safer way to handle filenames without extensions
        original_stem = os.path.splitext(file.filename)[0]
        original_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{original_stem}_{unique_suffix}{original_ext}"
        
        save_path = UPLOAD_DIR / unique_filename
        with open(save_path, "wb") as buffer:
            buffer.write(file.file.read())

        # Start the background conversion task
        task = conversion_task.delay(unique_filename)
        return {"task_id": task.id, "status_url": f"/status/{task.id}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")

@app.get("/status/{task_id}")
def get_status(task_id: str):
    """
    Endpoint to check the status of a conversion task.
    """
    # --- FIX: Use the imported 'celery_app' instance ---
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "state": task_result.state,
        "details": task_result.info,
    }
    
    if task_result.state == 'SUCCESS':
        response['download_url'] = f"/download/{task_id}"

    return response

@app.get("/download/{task_id}")
def download_result(task_id: str):
    """
    Endpoint to download the converted .glb file.
    """
    # --- FIX: Use the imported 'celery_app' instance ---
    task_result = AsyncResult(task_id, app=celery_app)

    if not task_result.successful():
        raise HTTPException(status_code=404, detail="Task not complete or failed.")

    result_info = task_result.get()
    file_path = result_info.get('result_path')
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Converted file not found.")

    return FileResponse(path=file_path, media_type='model/gltf-binary', filename=os.path.basename(file_path))

@app.get("/")
def read_root():
    return {"message": "Welcome to the CAD Converter API!"}