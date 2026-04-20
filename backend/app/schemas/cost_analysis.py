from datetime import datetime

from pydantic import BaseModel, ConfigDict


# Budget Category Schemas
class BudgetCategoryBase(BaseModel):
    name: str
    allocated: float
    color: str = "bg-blue-500"
    year: int

class BudgetCategoryCreate(BudgetCategoryBase):
    pass

class BudgetCategoryUpdate(BaseModel):
    name: str | None = None
    allocated: float | None = None
    color: str | None = None
    year: int | None = None

class BudgetCategory(BudgetCategoryBase):
    id: int
    organization_id: int
    spent: float = 0.0 # Calculated field

    model_config = ConfigDict(from_attributes=True)

# Expense Schemas
class ExpenseBase(BaseModel):
    budget_category_id: int
    description: str
    amount: float
    date: datetime
    project: str | None = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    budget_category_id: int | None = None
    description: str | None = None
    amount: float | None = None
    date: datetime | None = None
    project: str | None = None

class Expense(ExpenseBase):
    id: int
    organization_id: int
    category_name: str | None = None

    model_config = ConfigDict(from_attributes=True)

# Summary Schema
class CostAnalysisSummary(BaseModel):
    total_budget: float
    total_spent: float
    remaining: float
    utilization_rate: float
