import httpx
from src.config import settings


class B2BClientError(Exception):
    """Ошибка при вызове B2B."""
    pass


class B2BClient:
    def __init__(self):
        self.base_url = settings.B2B_SERVICE_URL
        self.headers = {"X-Service-Key": settings.B2B_SERVICE_KEY}

    def get_products(
        self,
        limit: int = 20,
        offset: int = 0,
        category_id: str = None,  # ✅ ИСПРАВЛЕНО: category → category_id
        search: str = None,
        sort: str = None,
        ids: str = None
    ) -> dict:
        params = {"limit": limit, "offset": offset}
        # ✅ ИСПРАВЛЕНО: category → category_id (по b2b/openapi.yaml:741)
        if category_id:
            params["category_id"] = category_id
        if search:
            params["search"] = search
        if sort:
            params["sort"] = sort
        if ids:
            params["ids"] = ids

        try:
            with httpx.Client() as client:
                # ✅ ИСПРАВЛЕНО: /api/v1/products → /api/v1/public/products
                # Публичный endpoint принимает X-Service-Key без JWT
                response = client.get(
                    f"{self.base_url}/api/v1/public/products",
                    params=params,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            raise B2BClientError(f"B2B unavailable: {e}")
        except httpx.HTTPStatusError as e:
            raise B2BClientError(f"B2B returned {e.response.status_code}")

    def get_product_by_id(self, product_id: str) -> dict:
        try:
            with httpx.Client() as client:
                # ✅ ИСПРАВЛЕНО: публичный endpoint
                response = client.get(
                    f"{self.base_url}/api/v1/public/products/{product_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.RequestError as e:
            raise B2BClientError(f"B2B unavailable: {e}")


b2b_client = B2BClient()