"""
Django REST Framework ViewSets for Affiliate Products API.

Provides full CRUD operations with filtering, pagination, and caching.
"""

from django.db.models import Avg, Count, Sum, Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import Brand, Category, SubCategory, Product
from .serializers import (
    BrandSerializer,
    BrandNestedSerializer,
    CategorySerializer,
    CategoryListSerializer,
    CategoryWithSubcategoriesSerializer,
    SubCategorySerializer,
    SubCategoryListSerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    BulkProductSerializer,
    ProductStatsSerializer,
)
from .filters import BrandFilter, CategoryFilter, SubCategoryFilter, ProductFilter
from .pagination import StandardResultsPagination, LargeResultsPagination


@extend_schema_view(
    list=extend_schema(
        summary="List all brands",
        description="Returns a paginated list of all brands with optional filtering.",
        parameters=[
            OpenApiParameter(
                name="lang",
                description="Language code (en, ar, fr)",
                required=False,
                type=str,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Get brand details",
        description="Returns detailed information about a specific brand.",
    ),
    create=extend_schema(
        summary="Create a new brand",
        description="Creates a new brand with translations.",
    ),
    update=extend_schema(
        summary="Update a brand", description="Updates an existing brand."
    ),
    partial_update=extend_schema(
        summary="Partial update a brand", description="Partially updates a brand."
    ),
    destroy=extend_schema(summary="Delete a brand", description="Deletes a brand."),
)
class BrandViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Brand CRUD operations.

    Supports multi-language responses via Accept-Language header or lang parameter.
    """

    queryset = Brand.objects.all()
    filterset_class = BrandFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]
    pagination_class = StandardResultsPagination
    lookup_field = "pk"

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return BrandNestedSerializer
        return BrandSerializer

    def get_queryset(self):
        """Filter queryset based on active status for non-staff users."""
        queryset = super().get_queryset()
        # Optionally filter by active status
        if self.action == "list" and not getattr(self.request.user, "is_staff", False):
            queryset = queryset.filter(is_active=True)
        return queryset

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    @method_decorator(vary_on_headers("Accept-Language"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=["get"])
    def products(self, request, pk=None):
        """Get all products for a specific brand."""
        brand = self.get_object()
        products = brand.products.filter(is_active=True).prefetch_related(
            "translations"
        )
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = ProductListSerializer(
            products, many=True, context={"request": request}
        )
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List all categories",
        description="Returns a paginated list of all categories with optional filtering.",
    ),
    retrieve=extend_schema(summary="Get category details"),
    create=extend_schema(summary="Create a new category"),
    update=extend_schema(summary="Update a category"),
    partial_update=extend_schema(summary="Partial update a category"),
    destroy=extend_schema(summary="Delete a category"),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category CRUD operations.
    """

    queryset = Category.objects.prefetch_related("translations", "subcategories").all()
    filterset_class = CategoryFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["translations__name", "slug"]
    ordering_fields = ["order", "created_at"]
    ordering = ["order", "translations__name"]
    pagination_class = StandardResultsPagination

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return CategoryListSerializer
        if self.action == "with_subcategories":
            return CategoryWithSubcategoriesSerializer
        return CategorySerializer

    def get_queryset(self):
        """Filter queryset based on active status."""
        queryset = super().get_queryset()
        if self.action == "list":
            queryset = queryset.filter(is_active=True)
        return queryset

    @method_decorator(cache_page(60 * 10))  # Cache for 10 minutes
    @method_decorator(vary_on_headers("Accept-Language"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get categories with subcategories",
        description="Returns all categories with their nested subcategories.",
    )
    @action(detail=False, methods=["get"])
    def with_subcategories(self, request):
        """Get all categories with their subcategories nested."""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = CategoryWithSubcategoriesSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def products(self, request, pk=None):
        """Get all products in a specific category."""
        category = self.get_object()
        products = category.products.filter(is_active=True).prefetch_related(
            "translations"
        )
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = ProductListSerializer(
            products, many=True, context={"request": request}
        )
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary="List all subcategories"),
    retrieve=extend_schema(summary="Get subcategory details"),
    create=extend_schema(summary="Create a new subcategory"),
    update=extend_schema(summary="Update a subcategory"),
    partial_update=extend_schema(summary="Partial update a subcategory"),
    destroy=extend_schema(summary="Delete a subcategory"),
)
class SubCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SubCategory CRUD operations.
    """

    queryset = (
        SubCategory.objects.select_related("category")
        .prefetch_related("translations")
        .all()
    )
    filterset_class = SubCategoryFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["translations__name", "slug"]
    ordering_fields = ["order", "created_at"]
    ordering = ["order"]
    pagination_class = StandardResultsPagination

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return SubCategoryListSerializer
        return SubCategorySerializer

    def get_queryset(self):
        """Filter queryset based on active status."""
        queryset = super().get_queryset()
        if self.action == "list":
            queryset = queryset.filter(is_active=True)
        return queryset

    @action(detail=True, methods=["get"])
    def products(self, request, pk=None):
        """Get all products in a specific subcategory."""
        subcategory = self.get_object()
        products = subcategory.products.filter(is_active=True).prefetch_related(
            "translations"
        )
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = ProductListSerializer(
            products, many=True, context={"request": request}
        )
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List all products",
        description="Returns a paginated list of products with comprehensive filtering options.",
        parameters=[
            OpenApiParameter(
                name="lang",
                description="Language code (en, ar, fr)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="search",
                description="Search in title and description",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="platform",
                description="Filter by platform",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="product_type",
                description="Filter by product type",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="brand", description="Filter by brand ID", required=False, type=int
            ),
            OpenApiParameter(
                name="category",
                description="Filter by category ID",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="min_rating",
                description="Minimum rating",
                required=False,
                type=float,
            ),
            OpenApiParameter(
                name="tags",
                description="Filter by tags (comma-separated)",
                required=False,
                type=str,
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Get product details by slug",
        description="Returns detailed information about a specific product using its slug.",
    ),
    create=extend_schema(summary="Create a new product"),
    update=extend_schema(summary="Update a product"),
    partial_update=extend_schema(summary="Partial update a product"),
    destroy=extend_schema(summary="Delete a product"),
)
class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD operations.

    Features:
    - Multi-language support via Accept-Language header
    - Slug-based lookup for detail views
    - Comprehensive filtering (platform, type, brand, category, rating, tags, etc.)
    - Search across translated fields
    - Ordering by multiple fields
    - Caching for list views
    - Bulk operations
    - Statistics endpoint
    """

    queryset = (
        Product.objects.select_related("brand", "category", "sub_category")
        .prefetch_related(
            "translations",
            "category__translations",
            "sub_category__translations",
        )
        .all()
    )
    filterset_class = ProductFilter
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = [
        "translations__title",
        "translations__description",
        "brand__name",
        "product_asin",
        "tags",
    ]
    ordering_fields = [
        "created_at",
        "updated_at",
        "rating",
        "view_count",
        "click_count",
    ]
    ordering = ["-created_at"]
    pagination_class = StandardResultsPagination

    # Use slug for detail views instead of pk
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return ProductListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        """
        Filter queryset based on action and user permissions.
        Apply language filtering.
        """
        queryset = super().get_queryset()

        # Filter inactive products for non-staff users in list view
        if self.action == "list" and not getattr(self.request.user, "is_staff", False):
            queryset = queryset.filter(is_active=True)

        return queryset

    def get_object(self):
        """
        Get object by slug or pk.
        Supports both slug and pk lookups.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Get the lookup value
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs.get(lookup_url_kwarg)

        # Try slug first, then pk
        filter_kwargs = {self.lookup_field: lookup_value}

        try:
            obj = queryset.get(**filter_kwargs)
        except Product.DoesNotExist:
            # If slug lookup fails, try pk lookup
            if lookup_value.isdigit():
                try:
                    obj = queryset.get(pk=int(lookup_value))
                except Product.DoesNotExist:
                    from django.http import Http404

                    raise Http404("Product not found")
            else:
                from django.http import Http404

                raise Http404("Product not found")

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    @method_decorator(cache_page(60 * 2))  # Cache for 2 minutes
    @method_decorator(vary_on_headers("Accept-Language"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a product and optionally increment view count.
        """
        instance = self.get_object()

        # Increment view count if 'track' query param is present
        if request.query_params.get("track", "").lower() == "true":
            instance.increment_view()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="Get featured products",
        description="Returns a list of featured products.",
    )
    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Get featured products."""
        queryset = self.get_queryset().filter(is_featured=True, is_active=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProductListSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = ProductListSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Track affiliate link click",
        description="Increments the click count for a product and returns the affiliate link.",
    )
    @action(detail=True, methods=["post"], url_path="track-click")
    def track_click(self, request, slug=None):
        """Track click and return affiliate link."""
        product = self.get_object()
        product.increment_click()
        return Response(
            {
                "affiliate_link": product.af_link,
                "product_asin": product.product_asin,
                "slug": product.slug,
            }
        )

    @extend_schema(
        summary="Bulk product operations",
        description="Perform bulk operations on multiple products.",
        request=BulkProductSerializer,
    )
    @action(detail=False, methods=["post"], url_path="bulk-action")
    def bulk_action(self, request):
        """Perform bulk actions on products."""
        serializer = BulkProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product_ids = serializer.validated_data["product_ids"]
        action_type = serializer.validated_data["action"]

        products = Product.objects.filter(id__in=product_ids)
        count = products.count()

        if action_type == "activate":
            products.update(is_active=True)
            message = f"Activated {count} products"
        elif action_type == "deactivate":
            products.update(is_active=False)
            message = f"Deactivated {count} products"
        elif action_type == "feature":
            products.update(is_featured=True)
            message = f"Featured {count} products"
        elif action_type == "unfeature":
            products.update(is_featured=False)
            message = f"Unfeatured {count} products"
        elif action_type == "delete":
            products.delete()
            message = f"Deleted {count} products"
        else:
            return Response(
                {"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({"message": message, "count": count})

    @extend_schema(
        summary="Get product statistics",
        description="Returns aggregate statistics about products.",
        responses={200: ProductStatsSerializer},
    )
    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get product statistics."""
        queryset = Product.objects.all()

        stats = {
            "total_products": queryset.count(),
            "active_products": queryset.filter(is_active=True).count(),
            "featured_products": queryset.filter(is_featured=True).count(),
            "products_by_platform": dict(
                queryset.values("platform")
                .annotate(count=Count("id"))
                .values_list("platform", "count")
            ),
            "products_by_type": dict(
                queryset.values("product_type")
                .annotate(count=Count("id"))
                .values_list("product_type", "count")
            ),
            "avg_rating": queryset.filter(rating__isnull=False).aggregate(
                avg=Avg("rating")
            )["avg"],
            "total_views": queryset.aggregate(total=Sum("view_count"))["total"] or 0,
            "total_clicks": queryset.aggregate(total=Sum("click_count"))["total"] or 0,
        }

        serializer = ProductStatsSerializer(stats)
        return Response(serializer.data)

    @extend_schema(
        summary="Get available platforms",
        description="Returns list of available platform choices.",
    )
    @action(detail=False, methods=["get"])
    def platforms(self, request):
        """Get list of available platforms."""
        return Response(
            [
                {"value": choice[0], "label": choice[1]}
                for choice in Product.Platform.choices
            ]
        )

    @extend_schema(
        summary="Get available product types",
        description="Returns list of available product type choices.",
    )
    @action(detail=False, methods=["get"], url_path="product-types")
    def product_types(self, request):
        """Get list of available product types."""
        return Response(
            [
                {"value": choice[0], "label": choice[1]}
                for choice in Product.ProductType.choices
            ]
        )

    @extend_schema(
        summary="Get product by ASIN",
        description="Retrieve a product by its ASIN/product ID.",
    )
    @action(detail=False, methods=["get"], url_path="by-asin/(?P<asin>[^/.]+)")
    def by_asin(self, request, asin=None):
        """Get product by ASIN."""
        try:
            product = self.get_queryset().get(product_asin=asin)
            serializer = ProductDetailSerializer(product, context={"request": request})
            return Response(serializer.data)
        except Product.DoesNotExist:
            return Response(
                {"error": f"Product with ASIN {asin} not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @extend_schema(
        summary="Get related products",
        description="Returns products related to the specified product (same category/brand).",
    )
    @action(detail=True, methods=["get"])
    def related(self, request, slug=None):
        """Get related products based on category and brand."""
        product = self.get_object()

        # Get products in same category or brand, excluding current product
        related = (
            Product.objects.filter(is_active=True)
            .exclude(pk=product.pk)
            .filter(Q(category=product.category) | Q(brand=product.brand))
            .distinct()
            .prefetch_related("translations")[:10]
        )

        serializer = ProductListSerializer(
            related, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        summary="Regenerate product slug",
        description="Regenerates the slug from the current title.",
    )
    @action(detail=True, methods=["post"], url_path="regenerate-slug")
    def regenerate_slug(self, request, slug=None):
        """Regenerate slug from title."""
        product = self.get_object()
        old_slug = product.slug
        new_slug = product.generate_slug()
        product.save(update_fields=["slug"])

        return Response(
            {
                "old_slug": old_slug,
                "new_slug": new_slug,
                "product_asin": product.product_asin,
            }
        )
