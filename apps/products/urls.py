"""
URL configuration for Affiliate Products API.

Uses DRF routers for automatic URL generation.
Product detail views use slug instead of pk.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    BrandViewSet,
    CategoryViewSet,
    SubCategoryViewSet,
    ProductViewSet,
)


class CustomRouter(DefaultRouter):
    """
    Custom router that uses slug for product detail views.
    """
    pass


# Create router and register viewsets
router = DefaultRouter()

# Brands - uses pk for lookup
router.register(r'brands', BrandViewSet, basename='brand')

# Categories - uses pk for lookup
router.register(r'categories', CategoryViewSet, basename='category')

# Subcategories - uses pk for lookup
router.register(r'subcategories', SubCategoryViewSet, basename='subcategory')

# Products - uses slug for lookup (configured in ViewSet)
router.register(r'products', ProductViewSet, basename='product')

app_name = 'products'

urlpatterns = [
    path('', include(router.urls)),
]


"""
Generated URL Patterns:

BRANDS:
  GET    /api/v1/brands/                    - List all brands
  POST   /api/v1/brands/                    - Create a brand
  GET    /api/v1/brands/{id}/               - Get brand by ID
  PUT    /api/v1/brands/{id}/               - Update brand
  PATCH  /api/v1/brands/{id}/               - Partial update brand
  DELETE /api/v1/brands/{id}/               - Delete brand
  GET    /api/v1/brands/{id}/products/      - Get brand's products

CATEGORIES:
  GET    /api/v1/categories/                - List all categories
  POST   /api/v1/categories/                - Create a category
  GET    /api/v1/categories/{id}/           - Get category by ID
  PUT    /api/v1/categories/{id}/           - Update category
  PATCH  /api/v1/categories/{id}/           - Partial update category
  DELETE /api/v1/categories/{id}/           - Delete category
  GET    /api/v1/categories/{id}/products/  - Get category's products
  GET    /api/v1/categories/with_subcategories/ - Get categories with subcategories

SUBCATEGORIES:
  GET    /api/v1/subcategories/             - List all subcategories
  POST   /api/v1/subcategories/             - Create a subcategory
  GET    /api/v1/subcategories/{id}/        - Get subcategory by ID
  PUT    /api/v1/subcategories/{id}/        - Update subcategory
  PATCH  /api/v1/subcategories/{id}/        - Partial update subcategory
  DELETE /api/v1/subcategories/{id}/        - Delete subcategory
  GET    /api/v1/subcategories/{id}/products/ - Get subcategory's products

PRODUCTS (uses SLUG for detail views):
  GET    /api/v1/products/                  - List all products
  POST   /api/v1/products/                  - Create a product
  GET    /api/v1/products/{slug}/           - Get product by SLUG
  PUT    /api/v1/products/{slug}/           - Update product
  PATCH  /api/v1/products/{slug}/           - Partial update product
  DELETE /api/v1/products/{slug}/           - Delete product
  GET    /api/v1/products/{slug}/related/   - Get related products
  POST   /api/v1/products/{slug}/track-click/ - Track affiliate click
  POST   /api/v1/products/{slug}/regenerate-slug/ - Regenerate slug from title
  
  GET    /api/v1/products/featured/         - Get featured products
  GET    /api/v1/products/stats/            - Get product statistics
  GET    /api/v1/products/platforms/        - Get platform choices
  GET    /api/v1/products/product-types/    - Get product type choices
  GET    /api/v1/products/by-asin/{asin}/   - Get product by ASIN
  POST   /api/v1/products/bulk-action/      - Bulk operations
"""