from src.services.b2b_client import b2b_client, B2BClientError
from src.schemas.catalog import ImageRef


# ✅ ИСПРАВЛЕНО: sort-enum согласно b2c/openapi.yaml
VALID_SORT_VALUES = ["price_asc", "price_desc", "popularity", "new"]

# ✅ ДОБАВЛЕНО: маппинг значений сортировки B2C → B2B
# B2C принимает: popularity, new
# B2B ожидает: popular, created_desc (по b2b/openapi.yaml:744)
SORT_VALUE_MAPPING = {
    "price_asc": "price_asc",
    "price_desc": "price_desc",
    "popularity": "popular",   # ✅ Трансляция
    "new": "created_desc",      # ✅ Трансляция
}


class CatalogService:
    def get_products(
        self,
        limit: int = 20,
        offset: int = 0,
        category_id: str = None,
        q: str = None,
        sort: str = None
    ) -> dict:
        if sort and sort not in VALID_SORT_VALUES:
            raise ValueError(f"Invalid sort parameter. Allowed: {', '.join(VALID_SORT_VALUES)}")

        # ✅ ИСПРАВЛЕНО: убрана проверка len(q) < 3 (спецификация не задаёт minLength)
        # ✅ ИСПРАВЛЕНО: maxLength = 200 вместо 255 (по b2c/openapi.yaml:308)
        if q is not None:
            if len(q) > 200:
                raise ValueError("Search query must be at most 200 characters")

        # ✅ ДОБАВЛЕНО: трансляция sort-значений B2C → B2B
        b2b_sort = None
        if sort:
            b2b_sort = SORT_VALUE_MAPPING.get(sort, sort)

        b2b_data = b2b_client.get_products(
            limit=limit,
            offset=offset,
            category_id=category_id,  # ✅ ИСПРАВЛЕНО: category_id вместо category
            search=q,
            sort=b2b_sort  # ✅ Передаём транслированное значение
        )

        items = []
        for item in b2b_data.get("items", []):
            skus = item.get("skus", [])
            min_price = min((s.get("price", 0) for s in skus if s.get("active_quantity", 0) > 0), default=0)
            has_stock = any(s.get("active_quantity", 0) > 0 for s in skus)
            
            # ✅ ИСПРАВЛЕНО: формируем images как List[ImageRef] вместо image: str
            images = []
            b2b_images = item.get("images", [])
            for idx, img in enumerate(b2b_images):
                if isinstance(img, dict):
                    images.append(ImageRef(
                        id=img.get("id", str(idx)),
                        url=img.get("url", ""),
                        ordering=img.get("ordering", idx),
                    ))
                elif isinstance(img, str):
                    images.append(ImageRef(
                        id=str(idx),
                        url=img,
                        ordering=idx,
                    ))

            items.append({
                "id": item.get("id"),
                "name": item.get("title"),
                "images": [img.model_dump() for img in images],  # ✅ images вместо image
                "min_price": min_price,
                "has_stock": has_stock,
                "is_in_cart": False
            })

        return {
            "items": items,
            "total_count": b2b_data.get("total_count", 0),
            "limit": limit,
            "offset": offset
        }

    def get_facets(self, category_id: str = None, q: str = None) -> dict:
        b2b_data = b2b_client.get_products(
            limit=100,
            offset=0,
            category_id=category_id,  # ✅ ИСПРАВЛЕНО: category_id вместо category
            search=q,
        )

        brand_counts = {}
        for item in b2b_data.get("items", []):
            for char in item.get("characteristics", []):
                if char.get("name") == "Бренд":
                    brand = char.get("value", "Unknown")
                    brand_counts[brand] = brand_counts.get(brand, 0) + 1

        facets = []
        if brand_counts:
            facets.append({
                "name": "brand",
                "values": [{"value": k, "count": v} for k, v in sorted(brand_counts.items(), key=lambda x: -x[1])]
            })

        return {
            "category_id": category_id,
            "facets": facets
        }


catalog_service = CatalogService()