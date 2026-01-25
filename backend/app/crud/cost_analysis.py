from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.cost_analysis import BudgetCategory, Expense
from app.schemas.cost_analysis import (
    BudgetCategoryCreate, BudgetCategoryUpdate,
    ExpenseCreate, ExpenseUpdate
)

class CRUDBudgetCategory(CRUDBase[BudgetCategory, BudgetCategoryCreate, BudgetCategoryUpdate]):
    async def get(self, db: AsyncSession, id: int) -> Optional[BudgetCategory]:
        query = select(BudgetCategory).options(selectinload(BudgetCategory.expenses)).where(BudgetCategory.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        org_id: Optional[int] = None,
        filters: Optional[dict] = None
    ) -> Tuple[List[BudgetCategory], int]:
        query = select(BudgetCategory).options(selectinload(BudgetCategory.expenses))

        if org_id:
            query = query.where(BudgetCategory.organization_id == org_id)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar()

        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total_count

class CRUDExpense(CRUDBase[Expense, ExpenseCreate, ExpenseUpdate]):
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        org_id: Optional[int] = None,
        filters: Optional[dict] = None
    ) -> Tuple[List[Expense], int]:
        query = select(Expense).options(selectinload(Expense.budget_category))

        if org_id:
            query = query.where(Expense.organization_id == org_id)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total_count = total_result.scalar()

        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total_count

budget_category = CRUDBudgetCategory(BudgetCategory)
expense = CRUDExpense(Expense)
