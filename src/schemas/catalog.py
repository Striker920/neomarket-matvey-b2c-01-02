from pydantic import BaseModel, Field
from typing import List, Optional, Any
from uuid import UUID


# ✅ ДОБАВЛЕНО: схема ImageRef по спецификации b2c/openapi.yaml:1040,1061-1063
class ImageRef(BaseModel):
    """Ссылка на изображение товара."""
    id: str
    url: str
    ordering: int


class ProductShortItem(BaseModel):
    id: str
    name: str  # title → name ✅
    # ✅ ИСПРАВЛЕНО: image: Optional[str] → images: List[ImageRef]
    images: List[ImageRef] = []
    min_price: int  # price → min_price ✅
    has_stock: bool = True  # in_stock → has_stock ✅
    is_in_cart: bool = False


class ProductShortListResponse(BaseModel):
    items: List[ProductShortItem] = []
    total_count: int = 0
    limit: int = 20
    offset: int = 0


class FacetValue(BaseModel):
    value: str
    count: int


class FacetItem(BaseModel):
    name: str
    values: List[FacetValue]


class FacetsResponse(BaseModel):
    category_id: Optional[str] = None
    facets: List[FacetItem] = []