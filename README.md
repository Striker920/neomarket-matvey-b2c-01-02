# Исправление US-CAT-01: соответствие b2c/openapi.yaml

## Описание
Реализованы исправления для полного соответствия спецификации `b2c/openapi.yaml`.

## Внесённые исправления

### 1. Путь endpoint
`GET /api/v1/products` → `GET /api/v1/catalog/products` (согласно b2c/openapi.yaml:296)

### 2. Query-параметр поиска
`search` → `q` (согласно b2c/openapi.yaml:306-309)

### 3. Sort-enum
Приведён к спецификации: `[price_asc, price_desc, popularity, new]`
Удалены недокументированные значения: `rating`, `date_desc`, `discount_desc`

### 4. Поля ответа (CatalogProductCard)
- `title` → `name`
- `price` → `min_price`
- `in_stock` → `has_stock`

## ADR: Расчёт фасетов

**Контекст:** Для каждого фильтра нужно вернуть подсчёт товаров.

**Рассмотренные альтернативы:**
1. SQL GROUP BY на каждый запрос
2. Кэш фасетов с TTL
3. Денормализованные счётчики в отдельной таблице

**Выбрано:** Вариант 1 (SQL GROUP BY) для MVP.

**Критерии:**
- **Консистентность данных:** Всегда актуальные данные
- **Нагрузка на БД:** Приемлема для каталога до 10k товаров

## Лог тестов
platform win32 -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\matvey_chertovikov\AppData\Lo
cachedir: .pytest_cache
rootdir: C:\US-B2C\US-B2C-01
collected 13 items                                                                                  
tests/test_catalog.py::TestCatalog::test_catalog_returns_filtered_sorted_products PASSED      [  7%]
tests/test_catalog.py::TestCatalog::test_b2b_unavailable_returns_502 PASSED                   [ 30%]
tests/test_catalog.py::TestCatalog::test_short_query_returns_400 PASSED                       [ 53%]
tests/test_catalog.py::TestCatalog::test_long_query_returns_400 PASSED                        [ 61%]
tests/test_catalog.py::TestCatalog::test_empty_results_returns_200 PASSED                     [ 76%]
tests/test_catalog.py::TestCatalog::test_search_combined_with_category PASSED                 [ 84%]
tests/test_catalog.py::TestCatalog::test_new_sort_value_accepted PASSED                       [ 92%]
tests/test_catalog.py::TestCatalog::test_popularity_sort_value_accepted PASSED 
