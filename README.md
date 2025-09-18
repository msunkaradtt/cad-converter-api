-----

# CAD Converter API Service

This project provides a robust, containerized microservice for converting various 3D CAD and mesh file formats into the web-standard `.glb` (binary glTF 2.0) format. The service is designed with a scalable architecture, exposing a simple REST API for uploading files, monitoring conversion status, and downloading the results.

## Technical Architecture

The service operates as a multi-container application orchestrated by Docker Compose, ensuring a clean separation of concerns and a reproducible environment. This architecture is composed of three core services:

  * **API Service (`api`)**: A high-performance web server built with **FastAPI**. It serves as the primary user-facing component, handling all HTTP requests for file uploads, status checks, and downloads. It is responsible for receiving files and delegating the heavy computational work to the worker service.
  * **Worker Service (`worker`)**: An asynchronous task queue powered by **Celery**. This service runs in the background and is responsible for executing the computationally intensive file conversion tasks. By decoupling the conversion process from the API, the service can handle long-running jobs without blocking web requests, ensuring the API remains responsive.
  * **Broker & Backend (`redis`)**: A **Redis** container that acts as the message broker and result backend for Celery. The API service places conversion jobs onto a queue in Redis, and the worker service picks them up. Once a task is complete, the worker stores the result (success or failure) back into Redis, where the API can retrieve it for status checks.

This asynchronous, queue-based architecture is highly scalable and resilient, capable of handling multiple conversion requests simultaneously.

-----

## Conversion Pipeline & Core Technologies

The service employs a sophisticated, multi-tool pipeline to handle a variety of file formats, routing each type to the most appropriate open-source tool for optimal performance and reliability.

  * **CAD Formats (`.stp`, `.step`, `.igs`, `.iges`)**:

      * **Tool**: **FreeCAD** (in-process Python library)
      * **Process**: CAD files are first processed by the powerful FreeCAD geometry kernel. The service uses the in-process FreeCAD Python library to import the source file into a clean document, which is then exported as an intermediate, standardized `.step` file. This pre-processing step normalizes complex CAD data. The intermediate file is then passed to Trimesh for the final conversion to `.glb`.

  * **FBX Format (`.fbx`)**:

      * **Tool**: **FBX2glTF** (command-line executable)
      * **Process**: Due to the complexities of the FBX format, the service utilizes the dedicated `FBX2glTF` tool, a highly optimized open-source converter. A `subprocess` call is made from the Python worker to this tool, which performs a direct and efficient conversion from `.fbx` to the final `.glb` format. This specialized path avoids intermediate steps and ensures high-fidelity conversions.

  * **Simple Mesh Formats (`.stl`, `.obj`)**:

      * **Tool**: **Trimesh** (Python library)
      * **Process**: These standard mesh formats are handled directly by the `trimesh` library. Trimesh is highly efficient at reading, processing, and writing these formats, allowing for a fast, direct conversion to `.glb` without the need for any pre-processing.

This multi-path approach ensures that each file format is handled by the best tool for the job, maximizing reliability, performance, and the quality of the final output.

-----

## Getting Started

### Prerequisites

  * **Docker**: The service is fully containerized. You must have Docker installed and running.
  * **Docker Compose**: The multi-container environment is managed by Docker Compose.

### How to Run the Service

1.  **Clone the Repository**:

    ```bash
    git clone <your-repo-url>
    cd cad-converter-api
    ```

2.  **Build and Start the Containers**:
    From the project's root directory, execute the following command:

    ```bash
    docker-compose up --build
    ```

    This command will:

      * Build the main Docker image based on the `Dockerfile`, which includes installing all system and Python dependencies.
      * Download the official Redis image.
      * Start the `api`, `worker`, and `redis` containers in the correct order.

    The API will be available at `http://localhost:8000`.

-----

## API Usage Guide

Interact with the service using any standard HTTP client, such as `curl` or Postman.

### 1\. Upload a File for Conversion

Send a `POST` request with your 3D model to the `/convert` endpoint.

  * **Endpoint**: `POST /convert`
  * **Body**: `multipart/form-data` with a `file` key.

**Example using `curl`:**

```bash
curl -X POST -F "file=@/path/to/your/model.fbx" http://localhost:8000/convert
```

The server will respond with a unique `task_id` for tracking the job:

```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status_url": "/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

### 2\. Check Conversion Status

Use the `task_id` to poll the `/status/{task_id}` endpoint for real-time updates.

  * **Endpoint**: `GET /status/{task_id}`

**Example using `curl`:**

```bash
curl http://localhost:8000/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

  * **Possible States**:
      * **PENDING**: The task is in the queue waiting for a worker.
      * **PROGRESS**: The task has been picked up and the conversion is in progress.
      * **SUCCESS**: The conversion completed successfully. The response will include a `download_url`.
      * **FAILURE**: The conversion failed. The response will include an `error` message with technical details.

### 3\. Download the Converted File

Once the task state is `SUCCESS`, use the provided `download_url` or construct the download link with the `task_id`.

  * **Endpoint**: `GET /download/{task_id}`

**Example using `curl`:**

```bash
# The -o flag saves the output to a file
curl -o my_converted_model.glb http://localhost:8000/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

This command will save the resulting `.glb` file in your current directory.

-----

## Project Structure

```
cad-converter-api/
├── .gitignore
├── docker-compose.yml        # Orchestrates the multi-container setup
├── Dockerfile                # Defines the main application image
├── pyproject.toml            # Manages Python dependencies
├── README.md                 # This file
└── src/
    └── cad_converter_service/
        ├── __init__.py
        ├── api/
        │   └── main.py       # FastAPI application: endpoints and routing
        ├── config.py         # Shared configuration (paths, Redis URL)
        ├── converter/
        │   └── core.py       # Core conversion logic for all file types
        └── worker/
            └── tasks.py      # Celery worker task definitions
```