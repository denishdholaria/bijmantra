"""
BrAPI v2.1 Methods Endpoints
Measurement methods for observation variables

Production-ready: All data from database, no in-memory mock data.
"""

from fastapi import APIRouter, Query, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import uuid

from app.api.deps import get_db
from app.models.brapi_phenotyping import Method
from app.core.rls import set_tenant_context

router = APIRouter()


def brapi_response(result, page: int = 0, page_size: int = 1000):
    """Wraps a result in the standard BrAPI response format.

    Args:
        result: The result data to be wrapped. Can be a list or a single object.
        page (int, optional): The current page number. Defaults to 0.
        page_size (int, optional): The number of items per page. Defaults to 1000.

    Returns:
        dict: A dictionary representing the standard BrAPI response.
    """
    if isinstance(result, list):
        total = len(result)
        start = page * page_size
        end = start + page_size
        data = result[start:end]
        return {
            "metadata": {
                "datafiles": [],
                "pagination": {
                    "currentPage": page,
                    "pageSize": page_size,
                    "totalCount": total,
                    "totalPages": (total + page_size - 1) // page_size if total > 0 else 1
                },
                "status": [{"message": "Success", "messageType": "INFO"}]
            },
            "result": {"data": data}
        }
    return {
        "metadata": {
            "datafiles": [],
            "pagination": {"currentPage": 0, "pageSize": 1, "totalCount": 1, "totalPages": 1},
            "status": [{"message": "Success", "messageType": "INFO"}]
        },
        "result": result
    }


def method_to_brapi(method: Method) -> dict:
    """Converts a Method model object to a BrAPI-compliant dictionary.

    Args:
        method (Method): The Method model object to convert.

    Returns:
        dict: A dictionary representing the method in BrAPI format.
    """
    ontology_ref = None
    if method.ontology_db_id:
        ontology_ref = {
            "ontologyDbId": method.ontology_db_id,
            "ontologyName": method.ontology_name,
            "version": method.ontology_version
        }
    
    return {
        "methodDbId": method.method_db_id or str(method.id),
        "methodName": method.method_name,
        "methodPUI": method.method_pui,
        "methodClass": method.method_class,
        "description": method.description,
        "formula": method.formula,
        "reference": method.reference,
        "bibliographicalReference": method.bibliographical_reference,
        "ontologyReference": ontology_ref,
        "externalReferences": method.external_references or [],
        "additionalInfo": method.additional_info or {}
    }


@router.get("/methods")
async def get_methods(
    request: Request,
    methodDbId: Optional[str] = None,
    methodClass: Optional[str] = None,
    methodName: Optional[str] = None,
    ontologyDbId: Optional[str] = None,
    externalReferenceId: Optional[str] = None,
    externalReferenceSource: Optional[str] = None,
    page: int = Query(0, ge=0),
    pageSize: int = Query(1000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a list of methods based on filter criteria.

    Args:
        request (Request): The incoming request object.
        methodDbId (Optional[str], optional): The database ID of the method.
            Defaults to None.
        methodClass (Optional[str], optional): The class of the method.
            Defaults to None.
        methodName (Optional[str], optional): The name of the method.
            Defaults to None.
        ontologyDbId (Optional[str], optional): The database ID of the ontology.
            Defaults to None.
        externalReferenceId (Optional[str], optional): The ID of the external
            reference. Defaults to None.
        externalReferenceSource (Optional[str], optional): The source of the
            external reference. Defaults to None.
        page (int, optional): The page number for pagination. Defaults to 0.
        pageSize (int, optional): The number of items per page. Defaults to 1000.
        db (AsyncSession, optional): The database session.
            Defaults to Depends(get_db).

    Returns:
        dict: A BrAPI-compliant response containing a list of methods.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    query = select(Method)
    
    if methodDbId:
        query = query.where(Method.method_db_id == methodDbId)
    if methodClass:
        query = query.where(Method.method_class == methodClass)
    if methodName:
        query = query.where(Method.method_name.ilike(f"%{methodName}%"))
    if ontologyDbId:
        query = query.where(Method.ontology_db_id == ontologyDbId)
    
    result = await db.execute(query)
    methods = result.scalars().all()
    brapi_methods = [method_to_brapi(m) for m in methods]
    
    return brapi_response(brapi_methods, page, pageSize)


@router.get("/methods/{methodDbId}")
async def get_method(
    methodDbId: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves a single method by its database ID.

    Args:
        methodDbId (str): The database ID of the method to retrieve.
        request (Request): The incoming request object.
        db (AsyncSession, optional): The database session.
            Defaults to Depends(get_db).

    Returns:
        dict: A BrAPI-compliant response containing the method. If the method is
              not found, the response will contain an error message.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    query = select(Method).where(Method.method_db_id == methodDbId)
    result = await db.execute(query)
    method = result.scalar_one_or_none()
    
    if not method:
        try:
            method_id = int(methodDbId)
            query = select(Method).where(Method.id == method_id)
            result = await db.execute(query)
            method = result.scalar_one_or_none()
        except ValueError:
            pass
    
    if not method:
        return {
            "metadata": {
                "status": [{"message": f"Method {methodDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    return brapi_response(method_to_brapi(method))


@router.post("/methods")
async def create_methods(
    methods: List[dict],
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Creates one or more new methods.

    Args:
        methods (List[dict]): A list of dictionaries, where each dictionary
            represents a method to be created.
        request (Request): The incoming request object.
        db (AsyncSession, optional): The database session.
            Defaults to Depends(get_db).

    Returns:
        dict: A BrAPI-compliant response containing the newly created methods.

    Raises:
        HTTPException: If the user is not authenticated.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    if not org_id and not is_superuser:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    created = []
    for method_data in methods:
        ont_ref = method_data.get("ontologyReference") or {}
        new_method = Method(
            organization_id=org_id,
            method_db_id=method_data.get("methodDbId") or str(uuid.uuid4()),
            method_name=method_data.get("methodName", ""),
            method_pui=method_data.get("methodPUI"),
            method_class=method_data.get("methodClass"),
            description=method_data.get("description"),
            formula=method_data.get("formula"),
            reference=method_data.get("reference"),
            bibliographical_reference=method_data.get("bibliographicalReference"),
            ontology_db_id=ont_ref.get("ontologyDbId"),
            ontology_name=ont_ref.get("ontologyName"),
            ontology_version=ont_ref.get("version"),
            external_references=method_data.get("externalReferences", []),
            additional_info=method_data.get("additionalInfo", {})
        )
        db.add(new_method)
        await db.flush()
        created.append(method_to_brapi(new_method))
    
    await db.commit()
    return brapi_response(created)


@router.put("/methods/{methodDbId}")
async def update_method(
    methodDbId: str,
    method_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Updates an existing method.

    Args:
        methodDbId (str): The database ID of the method to update.
        method_data (dict): A dictionary containing the method data to update.
        request (Request): The incoming request object.
        db (AsyncSession, optional): The database session.
            Defaults to Depends(get_db).

    Returns:
        dict: A BrAPI-compliant response containing the updated method. If the
              method is not found, the response will contain an error message.
    """
    org_id = getattr(request.state, "organization_id", None)
    is_superuser = getattr(request.state, "is_superuser", False)
    await set_tenant_context(db, org_id, is_superuser)
    
    query = select(Method).where(Method.method_db_id == methodDbId)
    result = await db.execute(query)
    method = result.scalar_one_or_none()
    
    if not method:
        return {
            "metadata": {
                "status": [{"message": f"Method {methodDbId} not found", "messageType": "ERROR"}]
            },
            "result": None
        }
    
    if "methodName" in method_data:
        method.method_name = method_data["methodName"]
    if "methodClass" in method_data:
        method.method_class = method_data["methodClass"]
    if "description" in method_data:
        method.description = method_data["description"]
    if "formula" in method_data:
        method.formula = method_data["formula"]
    if "reference" in method_data:
        method.reference = method_data["reference"]
    if "bibliographicalReference" in method_data:
        method.bibliographical_reference = method_data["bibliographicalReference"]
    if "ontologyReference" in method_data:
        ont_ref = method_data["ontologyReference"] or {}
        method.ontology_db_id = ont_ref.get("ontologyDbId")
        method.ontology_name = ont_ref.get("ontologyName")
        method.ontology_version = ont_ref.get("version")
    if "externalReferences" in method_data:
        method.external_references = method_data["externalReferences"]
    if "additionalInfo" in method_data:
        method.additional_info = method_data["additionalInfo"]
    
    await db.commit()
    await db.refresh(method)
    
    return brapi_response(method_to_brapi(method))
