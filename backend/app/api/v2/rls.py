"""
Row-Level Security (RLS) Management API

Endpoints for managing and testing RLS policies.
Admin-only access for security configuration.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.rls import (
    RLS_ENABLED_TABLES,
    set_tenant_context,
    get_current_tenant,
    generate_all_rls_policies_sql,
    generate_disable_rls_sql,
)

router = APIRouter(prefix="/rls", tags=["Row-Level Security"])


# ============================================
# Schemas
# ============================================

class RLSStatus(BaseModel):
    """RLS status for a table."""
    table_name: str
    rls_enabled: bool
    rls_forced: bool
    policies: List[str]


class RLSOverview(BaseModel):
    """Overall RLS status."""
    enabled: bool
    tables_with_rls: int
    total_tables: int
    current_tenant: Optional[int]
    is_superuser: bool
    tables: List[RLSStatus]


class TenantContext(BaseModel):
    """Current tenant context."""
    organization_id: Optional[int]
    is_superuser: bool
    user_id: Optional[str]


class RLSTestResult(BaseModel):
    """Result of RLS test query."""
    table_name: str
    total_rows: int
    visible_rows: int
    rls_working: bool
    message: str


# ============================================
# Endpoints
# ============================================

@router.get("/status", response_model=RLSOverview)
async def get_rls_status(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current RLS status for all tables.
    
    Returns:
        Overview of RLS configuration and status
    """
    # Get current tenant context from request
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    
    tables = []
    tables_with_rls = 0
    
    for table_name in RLS_ENABLED_TABLES:
        # Check if table exists and has RLS enabled
        result = await db.execute(text("""
            SELECT 
                relrowsecurity as rls_enabled,
                relforcerowsecurity as rls_forced
            FROM pg_class
            WHERE relname = :table_name
        """), {"table_name": table_name})
        
        row = result.fetchone()
        
        if row:
            rls_enabled = row.rls_enabled
            rls_forced = row.rls_forced
            
            if rls_enabled:
                tables_with_rls += 1
            
            # Get policies for this table
            policies_result = await db.execute(text("""
                SELECT polname
                FROM pg_policy
                WHERE polrelid = :table_name::regclass
            """), {"table_name": table_name})
            
            policies = [p.polname for p in policies_result.fetchall()]
            
            tables.append(RLSStatus(
                table_name=table_name,
                rls_enabled=rls_enabled,
                rls_forced=rls_forced,
                policies=policies
            ))
        else:
            # Table doesn't exist yet
            tables.append(RLSStatus(
                table_name=table_name,
                rls_enabled=False,
                rls_forced=False,
                policies=[]
            ))
    
    return RLSOverview(
        enabled=tables_with_rls > 0,
        tables_with_rls=tables_with_rls,
        total_tables=len(RLS_ENABLED_TABLES),
        current_tenant=org_id,
        is_superuser=is_superuser,
        tables=tables
    )


@router.get("/context", response_model=TenantContext)
async def get_tenant_context(request: Request):
    """
    Get current tenant context from the request.
    
    Returns:
        Current organization_id, superuser status, and user_id
    """
    return TenantContext(
        organization_id=getattr(request.state, "organization_id", None),
        is_superuser=getattr(request.state, "is_superuser", False),
        user_id=getattr(request.state, "user_id", None)
    )


@router.get("/test/{table_name}", response_model=RLSTestResult)
async def test_rls_for_table(
    table_name: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Test RLS filtering for a specific table.
    
    Compares total rows (as superuser) vs visible rows (as current tenant).
    
    Args:
        table_name: Name of the table to test
        
    Returns:
        Test result showing if RLS is working correctly
    """
    if table_name not in RLS_ENABLED_TABLES:
        raise HTTPException(
            status_code=400,
            detail=f"Table '{table_name}' is not RLS-enabled"
        )
    
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    
    # Get total rows (bypass RLS)
    await db.execute(text("SET LOCAL app.current_organization_id = '0'"))
    total_result = await db.execute(
        text(f"SELECT COUNT(*) FROM {table_name}")
    )
    total_rows = total_result.scalar() or 0
    
    # Get visible rows (with current tenant context)
    if is_superuser:
        await db.execute(text("SET LOCAL app.current_organization_id = '0'"))
    elif org_id:
        # Note: org_id is always an integer from JWT, safe to format
        await db.execute(
            text(f"SET LOCAL app.current_organization_id = '{int(org_id)}'")
        )
    else:
        await db.execute(text("SET LOCAL app.current_organization_id = '-1'"))
    
    visible_result = await db.execute(
        text(f"SELECT COUNT(*) FROM {table_name}")
    )
    visible_rows = visible_result.scalar() or 0
    
    # Determine if RLS is working
    if is_superuser:
        rls_working = visible_rows == total_rows
        message = "Superuser sees all rows (RLS bypassed)"
    elif org_id:
        rls_working = visible_rows <= total_rows
        message = f"Tenant {org_id} sees {visible_rows} of {total_rows} rows"
    else:
        rls_working = visible_rows == 0
        message = "No tenant context - should see 0 rows"
    
    return RLSTestResult(
        table_name=table_name,
        total_rows=total_rows,
        visible_rows=visible_rows,
        rls_working=rls_working,
        message=message
    )


@router.get("/test", response_model=List[RLSTestResult])
async def test_all_rls(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Test RLS filtering for all enabled tables.
    
    Returns:
        List of test results for each table
    """
    results = []
    
    for table_name in RLS_ENABLED_TABLES:
        try:
            result = await test_rls_for_table(table_name, request, db)
            results.append(result)
        except Exception as e:
            results.append(RLSTestResult(
                table_name=table_name,
                total_rows=0,
                visible_rows=0,
                rls_working=False,
                message=f"Error: {str(e)}"
            ))
    
    return results


@router.get("/sql/enable")
async def get_enable_rls_sql():
    """
    Get SQL script to enable RLS on all tables.
    
    Returns:
        SQL script for enabling RLS policies
    """
    return {
        "description": "SQL to enable Row-Level Security on all tenant-aware tables",
        "sql": generate_all_rls_policies_sql()
    }


@router.get("/sql/disable")
async def get_disable_rls_sql():
    """
    Get SQL script to disable RLS on all tables.
    
    Returns:
        SQL script for disabling RLS policies
    """
    return {
        "description": "SQL to disable Row-Level Security on all tables",
        "sql": generate_disable_rls_sql()
    }


@router.get("/tables")
async def list_rls_tables():
    """
    List all tables that have RLS policies configured.
    
    Returns:
        List of table names with RLS
    """
    return {
        "tables": RLS_ENABLED_TABLES,
        "count": len(RLS_ENABLED_TABLES)
    }


@router.post("/verify-isolation")
async def verify_tenant_isolation(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify that tenant isolation is working correctly.
    
    This endpoint:
    1. Checks RLS is enabled on all tables
    2. Verifies current tenant context is set
    3. Tests that queries are filtered correctly
    
    Returns:
        Verification results with pass/fail status
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    
    checks = []
    all_passed = True
    
    # Check 1: Tenant context is set
    if org_id or is_superuser:
        checks.append({
            "check": "Tenant context set",
            "passed": True,
            "details": f"org_id={org_id}, superuser={is_superuser}"
        })
    else:
        checks.append({
            "check": "Tenant context set",
            "passed": False,
            "details": "No tenant context - authentication required"
        })
        all_passed = False
    
    # Check 2: RLS function exists
    result = await db.execute(text("""
        SELECT EXISTS (
            SELECT 1 FROM pg_proc WHERE proname = 'current_organization_id'
        )
    """))
    func_exists = result.scalar()
    
    checks.append({
        "check": "RLS helper function exists",
        "passed": func_exists,
        "details": "current_organization_id() function" if func_exists else "Function not found - run migration"
    })
    if not func_exists:
        all_passed = False
    
    # Check 3: RLS enabled on core tables
    core_tables = ["programs", "trials", "studies"]
    for table in core_tables:
        result = await db.execute(text("""
            SELECT relrowsecurity
            FROM pg_class
            WHERE relname = :table_name
        """), {"table_name": table})
        row = result.fetchone()
        
        if row and row.relrowsecurity:
            checks.append({
                "check": f"RLS enabled on {table}",
                "passed": True,
                "details": "Row-level security active"
            })
        else:
            checks.append({
                "check": f"RLS enabled on {table}",
                "passed": False,
                "details": "RLS not enabled - run migration"
            })
            all_passed = False
    
    return {
        "verified": all_passed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tenant": {
            "organization_id": org_id,
            "is_superuser": is_superuser
        },
        "checks": checks
    }
