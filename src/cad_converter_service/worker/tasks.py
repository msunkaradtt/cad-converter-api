# src/cad_converter_service/worker/tasks.py
from celery import Celery
from ..config import REDIS_URL, UPLOAD_DIR, CONVERTED_DIR
from ..converter.core import convert_file_to_glb, ConversionError

celery_app = Celery(__name__, broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_track_started=True,
)

@celery_app.task(bind=True)
def conversion_task(self, original_filename: str):
    """
    Final robust version: Lets Celery handle exceptions naturally.
    """
    input_path = UPLOAD_DIR / original_filename
    output_path = CONVERTED_DIR / f"{input_path.stem}.glb"

    try:
        self.update_state(state='PROGRESS', meta={'status': 'Starting conversion...'})
        convert_file_to_glb(str(input_path), str(output_path))
        return {'status': 'SUCCESS', 'result_path': str(output_path)}
        
    except ConversionError as e:
        # Let Celery handle the exception. It will automatically mark the task
        # as FAILED and store the exception information correctly.
        raise e