# fix(us-cat-01): каталог с фильтрами и фасетами — исправления по OpenAPI

## 🎯 Цель

Реализовать каталог товаров с фильтрами, сортировкой и фасетами. B2C проксирует запросы к B2B, который выполняет фильтрацию видимости (MODERATED + deleted=false + active_quantity>0). Исправить 6 замечаний арбитров по соответствию спецификации `b2c/openapi.yaml`.

## 🔍 Контекст

Без работающего каталога покупатель не найдёт товар — весь труд продавцов по заполнению карточек пропадёт впустую. Покупатель открывает категорию, двигает ползунок цены, выбирает «только в наличии» — и мгновенно видит список с подсчётами по каждому фильтру.

## 🔧 Исправления по фидбэку арбитров

| # | Проблема | Было | Стало |
|---|----------|------|-------|
| 1 | Поле `images` отсутствовало в ответе | `image: Optional[str]` | ✅ `images: List[ImageRef]` с полями id, url, ordering |
| 2 | B2C обращался к seller-endpoint B2B | `/api/v1/products` (требует JWT) | ✅ `/api/v1/public/products` (только X-Service-Key) |
| 3 | Проверка `len(q) < 3` блокировала валидные запросы | Проверка min_length=3 | ✅ Убрана (спецификация не задаёт minLength) |
| 4 | Параметр `category` вместо `category_id` при вызове B2B | `category` | ✅ `category_id` (по b2b/openapi.yaml:741) |
| 5 | Сортировочные значения не транслировались из B2C в B2B | `popularity`, `new` | ✅ Трансляция в `popular`, `created_desc` |
| 6 | `maxLength` для `q` был 255 вместо 200 | `maxLength=255` | ✅ `maxLength=200` |

## ✅ Что реализовано

### Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/catalog/products` | Каталог с фильтрами и сортировкой |
| GET | `/api/v1/catalog/facets` | Фасеты (подсчёты по характеристикам) |

### Query-параметры каталога
- `limit`, `offset` — пагинация
- `category_id` — фильтр по категории
- `q` — поиск по названию (maxLength=200)
- `sort` — сортировка: `price_asc`, `price_desc`, `popularity`, `new`

### Обработка ошибок
- **400 Bad Request** — невалидный `sort` (с перечислением допустимых значений)
- **422 Unprocessable Entity** — `q` длиннее 200 символов (валидация FastAPI)
- **502 Bad Gateway** — B2B недоступен

### Межсервисная авторизация
- К B2B обращаемся с заголовком `X-Service-Key`
- Используем публичный endpoint `/api/v1/public/products`

### Фасеты
- Подсчёты по характеристикам товаров (например, "Бренд": Apple, Samsung)
- Формат: `{name: "brand", values: [{value: "Apple", count: 10}, ...]}`
- Сортировка по убыванию count

## 📂 Изменения в файлах

### `src/schemas/catalog.py`
```python
# ✅ ДОБАВЛЕНО: схема ImageRef
class ImageRef(BaseModel):
    id: str
    url: str
    ordering: int

class ProductShortItem(BaseModel):
    id: str
    name: str
    images: List[ImageRef] = []  # ✅ было image: Optional[str]
    min_price: int
    has_stock: bool = True
    is_in_cart: bool = False
Тесты
platform win32 -- Python 3.12.3, pytest-7.4.3, pluggy-1.6.0 -- C:\Users\matvey_chertovikov\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\neomarket-matvey-b2c-01-02-fix-us-cat-01-final
plugins: anyio-3.7.1, asyncio-0.21.1
asyncio: mode=Mode.STRICT
collected 14 items                                                                                      

tests/test_catalog.py::TestCatalog::test_catalog_returns_filtered_sorted_products PASSED          [  7%]
tests/test_catalog.py::TestCatalog::test_facets_return_counts_per_filter_value PASSED             [ 14%]
tests/test_catalog.py::TestCatalog::test_invalid_sort_returns_400 PASSED                          [ 21%]
tests/test_catalog.py::TestCatalog::test_b2b_unavailable_returns_502 PASSED                       [ 28%]
tests/test_catalog.py::TestCatalog::test_search_returns_matching_products PASSED                  [ 42%]
tests/test_catalog.py::TestCatalog::test_short_query_returns_200 PASSED                           [ 50%]
tests/test_catalog.py::TestCatalog::test_special_chars_do_not_break_query PASSED                  [ 64%]
tests/test_catalog.py::TestCatalog::test_empty_results_returns_200 PASSED                         [ 71%]
tests/test_catalog.py::TestCatalog::test_popularity_sort_value_accepted PASSED                    [ 92%]
