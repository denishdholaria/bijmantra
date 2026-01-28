"""
Image Analysis API
Deterministic computer vision algorithms for phenotyping.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import shutil
import tempfile
import os
import base64
from typing import Optional
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
    
    # Create temp file
    suffix = os.path.splitext(file.filename)[1]
    if not suffix:
        suffix = ".png"
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
        shutil.copyfileobj(file.file, tmp_in)
        tmp_in_path = tmp_in.name
        
    tmp_out_path = tmp_in_path + "_out.png"
    
    try:
        processed_img = None
        idx = index.lower()
        
        if idx == "tgi":
            processed_img = spectral_indices.calculate_tgi(
                rgb_image_path=tmp_in_path, 
                outfile_path=tmp_out_path
            )
        elif idx == "ccc":
            processed_img = spectral_indices.calculate_ccc(
                rgb_image_path=tmp_in_path,
                outfile_path=tmp_out_path
            )
        elif idx == "ndvi":
            # Assuming composite path for single file upload
            processed_img = spectral_indices.calculate_ndvi(
                composite_path=tmp_in_path,
                outfile_path=tmp_out_path
            )
        else:
            raise HTTPException(400, f"Unsupported index: {index}. Try: tgi, ccc, ndvi")
            
        if processed_img is None:
            raise HTTPException(500, "Image processing failed (returned None). Check image format.")

        # Read back and encode
        if os.path.exists(tmp_out_path):
            with open(tmp_out_path, "rb") as f:
                img_bytes = f.read()
                b64_str = base64.b64encode(img_bytes).decode("utf-8")
                mime_type = "image/png" # opencv writes as png/jpg depending on extension, we forced png output via temp name?
                # actually calculate_* uses outfile_path extension if provided.
                # let's force png output
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
        # Cleanup
        if os.path.exists(tmp_in_path):
            os.remove(tmp_in_path)
        if os.path.exists(tmp_out_path):
            os.remove(tmp_out_path)
