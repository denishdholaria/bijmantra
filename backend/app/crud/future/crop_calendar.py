"""
CRUD operations for Crop Calendar
"""

from app.crud.base import CRUDBase
from app.models.future.crop_calendar import CropCalendar
from app.schemas.future.crop_calendar import CropCalendarCreate, CropCalendarUpdate

class CRUDCropCalendar(CRUDBase[CropCalendar, CropCalendarCreate, CropCalendarUpdate]):
    """CRUD operations for CropCalendar"""
    pass

crop_calendar = CRUDCropCalendar(CropCalendar)
