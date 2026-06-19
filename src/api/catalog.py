from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from src.schemas.catalog import ProductShortListResponse, FacetsResponse
from src.services.catalog_service import catalog_service, VALID_SORT_VALUES

# <-- ИЗМЕНЕНО: prefix теперь /api/v1/catalog (согласно b2c/openapi.yaml:296)
router = APIRouter(prefix="/api/v1/catalog", tags=["Catalog"])


@router.get("/products", response_model=ProductShortListResponse)
def get_products(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category_id: Optional[str] = None,
    q: Optional[str] = Query(None),  # <-- ИЗМЕНЕНО: search → q
    sort: Optional[str] = None,
):
    try:
        result = catalog_service.get_products(
            limit=limit,
            offset=offset,
            category_id=category_id,
            q=q,  # <-- ИЗМЕНЕНО: search → q
            sort=sort
        )
        return result
    except ValueError as e:
        # <-- ИСПРАВЛЕНО: правильная структура try/except
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_REQUEST", "message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "BAD_GATEWAY", "message": "B2B service unavailable"}
        )


@router.get("/facets", response_model=FacetsResponse)  # <-- ИЗМЕНЕНО: /catalog/facets → /facets
def get_facets(
    category_id: Optional[str] = None,
    q: Optional[str] = Query(None),  # <-- ИЗМЕНЕНО: search → q
):
    try:
        result = catalog_service.get_facets(category_id=category_id, q=q)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "BAD_GATEWAY", "message": "B2B service unavailable"}
        )