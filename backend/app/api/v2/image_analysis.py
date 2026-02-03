"""
Image Analysis API
Deterministic computer vision algorithms for phenotyping.
"""

import asyncio
import base64
import functools
import os
import shutil
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.phenotyping import spectral_indices


router = APIRouter(prefix="/image-analysis", tags=["Image Analysis"])

@router.post("/spectral-indices")
async def analyze_spectral_indices(
    file: UploadFile = File(...),
    index: str = Form(..., description="Index to calculate: tgi, vari, ccc, ndvi"),
):
    """
    Calculate spectral indices from an uploaded image.
    
    Supported Indices:
    - **TGI** (Triangular Greenness Index): RGB only. GOOD for Chlorophyll.
    - **VARI** (Visible Atmospherically Resistant Index): RGB only. GOOD for vegetation fraction.
    - **CCC** (Canopy Cover Crop): RGB only. GOOD for identifying green pixel area.
    - **NDVI** (Normalized Difference Vegetation Index): Requires NIR.
      *Assumption*: Input image is composite where Blue channel = NIR, Green = Red.
      (Common in modified consumer cameras).
    """

    loop = asyncio.get_running_loop()

    # Create temp file
    suffix = os.path.splitext(file.filename)[1]
    if not suffix:
        suffix = ".png"

    tmp_in_path = None
    tmp_out_path = None

    try:
        # 1. Blocking I/O: Create temp file and write uploaded content in thread
        def create_and_save_upload(upload_file, file_suffix: str) -> str:
            fd, path = tempfile.mkstemp(suffix=file_suffix)
            try:
                with os.fdopen(fd, "wb") as buffer:
                    shutil.copyfileobj(upload_file, buffer)
            except Exception:
                try:
                    os.remove(path)
                except OSError:
                    pass
                raise
            return path

        tmp_in_path = await loop.run_in_executor(None, create_and_save_upload, file.file, suffix)
        tmp_out_path = tmp_in_path + "_out.png"

        processed_img = None
        idx = index.lower()

        # 2. CPU/Blocking I/O: Image Processing
        if idx == "tgi":
            processed_img = await loop.run_in_executor(
                None,
                functools.partial(
                    spectral_indices.calculate_tgi,
                    rgb_image_path=tmp_in_path,
                    outfile_path=tmp_out_path
                )
            )
        elif idx == "ccc":
            processed_img = await loop.run_in_executor(
                None,
                functools.partial(
                    spectral_indices.calculate_ccc,
                    rgb_image_path=tmp_in_path,
                    outfile_path=tmp_out_path
                )
            )
        elif idx == "ndvi":
            # Assuming composite path for single file upload
            processed_img = await loop.run_in_executor(
                None,
                functools.partial(
                    spectral_indices.calculate_ndvi,
                    composite_path=tmp_in_path,
                    outfile_path=tmp_out_path
                )
            )
        else:
            raise HTTPException(400, f"Unsupported index: {index}. Try: tgi, ccc, ndvi")

        if processed_img is None:
            raise HTTPException(500, "Image processing failed (returned None). Check image format.")

        # 3. Blocking I/O: Read back and encode
        # Check existence in thread as well to be safe (though os.path.exists is fast usually)
        if await loop.run_in_executor(None, os.path.exists, tmp_out_path):
            def read_and_encode(path: str) -> str:
                with open(path, "rb") as f:
                    img_bytes = f.read()
                    return base64.b64encode(img_bytes).decode("utf-8")

            b64_str = await loop.run_in_executor(None, read_and_encode, tmp_out_path)

            return {
                "success": True,
                "index": idx,
                "image_data": f"data:image/png;base64,{b64_str}"
            }
        else:
            raise HTTPException(500, "Output file creation failed.")

    except Exception as e:
        raise HTTPException(500, str(e))

    finally:
        # 4. Blocking I/O: Cleanup
        def cleanup(paths: list[str]):
            for p in paths:
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass

        await loop.run_in_executor(None, cleanup, [tmp_in_path, tmp_out_path])
