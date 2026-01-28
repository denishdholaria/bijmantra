from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_organization_id, get_current_active_user
from app.crud import cost_analysis as crud
from app.schemas import cost_analysis as schemas
from app.models.core import User

router = APIRouter(prefix="/cost-analysis", tags=["Cost Analysis"])

# Budget Categories
@router.get("/budget-categories", response_model=List[schemas.BudgetCategory])
async def list_budget_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    records, _ = await crud.budget_category.get_multi(db, skip=skip, limit=limit, org_id=org_id)
    return records

@router.post("/budget-categories", response_model=schemas.BudgetCategory)
async def create_budget_category(
    record_in: schemas.BudgetCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    record = await crud.budget_category.create(
        db, obj_in=record_in, org_id=current_user.organization_id
    )
    # Re-fetch to load relationships for 'spent' property
    return await crud.budget_category.get(db, id=record.id)

@router.put("/budget-categories/{id}", response_model=schemas.BudgetCategory)
async def update_budget_category(
    id: int,
    record_in: schemas.BudgetCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    record = await crud.budget_category.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Budget Category not found")
    record = await crud.budget_category.update(db, db_obj=record, obj_in=record_in)
    # Re-fetch to load relationships for 'spent' property
    return await crud.budget_category.get(db, id=record.id)

@router.delete("/budget-categories/{id}", status_code=204)
async def delete_budget_category(
    id: int,
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    record = await crud.budget_category.get(db, id=id)
    if not record or record.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Budget Category not found")
    await crud.budget_category.delete(db, id=id)
    return None

# Expenses
@router.get("/expenses", response_model=List[schemas.Expense])
async def list_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    records, _ = await crud.expense.get_multi(db, skip=skip, limit=limit, org_id=org_id)
    # Populate category_name
    for record in records:
        if record.budget_category:
            record.category_name = record.budget_category.name
    return records

@router.post("/expenses", response_model=schemas.Expense)
async def create_expense(
    record_in: schemas.ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Verify budget category exists and belongs to org
    category = await crud.budget_category.get(db, id=record_in.budget_category_id)
    if not category or category.organization_id != current_user.organization_id:
        raise HTTPException(status_code=400, detail="Invalid Budget Category")

    record = await crud.expense.create(
        db, obj_in=record_in, org_id=current_user.organization_id
    )
    # Populate category name for response
    record.category_name = category.name
    return record

# Summary
@router.get("/summary", response_model=schemas.CostAnalysisSummary)
async def get_summary(
    db: AsyncSession = Depends(get_db),
    org_id: int = Depends(get_organization_id)
):
    categories, _ = await crud.budget_category.get_multi(db, limit=1000, org_id=org_id)

    total_budget = sum(c.allocated for c in categories)
    total_spent = sum(c.spent for c in categories)
    remaining = total_budget - total_spent
    utilization_rate = (total_spent / total_budget * 100) if total_budget > 0 else 0

    return schemas.CostAnalysisSummary(
        total_budget=total_budget,
        total_spent=total_spent,
        remaining=remaining,
        utilization_rate=utilization_rate
    )
