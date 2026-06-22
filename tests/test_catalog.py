import pytest
from unittest.mock import patch, MagicMock


MOCK_B2B_PRODUCTS_RESPONSE = {
    "items": [
        {
            "id": "product-1",
            "title": "iPhone 15 Pro Max",
            "description": "Smartphone",
            "status": "MODERATED",
            "category": {"id": "cat-1", "name": "Electronics"},
            "images": [
                {"id": "img-1", "url": "/s3/iphone15.jpg", "ordering": 0},
                {"id": "img-2", "url": "/s3/iphone15-2.jpg", "ordering": 1}
            ],
            "characteristics": [
                {"name": "Бренд", "value": "Apple"},
                {"name": "Цвет", "value": "Чёрный"}
            ],
            "skus": [
                {
                    "id": "sku-1",
                    "name": "256GB Black",
                    "price": 12999000,
                    "discount": 0,
                    "image": "/s3/iphone15-black.jpg",
                    "active_quantity": 10,
                    "characteristics": []
                }
            ]
        },
        {
            "id": "product-2",
            "title": "Samsung Galaxy S24",
            "description": "Smartphone",
            "status": "MODERATED",
            "category": {"id": "cat-1", "name": "Electronics"},
            "images": [{"id": "img-3", "url": "/s3/s24.jpg", "ordering": 0}],
            "characteristics": [
                {"name": "Бренд", "value": "Samsung"},
                {"name": "Цвет", "value": "Белый"}
            ],
            "skus": [
                {
                    "id": "sku-2",
                    "name": "128GB White",
                    "price": 8999000,
                    "discount": 500000,
                    "image": "/s3/s24-white.jpg",
                    "active_quantity": 5,
                    "characteristics": []
                }
            ]
        }
    ],
    "total_count": 2,
    "limit": 20,
    "offset": 0
}


class TestCatalog:

    @patch('src.services.catalog_service.b2b_client.get_products')
    def test_catalog_returns_filtered_sorted_products(self, mock_get_products, client):
        """Happy path: filters, sorting, pagination work"""
        mock_get_products.return_value = MOCK_B2B_PRODUCTS_RESPONSE

        response = client.get(
            "/api/v1/catalog/products?category_id=cat-1&sort=price_asc&limit=10&offset=0"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total_count"] == 2
        assert data["limit"] == 10
        assert data["offset"] == 0
        assert data["items"][0]["name"] == "iPhone 15 Pro Max"
        assert data["items"][0]["min_price"] == 12999000
        assert data["items"][0]["has_stock"] is True
        
        # Проверяем images как массив объектов
        assert "images" in data["items"][0]
        assert isinstance(data["items"][0]["images"], list)
        assert len(data["items"][0]["images"]) == 2
        assert data["items"][0]["images"][0]["id"] == "img-1"
        assert data["items"][0]["images"][0]["url"] == "/s3/iphone15.jpg"
        assert data["items"][0]["images"][0]["ordering"] == 0

    @patch('src.services.catalog_service.b2b_client.get_products')
    def test_facets_return_counts_per_filter_value(self, mock_get_products, client):
        """Facets return correct counts"""
        mock_get_products.return_value = MOCK_B2B_PRODUCTS_RESPONSE

        response = client.get("/api/v1/catalog/facets?category_id=cat-1")

        assert response.status_code == 200
        data = response.json()
        assert data["category_id"] == "cat-1"
        assert len(data["facets"]) >= 1

        brand_facet = next((f for f in data["facets"] if f["name"] == "brand"), None)
        assert brand_facet is not None
        brand_values = {v["value"]: v["count"] for v in brand_facet["values"]}
        assert brand_values["Apple"] == 1
        assert brand_values["Samsung"] == 1

    def test_invalid_sort_returns_400(self, client):
        """Invalid sort returns 400 with allowed values"""
        response = client.get("/api/v1/catalog/products?sort=invalid_sort")

        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "INVALID_REQUEST"
        assert "price_asc" in data["message"]
        assert "price_desc" in data["message"]
        assert "popularity" in data["message"]
        assert "new" in data["message"]

    @patch('src.services.catalog_service.b2b_client.get_products')
    def test_b2b_unavailable_returns_502(self, mock_get_products, client):
        """B2B unavailable returns 502"""
        from src.services.b2b_client import B2BClientError
        mock_get_products.side_effect = B2BClientError("Connection refused")

        response = client.get("/api/v1/catalog/products")

        assert response.status_code == 502
        data = response.json()
        assert data["code"] == "BAD_GATEWAY"

    @patch('src.services.catalog_service.b2b_client.get_products')
    def test_empty_catalog_returns_200(self, mock_get_products, client):
        """Empty catalog returns 200 with empty items"""
        mock_get_products.return_value = {
            "items": [],
            "total_count": 0,
            "limit": 20,
            "offset": 0
        }

        response = client.get("/api/v1/catalog/products?category_id=empty-cat")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_count"] == 0

    @patch('src.services.catalog_service.b2b_client.get_products')
    def test_search_returns_matching_products(self, mock_get_products, client):
        """Happy path: search returns matching products"""
        mock_get_products.return_value = MOCK_B2B_PRODUCTS_RESPONSE

        response = client.get("/api/v1/catalog/products?q=iPhone")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        # ✅ ИСПРАВЛЕНО: sort=None (не передаётся в запросе)
        mock_get_products.assert_called_once_with(
            limit=20, offset=0, category_id=None, search="iPhone", sort=None
        )

    @patch('src.services.catalog_service.b2b_client.get_products')
    def test_short_query_returns_200(self, mock_get_products, client):
        """Query shorter than 3 chars → 200 (не 400)"""
        mock_get_products.return_value = {
            "items": [],
            "total_count": 0,
            "limit": 20,
            "offset": 0
        }
        response = client.get("/api/v1/catalog/products?q=ab")

        assert response.status_code == 200

    @patch('src.services.catalog_service.b2b_client.get_products')
    def test_long_query_returns_422(self, mock_get_products, client):
        """
        ✅ ИСПРАВЛЕНО: Query longer than 200 chars → 422 (не 400)
        FastAPI валидирует max_length на уровне Query и возвращает 422 Unprocessable Entity
        """
        mock_get_products.return_value = {
            "items": [],
            "total_count": 0,
            "limit": 20,
            "offset": 0
        }
        long_query = "a" * 201
        response = client.get(f"/api/v1/catalog/products?q={long_query}")

        # ✅ FastAPI возвращает 422 при нарушении max_length
        assert response.status_code == 422

    @patch('src.services.catalog_service.b2b_client.get_products')
    def test_special_chars_do_not_break_query(self, mock_get_products, client):
        """Special chars (%, _, ') don't break the query"""
        mock_get_products.return_value = {
            "items": [],
            "total_count": 0,
            "limit": 20,
            "offset": 0
        }

        response = client.get("/api/v1/catalog/products?q=product'_test%value_with_underscore")

        assert response.status_code == 200
        mock_get_products.assert_called_once()

    @patch('src.services.catalog_service.b2b_client.get_products')
    def test_empty_results_returns_200(self, mock_get_products, client):
        """No matches → 200 with empty list"""
        mock_get_products.return_value = {
            "items": [],
            "total_count": 0,
            "limit": 20,
            "offset": 0
        }

        response = client.get("/api/v1/catalog/products?q=nonexistent_product_xyz")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_count"] == 0

    @patch('src.services.catalog_service.b2b_client.get_products')
    def test_search_combined_with_category(self, mock_get_products, client):
        """Search + category_id work together"""
        mock_get_products.return_value = MOCK_B2B_PRODUCTS_RESPONSE

        response = client.get("/api/v1/catalog/products?q=iPhone&category_id=cat-1")

        assert response.status_code == 200
        # ✅ ИСПРАВЛЕНО: sort=None (не передаётся в запросе)
        mock_get_products.assert_called_once_with(
            limit=20, offset=0, category_id="cat-1", search="iPhone", sort=None
        )

    def test_new_sort_value_accepted(self, client):
        """sort=new принимается (согласно b2c/openapi.yaml)"""
        with patch('src.services.catalog_service.b2b_client.get_products') as mock_get:
            mock_get.return_value = {"items": [], "total_count": 0, "limit": 20, "offset": 0}
            response = client.get("/api/v1/catalog/products?sort=new")
            assert response.status_code == 200

    def test_popularity_sort_value_accepted(self, client):
        """sort=popularity принимается (согласно b2c/openapi.yaml)"""
        with patch('src.services.catalog_service.b2b_client.get_products') as mock_get:
            mock_get.return_value = {"items": [], "total_count": 0, "limit": 20, "offset": 0}
            response = client.get("/api/v1/catalog/products?sort=popularity")
            assert response.status_code == 200

    @patch('src.services.catalog_service.b2b_client.get_products')
    def test_sort_value_translated_to_b2b(self, mock_get_products, client):
        """Значения сортировки B2C транслируются в B2B"""
        mock_get_products.return_value = {"items": [], "total_count": 0, "limit": 20, "offset": 0}

        # B2C: popularity → B2B: popular
        response = client.get("/api/v1/catalog/products?sort=popularity")
        assert response.status_code == 200
        mock_get_products.assert_called_with(
            limit=20, offset=0, category_id=None, search=None, sort="popular"
        )

        # B2C: new → B2B: created_desc
        response = client.get("/api/v1/catalog/products?sort=new")
        assert response.status_code == 200
        mock_get_products.assert_called_with(
            limit=20, offset=0, category_id=None, search=None, sort="created_desc"
        )