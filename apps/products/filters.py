"""
Django Filter classes for Affiliate Products API.

Provides advanced filtering capabilities for products and related models.
"""

from django.db.models import Q
from django_filters import rest_framework as filters

from .models import Brand, Category, SubCategory, Product


class BrandFilter(filters.FilterSet):
    """Filter for Brand model."""
    
    name = filters.CharFilter(method='filter_by_name', help_text='Filter by brand name (partial match)')
    is_active = filters.BooleanFilter(field_name='is_active')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Brand
        fields = ['is_active', 'slug']

    def filter_by_name(self, queryset, name, value):
        """Filter by translated name across all languages."""
        return queryset.filter(
            Q(translations__name__icontains=value)
        ).distinct()


class CategoryFilter(filters.FilterSet):
    """Filter for Category model."""
    
    name = filters.CharFilter(method='filter_by_name', help_text='Filter by category name (partial match)')
    is_active = filters.BooleanFilter(field_name='is_active')
    has_products = filters.BooleanFilter(method='filter_has_products')

    class Meta:
        model = Category
        fields = ['is_active', 'slug']

    def filter_by_name(self, queryset, name, value):
        """Filter by translated name across all languages."""
        return queryset.filter(
            Q(translations__name__icontains=value)
        ).distinct()

    def filter_has_products(self, queryset, name, value):
        """Filter categories that have active products."""
        if value:
            return queryset.filter(products__is_active=True).distinct()
        return queryset.filter(~Q(products__is_active=True)).distinct()


class SubCategoryFilter(filters.FilterSet):
    """Filter for SubCategory model."""
    
    name = filters.CharFilter(method='filter_by_name', help_text='Filter by subcategory name (partial match)')
    category = filters.NumberFilter(field_name='category_id')
    category_slug = filters.CharFilter(field_name='category__slug')
    is_active = filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = SubCategory
        fields = ['category', 'is_active', 'slug']

    def filter_by_name(self, queryset, name, value):
        """Filter by translated name across all languages."""
        return queryset.filter(
            Q(translations__name__icontains=value)
        ).distinct()


class ProductFilter(filters.FilterSet):
    """
    Comprehensive filter for Product model.
    
    Supports filtering by:
    - Text search (title, description)
    - Platform and product type
    - Brand, category, subcategory
    - Price range
    - Rating range
    - Tags
    - Date range
    - Status flags
    """
    
    # Text search
    search = filters.CharFilter(method='filter_search', help_text='Search in title and description')
    title = filters.CharFilter(method='filter_by_title', help_text='Filter by title (partial match)')
    
    # Choice filters
    platform = filters.ChoiceFilter(choices=Product.Platform.choices)
    product_type = filters.ChoiceFilter(choices=Product.ProductType.choices)
    
    # Relationship filters
    brand = filters.NumberFilter(field_name='brand_id')
    brand_slug = filters.CharFilter(field_name='brand__slug')
    category = filters.NumberFilter(field_name='category_id')
    category_slug = filters.CharFilter(field_name='category__slug')
    sub_category = filters.NumberFilter(field_name='sub_category_id')
    sub_category_slug = filters.CharFilter(field_name='sub_category__slug')
    
    # Rating filters
    min_rating = filters.NumberFilter(field_name='rating', lookup_expr='gte')
    max_rating = filters.NumberFilter(field_name='rating', lookup_expr='lte')
    has_rating = filters.BooleanFilter(method='filter_has_rating')
    
    # Price filters (searches within JSON field)
    has_discount = filters.BooleanFilter(method='filter_has_discount')
    
    # Tag filter
    tags = filters.CharFilter(method='filter_by_tags', help_text='Filter by tags (comma-separated)')
    tag = filters.CharFilter(method='filter_by_single_tag', help_text='Filter by a single tag')
    
    # Date filters
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    # Status filters
    is_active = filters.BooleanFilter(field_name='is_active')
    is_featured = filters.BooleanFilter(field_name='is_featured')
    
    # Engagement filters
    min_views = filters.NumberFilter(field_name='view_count', lookup_expr='gte')
    min_clicks = filters.NumberFilter(field_name='click_count', lookup_expr='gte')

    class Meta:
        model = Product
        fields = [
            'platform',
            'product_type',
            'brand',
            'category',
            'sub_category',
            'is_active',
            'is_featured',
            'product_asin',
        ]

    def filter_search(self, queryset, name, value):
        """
        Full-text search across title and description in all languages.
        """
        return queryset.filter(
            Q(translations__title__icontains=value) |
            Q(translations__description__icontains=value)
        ).distinct()

    def filter_by_title(self, queryset, name, value):
        """Filter by translated title across all languages."""
        return queryset.filter(
            Q(translations__title__icontains=value)
        ).distinct()

    def filter_has_rating(self, queryset, name, value):
        """Filter products that have/don't have ratings."""
        if value:
            return queryset.filter(rating__isnull=False)
        return queryset.filter(rating__isnull=True)

    def filter_has_discount(self, queryset, name, value):
        """Filter products with discounts in price_info."""
        if value:
            return queryset.filter(
                Q(price_info__has_key='discount_percent') |
                Q(price_info__has_key='savings_percent')
            ).exclude(price_info__discount_percent__isnull=True)
        return queryset.exclude(
            Q(price_info__has_key='discount_percent') |
            Q(price_info__has_key='savings_percent')
        )

    def filter_by_tags(self, queryset, name, value):
        """
        Filter by multiple tags (comma-separated).
        Returns products that have ALL specified tags.
        """
        tags = [tag.strip() for tag in value.split(',') if tag.strip()]
        for tag in tags:
            queryset = queryset.filter(tags__icontains=tag)
        return queryset

    def filter_by_single_tag(self, queryset, name, value):
        """Filter by a single tag (case-insensitive partial match)."""
        return queryset.filter(tags__icontains=value.strip())


class ProductOrderingFilter(filters.OrderingFilter):
    """
    Custom ordering filter with additional ordering options.
    """
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('fields', (
            ('created_at', 'created'),
            ('updated_at', 'updated'),
            ('rating', 'rating'),
            ('view_count', 'views'),
            ('click_count', 'clicks'),
        ))
        super().__init__(*args, **kwargs)