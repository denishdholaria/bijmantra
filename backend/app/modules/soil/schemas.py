from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


# NutrientTest
class NutrientTestBase(BaseModel):
    field_id: int
    sample_date: date
    nitrogen: float | None = None
    phosphorus: float | None = None
    potassium: float | None = None
    ph: float | None = None

class NutrientTestCreate(NutrientTestBase):
    pass

class NutrientTest(NutrientTestBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

# PhysicalProperties
class PhysicalPropertiesBase(BaseModel):
    field_id: int
    date: date
    texture_class: str | None = None
    bulk_density: float | None = None

class PhysicalPropertiesCreate(PhysicalPropertiesBase):
    pass

class PhysicalProperties(PhysicalPropertiesBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

# MicrobialActivity
class MicrobialActivityBase(BaseModel):
    field_id: int
    date: date
    respiration_rate: float | None = None

class MicrobialActivityCreate(MicrobialActivityBase):
    pass

class MicrobialActivity(MicrobialActivityBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

# AmendmentLog
class AmendmentLogBase(BaseModel):
    field_id: int
    date: date
    amendment_type: str
    amount: float
    unit: str

class AmendmentLogCreate(AmendmentLogBase):
    pass

class AmendmentLog(AmendmentLogBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

# SoilMap
class SoilMapBase(BaseModel):
    field_id: int
    date: date
    map_type: str
    image_url: str

class SoilMapCreate(SoilMapBase):
    pass

class SoilMap(SoilMapBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
