
"""
Image Analysis API

Endpoints for processing field images.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import numpy as np
import cv2
import io
import logging

from app.api import deps
from app.services.image_analysis import image_analysis_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/stats", response_model=Dict[str, float])
async def analyze_image_stats(
    file: UploadFile = File(..., description="Image file (JPG/PNG)"),
    method: str = "exg_otsu",
    current_user: Any = Depends(deps.get_current_active_user),
):
    """
    Upload an image and get phenotypic statistics.
    - Canopy Coverage %
    - Mean ExG (Greenness)
    - Mean VARI
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
        
    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise HTTPException(status_code=400, detail="Could not decode image")
            
        # Convert BGR (OpenCV default) to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Analyze
        stats = image_analysis_service.extract_plot_metrics(img_rgb)
        
        return stats
        
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/segment", response_class=JSONResponse)
async def segment_image(
    file: UploadFile = File(...),
    method: str = "exg_otsu",
    current_user: Any = Depends(deps.get_current_active_user),
):
    """
    Returns segmented mask as binary list (simplified for now, 
    production should return image blob).
    """
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        mask = image_analysis_service.segment_plants(img_rgb, method=method)
        
        # For simplicity in this JSON API, returning coverage stats.
        # Returning full mask array is too heavy for JSON.
        # In real app, we would return a PNG blob.
        
        coverage = (cv2.countNonZero(mask) / mask.size) * 100
        
        return JSONResponse(content={
            "filename": file.filename,
            "method": method,
            "canopy_coverage_percent": coverage,
            "mask_shape": mask.shape
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
