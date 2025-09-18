# src/cad_converter_service/converter/core.py
import trimesh
import os
import shutil
import tempfile
import subprocess

import FreeCAD
import Import
import Part

from ..config import DATA_DIR

class ConversionError(Exception):
    pass

def convert_file_to_glb(input_path: str, output_path: str):
    """
    Handles conversion using a dedicated path for each format type:
    - FreeCAD for CAD files
    - FBX2glTF for FBX files
    - Trimesh for simple meshes
    """
    file_ext = os.path.splitext(input_path)[1].lower()
    
    # Define categories for different file types
    CAD_FORMATS = {'.stp', '.step', '.igs', '.iges'}
    FBX_FORMAT = {'.fbx'}
    DIRECT_MESH_FORMATS = {'.stl', '.obj'}
    
    SUPPORTED_FORMATS = CAD_FORMATS.union(FBX_FORMAT).union(DIRECT_MESH_FORMATS)

    if file_ext not in SUPPORTED_FORMATS:
        raise ConversionError(f"Unsupported file format: '{file_ext}'.")

    temp_dir = tempfile.mkdtemp(dir=(DATA_DIR / "temp"))
    doc = None

    try:
        # --- PATH 1: FreeCAD for complex CAD files ---
        if file_ext in CAD_FORMATS:
            print(f"--- Detected CAD format ({file_ext}). Using FreeCAD. ---")
            temp_step_path = os.path.join(temp_dir, "intermediate.step")
            
            Import.open(input_path)
            doc = FreeCAD.ActiveDocument

            if not doc or not doc.Objects:
                raise ConversionError(f"FreeCAD failed to read geometry from: {input_path}")
            
            shape_objects = [obj for obj in doc.Objects if hasattr(obj, 'Shape')]
            if not shape_objects:
                raise ConversionError("No importable shapes found.")

            Import.export(shape_objects, temp_step_path)
            
            print(f"--- Loading intermediate STEP with Trimesh... ---")
            scene = trimesh.load(temp_step_path, force='scene')
            scene.export(file_obj=output_path)

        # --- PATH 2: FBX2glTF for FBX files ---
        elif file_ext in FBX_FORMAT:
            print(f"--- Detected FBX format. Using FBX2glTF. ---")
            output_dir = os.path.dirname(output_path)
            output_filename = os.path.basename(output_path)
            
            # The tool needs the output path without the extension
            output_name_without_ext = os.path.splitext(output_path)[0]

            command = [
                "FBX2glTF",
                "-i", input_path,
                "-o", output_name_without_ext,
                "-b"  # Flag for binary .glb output
            ]

            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            print(f"--- Successfully converted FBX to GLB. ---")

        # --- PATH 3: Trimesh for simple mesh files ---
        elif file_ext in DIRECT_MESH_FORMATS:
            print(f"--- Detected simple mesh format ({file_ext}). Using Trimesh directly. ---")
            scene = trimesh.load(input_path, force='scene')
            scene.export(file_obj=output_path)
    
    except subprocess.CalledProcessError as e:
        error_details = (
            f"FBX2glTF execution failed.\n"
            f"--- Stderr ---\n{e.stderr or 'Empty'}\n"
            f"--- Stdout ---\n{e.stdout or 'Empty'}"
        )
        raise ConversionError(error_details)
    except Exception as e:
        raise ConversionError(f"Conversion process failed: {repr(e)}")
    finally:
        if doc:
            FreeCAD.closeDocument(doc.Name)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)