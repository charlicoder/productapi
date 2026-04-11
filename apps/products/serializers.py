"""
Django REST Framework serializers for Affiliate Products.

Includes translation support via django-parler-rest.
"""

from rest_framework import serializers
from parler_rest.serializers import TranslatableModelSerializer, TranslatedFieldsField
from parler_rest.fields import TranslatedField

from .models import Brand, Category, SubCategory, Product


# =============================================================================
# BRAND SERIALIZERS
# =============================================================================


class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source="products.count", read_only=True)

    class Meta:
        model = Brand
        fields = "__all__"


class BrandNestedSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source="name")
    brand_url = serializers.URLField(source="url")
    brand_logo = serializers.URLField(source="logo")

    class Meta:
        model = Brand
        fields = ["brand_name", "brand_url", "brand_logo"]


# =============================================================================
# CATEGORY SERIALIZERS
# =============================================================================


class CategorySerializer(TranslatableModelSerializer):
    """Serializer for Category model with translations."""

    translations = TranslatedFieldsField(shared_model=Category)
    subcategories_count = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "translations",
            "slug",
            "icon",
            "is_active",
            "order",
            "subcategories_count",
            "product_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "subcategories_count",
            "product_count",
        ]

    def get_subcategories_count(self, obj):
        """Return count of active subcategories."""
        return obj.subcategories.filter(is_active=True).count()

    def get_product_count(self, obj):
        """Return count of active products in this category."""
        return obj.products.filter(is_active=True).count()


class CategoryNestedSerializer(serializers.ModelSerializer):
    """
    Nested serializer for Category in Product responses.

    Returns:
    {
        "name": "Electronics",
        "icon": "some-icon"
    }
    """

    name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["name", "icon"]

    def get_name(self, obj):
        return obj.safe_translation_getter("name", any_language=True)


class CategoryListSerializer(TranslatableModelSerializer):
    """Lightweight serializer for Category in list views."""

    name = TranslatedField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "icon"]


# =============================================================================
# SUBCATEGORY SERIALIZERS
# =============================================================================


class SubCategorySerializer(TranslatableModelSerializer):
    """Serializer for SubCategory model with translations."""

    translations = TranslatedFieldsField(shared_model=SubCategory)
    category_detail = CategoryListSerializer(source="category", read_only=True)
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = SubCategory
        fields = [
            "id",
            "translations",
            "slug",
            "category",
            "category_detail",
            "icon",
            "is_active",
            "order",
            "product_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "category_detail",
            "product_count",
        ]

    def get_product_count(self, obj):
        """Return count of active products in this subcategory."""
        return obj.products.filter(is_active=True).count()


class SubCategoryListSerializer(TranslatableModelSerializer):
    """Lightweight serializer for SubCategory in list views."""

    name = TranslatedField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = SubCategory
        fields = ["id", "name", "slug", "category_name"]

    def get_category_name(self, obj):
        """Get translated category name."""
        return (
            obj.category.safe_translation_getter("name", any_language=True)
            if obj.category
            else None
        )


class SubCategoryNestedSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = SubCategory
        fields = ["name", "slug", "icon"]

    def get_name(self, obj):
        return obj.safe_translation_getter("name", any_language=True)


# =============================================================================
# PRODUCT SERIALIZERS
# =============================================================================

# serializers.py


class ProductListSerializer(TranslatableModelSerializer):
    """
    List serializer for Product list views.

    Includes images, videos, affiliate link, and features as requested.
    """

    title = TranslatedField()
    description = TranslatedField()

    brand = BrandNestedSerializer(read_only=True)
    category = CategoryNestedSerializer(read_only=True)
    sub_category = SubCategoryNestedSerializer(read_only=True)

    featured_image = serializers.ReadOnlyField()
    current_price = serializers.ReadOnlyField()
    tags_list = serializers.ReadOnlyField()

    # JSON fields (returned as-is)
    features = serializers.JSONField(read_only=True)
    images = serializers.JSONField(read_only=True)
    videos = serializers.JSONField(read_only=True)
    meta = serializers.JSONField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "product_asin",
            "slug",
            "title",
            "description",
            "platform",
            "product_type",
            # requested
            "af_link",
            "features",
            "images",
            "videos",
            "meta",
            # existing
            "brand",
            "category",
            "sub_category",
            "featured_image",
            "current_price",
            "price_info",
            "rating",
            "tags_list",
            "is_featured",
            "created_at",
        ]

    def get_category_name(self, obj):
        if obj.category:
            return obj.category.safe_translation_getter("name", any_language=True)
        return None


class ProductDetailSerializer(TranslatableModelSerializer):
    """
    Full serializer for Product detail views.

    Returns complete product data with nested brand, category, subcategory.

    Response format for brand:
    {
        "brand_name": "BAGSMART",
        "brand_url": "https://www.bagsmart.com/"
    }

    JSON fields (price_info, features, images, videos) are returned as-is.
    """

    translations = TranslatedFieldsField(shared_model=Product)

    # Brand as nested object with brand_name and brand_url
    brand = BrandNestedSerializer(read_only=True)

    # Category and SubCategory
    category = serializers.SerializerMethodField()
    sub_category = serializers.SerializerMethodField()

    # Tags as list
    tags_list = serializers.ListField(
        child=serializers.CharField(), read_only=True, help_text="List of tags"
    )

    # Display values
    platform_display = serializers.CharField(
        source="get_platform_display", read_only=True
    )
    product_type_display = serializers.CharField(
        source="get_product_type_display", read_only=True
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "product_asin",
            "slug",
            "platform",
            "platform_display",
            "af_link",
            "translations",
            "price_info",
            "rating",
            "brand",
            "features",
            "shipping",
            "returns",
            "product_type",
            "product_type_display",
            "category",
            "sub_category",
            "tags",
            "tags_list",
            "videos",
            "images",
            "meta",
            "is_active",
            "is_featured",
            "view_count",
            "click_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "view_count",
            "click_count",
            "created_at",
            "updated_at",
            "brand",
            "category",
            "sub_category",
            "platform_display",
            "product_type_display",
            "tags_list",
        ]

    def get_category(self, obj):
        """Return category name."""
        if obj.category:
            return obj.category.safe_translation_getter("name", any_language=True)
        return None

    def get_sub_category(self, obj):
        """Return subcategory name."""
        if obj.sub_category:
            return obj.sub_category.safe_translation_getter("name", any_language=True)
        return None

    def to_representation(self, instance):
        """
        Customize the output representation.
        Ensures JSON fields are returned in the correct format.
        """
        data = super().to_representation(instance)

        # Get translated fields directly for convenience
        data["shipping"] = instance.safe_translation_getter(
            "shipping", any_language=True
        )
        data["returns"] = instance.safe_translation_getter("returns", any_language=True)

        # Ensure price_info has the correct structure
        if not data.get("price_info"):
            data["price_info"] = {
                "price": None,
                "regular_price": None,
                "cost_savings": None,
                "discount_percent": None,
                "savings_percent": None,
            }

        # Ensure features is a list of {key, value} objects
        if not data.get("features"):
            data["features"] = []

        # Ensure images is a list of {image, alt_text, is_featured, order} objects
        if not data.get("images"):
            data["images"] = []

        # Ensure videos is a list of {video, title, is_featured, order} objects
        if not data.get("videos"):
            data["videos"] = []

        return data


class ProductCreateUpdateSerializer(TranslatableModelSerializer):
    """
    Serializer for creating and updating products.

    Accepts:
    - translations: dict with language codes as keys
    - brand: brand ID (integer)
    - category: category ID (integer)
    - sub_category: subcategory ID (integer)
    - price_info: JSON object
    - features: list of {key, value} objects
    - images: list of {image, alt_text, is_featured, order} objects
    - videos: list of {video, title, is_featured, order} objects
    - tags_list: list of strings (optional, converted to comma-separated)
    """

    translations = TranslatedFieldsField(shared_model=Product)
    tags_list = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        write_only=True,
        help_text="List of tags (will be converted to comma-separated)",
    )

    # For write operations, accept IDs
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(), required=False, allow_null=True
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), required=False, allow_null=True
    )
    sub_category = serializers.PrimaryKeyRelatedField(
        queryset=SubCategory.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            "product_asin",
            "slug",
            "platform",
            "af_link",
            "translations",
            "price_info",
            "rating",
            "brand",
            "features",
            "images",
            "videos",
            "product_type",
            "category",
            "sub_category",
            "tags",
            "tags_list",
            "meta",
            "is_active",
            "is_featured",
        ]
        extra_kwargs = {
            "slug": {"required": False, "allow_blank": True},
        }

    def validate_price_info(self, value):
        """Validate price_info JSON structure."""
        if value:
            allowed_keys = {
                "price",
                "regular_price",
                "cost_savings",
                "discount_percent",
                "savings_percent",
            }
            for key in value.keys():
                if key not in allowed_keys:
                    raise serializers.ValidationError(
                        f"Invalid key '{key}' in price_info. Allowed keys: {allowed_keys}"
                    )
        return value

    def validate_features(self, value):
        """
        Validate features JSON structure.
        Expected format: [{"key": "...", "value": "..."}, ...]
        """
        if value:
            for idx, feature in enumerate(value):
                if not isinstance(feature, dict):
                    raise serializers.ValidationError(
                        f"Feature at index {idx} must be an object"
                    )
                if "key" not in feature or "value" not in feature:
                    raise serializers.ValidationError(
                        f"Feature at index {idx} must have 'key' and 'value' fields"
                    )
        return value

    def validate_images(self, value):
        """
        Validate images JSON structure.
        Expected format: [{"image": "...", "alt_text": "...", "is_featured": bool, "order": int}, ...]
        """
        if value:
            for idx, img in enumerate(value):
                if not isinstance(img, dict):
                    raise serializers.ValidationError(
                        f"Image at index {idx} must be an object"
                    )
                if "image" not in img:
                    raise serializers.ValidationError(
                        f"Image at index {idx} missing 'image' field"
                    )
                # Set defaults for optional fields
                img.setdefault("alt_text", "")
                img.setdefault("is_featured", False)
                img.setdefault("order", idx + 1)
        return value

    def validate_videos(self, value):
        """
        Validate videos JSON structure.
        Expected format: [{"video": "...", "title": "...", "is_featured": bool, "order": int}, ...]
        """
        if value:
            for idx, vid in enumerate(value):
                if not isinstance(vid, dict):
                    raise serializers.ValidationError(
                        f"Video at index {idx} must be an object"
                    )
                if "video" not in vid:
                    raise serializers.ValidationError(
                        f"Video at index {idx} missing 'video' field"
                    )
                # Set defaults for optional fields
                vid.setdefault("title", "")
                vid.setdefault("is_featured", False)
                vid.setdefault("order", idx + 1)
        return value

    def validate(self, data):
        """Cross-field validation."""
        # Ensure subcategory belongs to category if both provided
        sub_category = data.get("sub_category")
        category = data.get("category")

        if sub_category and category:
            if sub_category.category_id != category.id:
                raise serializers.ValidationError(
                    {
                        "sub_category": "Subcategory must belong to the selected category."
                    }
                )
        elif sub_category and not category:
            # Auto-set category from subcategory
            data["category"] = sub_category.category

        return data

    def create(self, validated_data):
        """Handle tags_list during creation."""
        tags_list = validated_data.pop("tags_list", None)
        instance = super().create(validated_data)
        if tags_list is not None:
            instance.tags_list = tags_list
            instance.save(update_fields=["tags"])
        return instance

    def update(self, instance, validated_data):
        """Handle tags_list during update."""
        tags_list = validated_data.pop("tags_list", None)
        instance = super().update(instance, validated_data)
        if tags_list is not None:
            instance.tags_list = tags_list
            instance.save(update_fields=["tags"])
        return instance

    def to_representation(self, instance):
        """Return the detail serializer format for response."""
        return ProductDetailSerializer(instance, context=self.context).data


class CategoryWithSubcategoriesSerializer(TranslatableModelSerializer):
    """Category serializer with nested subcategories."""

    translations = TranslatedFieldsField(shared_model=Category)
    subcategories = SubCategoryListSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "translations",
            "slug",
            "icon",
            "is_active",
            "order",
            "subcategories",
        ]


class BulkProductSerializer(serializers.Serializer):
    """Serializer for bulk product operations."""

    product_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100,
        help_text="List of product IDs",
    )
    action = serializers.ChoiceField(
        choices=["activate", "deactivate", "feature", "unfeature", "delete"],
        help_text="Action to perform on products",
    )


class ProductStatsSerializer(serializers.Serializer):
    """Serializer for product statistics."""

    total_products = serializers.IntegerField()
    active_products = serializers.IntegerField()
    featured_products = serializers.IntegerField()
    products_by_platform = serializers.DictField()
    products_by_type = serializers.DictField()
    avg_rating = serializers.DecimalField(
        max_digits=2, decimal_places=1, allow_null=True
    )
    total_views = serializers.IntegerField()
    total_clicks = serializers.IntegerField()
