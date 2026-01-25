from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Budget Category Schemas
class BudgetCategoryBase(BaseModel):
    name: str
    allocated: float
    color: str = "bg-blue-500"
    year: int

class BudgetCategoryCreate(BudgetCategoryBase):
    pass

class BudgetCategoryUpdate(BaseModel):
    name: Optional[str] = None
    allocated: Optional[float] = None
    color: Optional[str] = None
    year: Optional[int] = None

class BudgetCategory(BudgetCategoryBase):
    id: int
    organization_id: int
    spent: float = 0.0 # Calculated field

    class Config:
        from_attributes = True

# Expense Schemas
class ExpenseBase(BaseModel):
    budget_category_id: int
    description: str
    amount: float
    date: datetime
    project: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    budget_category_id: Optional[int] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[datetime] = None
    project: Optional[str] = None

class Expense(ExpenseBase):
    id: int
    organization_id: int
    category_name: Optional[str] = None

    class Config:
        from_attributes = True

# Summary Schema
class CostAnalysisSummary(BaseModel):
    total_budget: float
    total_spent: float
    remaining: float
    utilization_rate: float
