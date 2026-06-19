from src.services.b2b_client import b2b_client


# <-- ИЗМЕНЕНО: sort-enum согласно b2c/openapi.yaml
VALID_SORT_VALUES = ["price_asc", "price_desc", "popularity", "new"]


class CatalogService:
    def get_products(
        self,
        limit: int = 20,
        offset: int = 0,
        category_id: str = None,
        q: str = None,  # <-- ИЗМЕНЕНО: search → q
        sort: str = None
    ) -> dict:
        if sort and sort not in VALID_SORT_VALUES:
            raise ValueError(f"Invalid sort parameter. Allowed: {', '.join(VALID_SORT_VALUES)}")

        if q is not None:  # <-- ИЗМЕНЕНО: search → q
            if len(q) < 3:
                raise ValueError("Search query must be at least 3 characters")
            if len(q) > 255:
                raise ValueError("Search query must be at most 255 characters")

        b2b_data = b2b_client.get_products(
            limit=limit,
            offset=offset,
            category=category_id,
            search=q,  # <-- ИЗМЕНЕНО: search → q (передаём в B2B как search)
            sort=sort
        )

        items = []
        for item in b2b_data.get("items", []):
            skus = item.get("skus", [])
            min_price = min((s.get("price", 0) for s in skus if s.get("active_quantity", 0) > 0), default=0)
            has_stock = any(s.get("active_quantity", 0) > 0 for s in skus)  # <-- ИЗМЕНЕНО: in_stock → has_stock
            image = None
            for s in skus:
                if s.get("image"):
                    image = s["image"]
                    break
            if not image and item.get("images"):
                image = item["images"][0].get("url") if isinstance(item["images"][0], dict) else item["images"][0]

            items.append({
                "id": item.get("id"),
                "name": item.get("title"),  # <-- ИЗМЕНЕНО: title → name
                "image": image,
                "min_price": min_price,  # <-- ИЗМЕНЕНО: price → min_price
                "has_stock": has_stock,  # <-- ИЗМЕНЕНО: in_stock → has_stock
                "is_in_cart": False
            })

        return {
            "items": items,
            "total_count": b2b_data.get("total_count", 0),
            "limit": limit,
            "offset": offset
        }

    def get_facets(self, category_id: str = None, q: str = None) -> dict:  # <-- ИЗМЕНЕНО: добавлен q
        b2b_data = b2b_client.get_products(
            limit=100,
            offset=0,
            search=q,  # <-- ИЗМЕНЕНО: передаём q в B2B
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