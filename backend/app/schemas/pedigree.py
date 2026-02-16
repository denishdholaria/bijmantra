from pydantic import BaseModel, Field


class PedigreeNode(BaseModel):
    id: str = Field(..., description="Unique germplasm identifier")
    label: str = Field(..., description="Display label for the germplasm")
    type: str = Field(default="germplasm", description="Node type")


class PedigreeEdge(BaseModel):
    source: str = Field(..., description="Parent germplasm identifier")
    target: str = Field(..., description="Child germplasm identifier")
