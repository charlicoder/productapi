# Affiliate Products REST API

A Django REST Framework API for managing affiliate products with multi-language support (English, Arabic, French).

## Features

- **Multi-language Support**: Full translation support for product data using django-parler
- **Comprehensive Filtering**: Filter by platform, category, brand, tags, price, rating, and more
- **Search Functionality**: Full-text search across translated fields
- **Caching**: Built-in response caching for performance
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Pagination**: Configurable page-based pagination
- **Bulk Operations**: Perform actions on multiple products at once
- **Statistics Endpoint**: Aggregate product statistics

## Tech Stack

- Django 4.2+
- Django REST Framework 3.14+
- django-parler (translations)
- django-filter (advanced filtering)
- drf-spectacular (OpenAPI docs)
- PostgreSQL (recommended)

## Installation

### 1. Clone and Setup Virtual Environment

```bash
cd affiliate_api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

## API Documentation

Access interactive API documentation:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- OpenAPI Schema: `http://localhost:8000/api/schema/`

## API Endpoints

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/products/` | List all products |
| POST | `/api/v1/products/` | Create a product |
| GET | `/api/v1/products/{id}/` | Get product details |
| PUT | `/api/v1/products/{id}/` | Update a product |
| PATCH | `/api/v1/products/{id}/` | Partial update |
| DELETE | `/api/v1/products/{id}/` | Delete a product |
| GET | `/api/v1/products/featured/` | Get featured products |
| GET | `/api/v1/products/stats/` | Get statistics |
| GET | `/api/v1/products/platforms/` | Get platform choices |
| GET | `/api/v1/products/product_types/` | Get product type choices |
| GET | `/api/v1/products/by-asin/{asin}/` | Get product by ASIN |
| POST | `/api/v1/products/{id}/track_click/` | Track affiliate click |
| GET | `/api/v1/products/{id}/related/` | Get related products |
| POST | `/api/v1/products/bulk_action/` | Bulk operations |

### Brands

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/brands/` | List all brands |
| POST | `/api/v1/brands/` | Create a brand |
| GET | `/api/v1/brands/{id}/` | Get brand details |
| PUT | `/api/v1/brands/{id}/` | Update a brand |
| DELETE | `/api/v1/brands/{id}/` | Delete a brand |
| GET | `/api/v1/brands/{id}/products/` | Get brand's products |

### Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/categories/` | List all categories |
| POST | `/api/v1/categories/` | Create a category |
| GET | `/api/v1/categories/{id}/` | Get category details |
| GET | `/api/v1/categories/with_subcategories/` | Categories with subcategories |
| GET | `/api/v1/categories/{id}/products/` | Get category's products |

### Subcategories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/subcategories/` | List all subcategories |
| POST | `/api/v1/subcategories/` | Create a subcategory |
| GET | `/api/v1/subcategories/{id}/` | Get subcategory details |
| GET | `/api/v1/subcategories/{id}/products/` | Get subcategory's products |

## Filtering & Search

### Product Filters

```bash
# By platform
GET /api/v1/products/?platform=amazon

# By product type
GET /api/v1/products/?product_type=electronics

# By brand
GET /api/v1/products/?brand=1
GET /api/v1/products/?brand_slug=apple

# By category
GET /api/v1/products/?category=1
GET /api/v1/products/?category_slug=electronics

# By rating
GET /api/v1/products/?min_rating=4.0&max_rating=5.0

# By tags
GET /api/v1/products/?tags=phone,apple
GET /api/v1/products/?tag=smartphone

# By status
GET /api/v1/products/?is_active=true&is_featured=true

# By date
GET /api/v1/products/?created_after=2024-01-01

# Search
GET /api/v1/products/?search=iphone

# Ordering
GET /api/v1/products/?ordering=-rating
GET /api/v1/products/?ordering=-created_at
```

## Multi-Language Support

### Request translations via Accept-Language header:

```bash
# English (default)
curl -H "Accept-Language: en" http://localhost:8000/api/v1/products/

# Arabic
curl -H "Accept-Language: ar" http://localhost:8000/api/v1/products/

# French
curl -H "Accept-Language: fr" http://localhost:8000/api/v1/products/
```

### Or via query parameter:

```bash
GET /api/v1/products/?lang=ar
```

## Creating a Product

### Request Body Example:

```json
{
  "product_asin": "B0CS2X23RY",
  "platform": "amazon",
  "af_link": "https://www.amazon.com/dp/B0CS2X23RY?tag=myaffiliate-20",
  "translations": {
    "en": {
      "title": "BAGSMART Lightweight Puffy Tote Bag for Women",
      "description": "This BAGSMART Tote Bag for women is the perfect companion...",
      "shipping": "$28.10 Shipping & Import Charges to Qatar",
      "returns": null
    },
    "ar": {
      "title": "حقيبة توت خفيفة الوزن للنساء",
      "description": "حقيبة توت باجسمارت للنساء هي الرفيق المثالي..."
    },
    "fr": {
      "title": "Sac fourre-tout léger pour femmes",
      "description": "Ce sac fourre-tout BAGSMART pour femmes..."
    }
  },
  "price_info": {
    "price": "$26.59",
    "regular_price": "$31.99",
    "cost_savings": 5,
    "discount_percent": "-17%",
    "savings_percent": "17%"
  },
  "rating": "4.7",
  "brand": 1,
  "category": 1,
  "sub_category": 1,
  "product_type": "clothing",
  "features": [
    {"key": "Fabric type", "value": "Polyester fibre"},
    {"key": "Care instructions", "value": "Machine Wash"},
    {"key": "Origin", "value": "Imported"}
  ],
  "images": [
    {
      "image": "https://m.media-amazon.com/images/I/51k6GQbjoVL._AC_SY550_.jpg",
      "alt_text": "BAGSMART Tote Bag Front View",
      "is_featured": true,
      "order": 1
    }
  ],
  "videos": [
    {
      "video": "https://www.amazon.com/f5aae4a0-60e1-484b-8473-802c0e45ca6e",
      "title": "Product Overview",
      "is_featured": true,
      "order": 1
    }
  ],
  "tags_list": ["Women", "Handbags & Wallets", "Totes"],
  "meta": {
    "page_header": "BAGSMART Lightweight Puffy Tote Bag for Women",
    "meta_description": "Explore the BAGSMART lightweight puffy tote bag...",
    "meta_keywords": "BAGSMART, tote bag, women's bag",
    "open_graph_meta_description": "Discover the BAGSMART tote bag for women...",
    "product_tags": "#BAGSMART #ToteBag #WomensBag"
  },
  "is_active": true,
  "is_featured": false
}
```

## Bulk Operations

```json
POST /api/v1/products/bulk_action/
{
  "product_ids": [1, 2, 3, 4, 5],
  "action": "activate"  // activate, deactivate, feature, unfeature, delete
}
```

## Pagination

```json
{
  "pagination": {
    "count": 150,
    "total_pages": 8,
    "current_page": 1,
    "page_size": 20,
    "next": "http://localhost:8000/api/v1/products/?page=2",
    "previous": null
  },
  "results": [...]
}
```

Configure page size: `?page_size=50` (max: 100)

## Models Structure

```
┌─────────────────┐     ┌─────────────────┐
│     Brand       │     │    Category     │
├─────────────────┤     ├─────────────────┤
│ id              │     │ id              │
│ name (i18n)     │     │ name (i18n)     │
│ description     │     │ description     │
│ slug            │     │ slug            │
│ url             │     │ icon            │
│ logo            │     │ order           │
│ is_active       │     │ is_active       │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │              ┌────────┴────────┐
         │              │  SubCategory    │
         │              ├─────────────────┤
         │              │ id              │
         │              │ name (i18n)     │
         │              │ category (FK)   │
         │              │ slug            │
         │              └────────┬────────┘
         │                       │
         └──────────┬────────────┘
                    │
           ┌────────┴────────┐
           │    Product      │
           ├─────────────────┤
           │ id              │
           │ product_asin    │
           │ platform        │
           │ af_link         │
           │ title (i18n)    │
           │ description     │
           │ price_info (JSON)│
           │ features (JSON) │
           │ images (JSON)   │
           │ videos (JSON)   │
           │ meta (JSON)     │
           │ tags (text)     │
           │ rating          │
           │ brand (FK)      │
           │ category (FK)   │
           │ sub_category (FK)│
           │ product_type    │
           │ is_active       │
           │ is_featured     │
           └─────────────────┘
```

## Database Indexes

Optimized indexes for common query patterns:
- `platform + is_active`
- `product_type + is_active`
- `category + is_active`
- `brand + is_active`
- `rating + is_active`
- `created_at + is_active`
- `is_active + is_featured`

## Running Tests

```bash
python manage.py test products
```

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Configure PostgreSQL database
3. Set up Redis for caching (optional but recommended)
4. Run with Gunicorn: `gunicorn config.wsgi:application`
5. Use Nginx as reverse proxy
6. Enable HTTPS

## License

MIT License