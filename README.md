# US-CAT-02: Текстовый поиск товаров

## Описание
Реализован текстовый поиск товаров с проксированием в B2B-сервис.

## Соответствие канон-флоу

### Happy path
- ✅ **search_returns_matching_products** — результаты по title и description
- ✅ Поиск комбинируется с фильтрами из US-CAT-01

### Unhappy path
- ✅ **short_query_returns_400** — запрос < 3 символов → 400
- ✅ **special_chars_do_not_break_query** — спецсимволы не ломают запрос
- ✅ **empty_results_returns_200** — нет совпадений → 200 с пустым списком

## Соответствие OpenAPI

- ✅ Endpoint: `GET /api/v1/catalog/products?q=...` (строка 296)
- ✅ Параметр: `q` (minLength: 3, maxLength: 200) — строки 306-309

## Исправления по замечаниям арбитра

1. Путь: `/api/v1/products` → `/api/v1/catalog/products`
2. Параметр: `search` → `q`
3. maxLength: 255 → 200 (рекомендация)

## ADR: Реализация поиска

**Выбрано:** SQL LIKE / icontains на стороне B2B.

**Критерии:**
- **Сложность на MVP:** Одна строка SQL
- **Релевантность:** Достаточно для каталога до 10k товаров

**Альтернативы:** pg_trgm (требует миграции), SearchVector (сложно для MVP).

## Лог тестов
tests/test_catalog.py::TestCatalog::test_catalog_returns_filtered_sorted_products PASSED      [  7%]
tests/test_catalog.py::TestCatalog::test_facets_return_counts_per_filter_value PASSED         [ 15%]
tests/test_catalog.py::TestCatalog::test_invalid_sort_returns_400 PASSED                      [ 23%]
tests/test_catalog.py::TestCatalog::test_b2b_unavailable_returns_502 PASSED                   [ 30%]
tests/test_catalog.py::TestCatalog::test_empty_catalog_returns_200 PASSED                     [ 38%]
tests/test_catalog.py::TestCatalog::test_search_returns_matching_products PASSED              [ 46%]
tests/test_catalog.py::TestCatalog::test_short_query_returns_400 PASSED                       [ 53%]
tests/test_catalog.py::TestCatalog::test_long_query_returns_400 PASSED                        [ 61%]
tests/test_catalog.py::TestCatalog::test_special_chars_do_not_break_query PASSED              [ 69%]
tests/test_catalog.py::TestCatalog::test_empty_results_returns_200 PASSED                     [ 76%]
tests/test_catalog.py::TestCatalog::test_search_combined_with_category PASSED                 [ 84%]
tests/test_catalog.py::TestCatalog::test_new_sort_value_accepted PASSED                       [ 92%]
tests/test_catalog.py::TestCatalog::test_popularity_sort_value_accepted PASSED     
