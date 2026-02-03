
class SharedItem(BaseModel):
    """Items shared between users/teams"""
    __tablename__ = "shared_items"
    
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    item_type = Column(String(50), nullable=False) # trial, study, germplasm, report
    item_id = Column(String(100), nullable=False)
    
    shared_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_with_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    permission = Column(String(20), default="view") # view, edit, admin
    shared_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    organization = relationship("Organization")
    shared_by = relationship("User", foreign_keys=[shared_by_id])
    shared_with = relationship("User", foreign_keys=[shared_with_id])
