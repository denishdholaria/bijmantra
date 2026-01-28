from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class BudgetCategory(BaseModel):
    __tablename__ = "budget_categories"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    allocated = Column(Float, default=0.0)
    color = Column(String(50)) # e.g. "bg-blue-500"
    year = Column(Integer, nullable=False)

    # Relationships
    expenses = relationship("Expense", back_populates="budget_category")
    organization = relationship("Organization")

    @property
    def spent(self):
        return sum(e.amount for e in self.expenses) if self.expenses else 0.0

class Expense(BaseModel):
    __tablename__ = "expenses"

    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    budget_category_id = Column(Integer, ForeignKey("budget_categories.id"), nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    project = Column(String(255))

    # Relationships
    budget_category = relationship("BudgetCategory", back_populates="expenses")
    organization = relationship("Organization")
