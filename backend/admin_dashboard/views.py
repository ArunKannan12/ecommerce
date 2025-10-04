from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import status
from django.db import transaction
from django.db.models.functions import Concat
from django_filters.rest_framework import DjangoFilterBackend
from .filters import WarehouseTimelineFilter
from rest_framework import generics, permissions, filters
from accounts.permissions import IsAdmin,IsWarehouseStaffOrAdmin
from .serializers import (
                        AdminDashboardStatsSerializer, 
                        ProductAdminSerializer,
                        ProductVariantAdminSerializer,
                        CustomerSerializer,
                        AdminOrderSerializer,
                        WarehouseLogSerializer,
                        WarehouseTimeLineSerializer,
                        DeliveryManStatsSerializer,
                        DeliveryTrackingSerializer
                        )
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_datetime
from delivery.serializers import DeliveryManRequestSerializer,DeliveryManSerializer
from delivery.models import DeliveryMan,DeliveryManRequest
from rest_framework.exceptions import NotFound
from django.db import transaction
from django.db.models import Max,Q,F,Value,CharField
from products.models import Product
import json
from rest_framework.parsers import MultiPartParser,FormParser,JSONParser
from rest_framework.exceptions import ValidationError
from products.models import ProductVariant,Banner
from products.serializers import BannerSerializer
from rest_framework.generics import ListAPIView,RetrieveAPIView,RetrieveUpdateAPIView
from django.contrib.auth import get_user_model
from orders.returnReplacementSerializer import ReturnRequestSerializer,ReplacementRequestSerializer
from rest_framework.filters import OrderingFilter,SearchFilter
from django.utils.dateparse import parse_date
from orders.models import Order,ReturnRequest,ReplacementRequest,OrderItem
from .helpers import str_to_bool
from .pagination import FlexiblePageSizePagination,TimelinePagination
from .models import WarehouseLog
User=get_user_model()

class AdminDashboardStatsAPIView(APIView):
    """
    Returns admin dashboard stats (e.g., product count, orders, revenue).
    Accessible only to authenticated admins.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        serializer = AdminDashboardStatsSerializer({})
        return Response(serializer.data)


class ProductAdminCreateAPIView(CreateAPIView):
    serializer_class = ProductAdminSerializer
    permission_classes = [IsAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Product.objects.all()

    def get_serializer_context(self):
        return {"request": self.request}

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        data = request.data.copy()

        # Parse variants JSON string
        if "variants" in data and isinstance(data["variants"], str):
            try:
                data["variants"] = json.loads(data["variants"])
                print("✅ Parsed variants:", data["variants"])
            except json.JSONDecodeError as e:
                print("❌ JSON decode error:", str(e))
                return Response({"variants": ["Invalid JSON format"]}, status=400)

        if not data.get("variants"):
            print("⚠️ No variants found after parsing")
            return Response({"variants": ["This field is required."]}, status=400)

        # Bind images to variants
        for i, variant in enumerate(data["variants"]):
            images = []
            for key, file in request.FILES.items():
                if key.startswith(f"variant_{i}_image_"):
                    print(f"🖼️ Binding image {key} to variant {i}")
                    images.append({"image": file})
            variant["images"] = images

        # Construct clean product payload
        product_data = {
            "name": data.get("name"),
            "description": data.get("description"),
            "is_available": data.get("is_available"),
            "featured": data.get("featured"),
            "category_id": data.get("category_id"),
            "image": data.get("image"),
            "variants": data.get("variants")
        }

        serializer = self.get_serializer(data=product_data)
        if not serializer.is_valid():
            print("❌ Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=400)

        product = serializer.save()
        print("🎉 Product created:", product.id)
        return Response(self.get_serializer(product).data, status=201)
    
class ProductAdminDetailAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductAdminSerializer
    permission_classes = [IsAdmin]
    lookup_field = "id"
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return Product.objects.all()

    def get_serializer_context(self):
        return {"request": self.request}

    def _parse_variants(self, data, files):
        """
        Parse 'variants' JSON string, bind uploaded images, and prepare
        variant payload for the serializer.
        Handles new uploads and tracks existing images to keep/remove.
        """
        variants = data.get("variants")
        if variants and isinstance(variants, str):
            try:
                variants = json.loads(variants)
                print("✅ Parsed variants:", variants)
            except json.JSONDecodeError:
                raise ValidationError({"variants": ["Invalid JSON format"]})
        elif not variants:
            variants = []

        for i, variant in enumerate(variants):
            # Gather newly uploaded images
            new_images = []
            for key, file in files.items():
                if key.startswith(f"variant_{i}_image_"):
                    print(f"🖼️ Binding uploaded image {key} to variant {i}")
                    new_images.append({"image": file})

            # Existing images the user wants to keep
            existing_images = []
            for img in variant.get("existing_images", []):
                if isinstance(img, dict) and img.get("id"):
                    existing_images.append({"id": img["id"]})

            # Images user wants to remove
            remove_images = []
            for img in variant.get("remove_images", []):
                if isinstance(img, int):
                    remove_images.append(img)

            # Store in variant for serializer
            variant["images"] = existing_images + new_images
            variant["remove_images"] = remove_images
            variant.pop("existing_images", None)

        # PUT must have at least one variant
        if self.request.method == "PUT" and not variants:
            raise ValidationError({"variants": ["At least one variant is required."]})

        data["variants"] = variants
        return data


    def _handle_main_image_removal(self, request, instance):
        """
        Optional improvement: handle main product image removal via 'remove_image' flag.
        """
        if request.data.get("remove_image"):
            if instance.image:
                instance.image.delete(save=False)
            instance.image = None
            instance.image_url = None

    @transaction.atomic
    def put(self, request, *args, **kwargs):
        data = request.data.copy()
        print("🔹 PUT payload before parsing:", data)
        data = self._parse_variants(data, request.FILES)

        instance = self.get_object()
        self._handle_main_image_removal(request, instance)

        serializer = self.get_serializer(instance, data=data)
        if not serializer.is_valid():
            print("❌ Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=400)

        product = serializer.save()
        print("🎉 Product updated (PUT):", product.id)
        return Response(self.get_serializer(product).data)

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        data = request.data.copy()
        print("🔹 PATCH payload before parsing:", data)
        data = self._parse_variants(data, request.FILES)

        instance = self.get_object()
        self._handle_main_image_removal(request, instance)

        # Update product fields
        serializer = self.get_serializer(instance, data=data, partial=True)
        if not serializer.is_valid():
            print("❌ Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=400)

        product = serializer.save()
        print("🎉 Product updated (PATCH):", product.id)

        # 🔁 Handle variants manually
        for i, variant_data in enumerate(data.get("variants", [])):
            variant_id = variant_data.get("id")
            if variant_id:
                try:
                    variant_instance = ProductVariant.objects.get(id=variant_id)
                    print(f"🔄 Updating variant {variant_id}")
                    variant_serializer = ProductVariantAdminSerializer(
                        instance=variant_instance,
                        data=variant_data,
                        context={"product": product},
                        partial=True
                    )
                except ProductVariant.DoesNotExist:
                    print(f"⚠️ Variant {variant_id} not found")
                    continue
            else:
                print(f"➕ Creating new variant: {variant_data.get('variant_name')}")
                variant_serializer = ProductVariantAdminSerializer(
                    data=variant_data,
                    context={"product": product}
                )

            if variant_serializer.is_valid():
                variant_serializer.save()
            else:
                print(f"❌ Variant {i} error:", variant_serializer.errors)

        return Response(self.get_serializer(product).data)

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        print(f"🗑️ Deleting product {product.id}")
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductBulkActionAPIView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        ids = request.data.get("ids", [])
        action = request.data.get("action")
        value = request.data.get("value")  # boolean for set_featured/set_availability

        if not ids or not isinstance(ids, list):
            return Response({"error": "IDs must be a list of product IDs"}, status=400)

        products = Product.objects.filter(id__in=ids)
        if not products.exists():
            return Response({"error": "No products found for given IDs"}, status=404)

        if action == "delete":
            count = products.count()
            products.delete()
            return Response({"deleted": count}, status=200)

        elif action == "set_featured":
            if value is None:
                return Response({"error": "Value is required for set_featured"}, status=400)
            products.update(featured=value)
            return Response({"updated": products.count(), "action": "set_featured"}, status=200)

        elif action == "set_availability":
            if value is None:
                return Response({"error": "Value is required for set_availability"}, status=400)
            products.update(is_available=value)
            return Response({"updated": products.count(), "action": "set_availability"}, status=200)

        return Response({"error": "Invalid action"}, status=400)


class CustomerListAPIView(ListAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [IsAdmin]
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = [
        "created_at", "first_name", "last_name", "email", "phone_number", "block_count", "is_verified"
    ]
    ordering = ["-created_at"]
    search_fields = ["first_name", "last_name", "email", "phone_number"]

    def get_queryset(self):
        queryset = User.objects.filter(role='customer')
        params = self.request.query_params

        # 🔍 Search filter
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone_number__icontains=search)
            )

        # 📌 Status filter
        status = params.get('status')
        if status == 'active':
            queryset = queryset.filter(is_permanently_banned=False, blocked_until__isnull=True)
        elif status == 'blocked':
            queryset = queryset.filter(blocked_until__gt=timezone.now())
        elif status == 'banned':
            queryset = queryset.filter(is_permanently_banned=True)

        # ✅ Verification filter
        verified = params.get('verified')
        if verified == 'true':
            queryset = queryset.filter(is_verified=True)
        elif verified == 'false':
            queryset = queryset.filter(is_verified=False)

        # 🔐 Auth provider filter
        auth_provider = params.get('auth_provider')
        if auth_provider:
            queryset = queryset.filter(auth_provider=auth_provider)

        # 🏙️ Location filters
        city = params.get('city')
        state = params.get('state')
        if city:
            queryset = queryset.filter(city__icontains=city)
        if state:
            queryset = queryset.filter(state__icontains=state)

        # 📅 Date range filter
        created_after = params.get('created_after')
        created_before = params.get('created_before')
        if created_after:
            queryset = queryset.filter(created_at__gte=created_after)
        if created_before:
            queryset = queryset.filter(created_at__lte=created_before)

        # 🚫 Block count threshold
        min_block_count = params.get('min_block_count')
        if min_block_count:
            queryset = queryset.filter(block_count__gte=min_block_count)

        # 🔃 Flexible sorting
        sort_by = params.getlist('sort_by') or ['-created_at']
        return queryset.order_by(*sort_by)

class CustomerDetailAPIView(RetrieveAPIView):
    serializer_class=CustomerSerializer
    lookup_field='id'
    permission_classes=[IsAdmin]
    queryset=User.objects.filter(role='customer')
    
from django.utils import timezone

class CustomerBlockAPIView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        """
        Block/unblock a customer.
        JSON options:
        {
            "duration_minutes": 60,  # optional temporary block
            "permanent": true/false, # optional permanent ban
            "unblock": true           # optional to remove any block
        }

        Logic:
        - If "unblock" is True → clears temporary & permanent block.
        - If "permanent" is True → sets permanent ban, clears temporary block.
        - If "duration_minutes" is provided → sets temporary block for that duration.
        - If none provided → toggles permanent ban.
        """
        try:
            user = User.objects.get(pk=pk, role='customer')
        except User.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

        unblock = request.data.get("unblock", False)
        permanent = request.data.get("permanent", False)
        duration = request.data.get("duration_minutes")

        if unblock:
            # Remove any blocks
            user.blocked_until = None
            user.is_permanently_banned = False
        elif permanent:
            # Set permanent ban
            user.is_permanently_banned = True
            user.blocked_until = None
        elif duration is not None:
            # Temporary block for X minutes
            try:
                minutes = int(duration)
                user.blocked_until = timezone.now() + timezone.timedelta(minutes=minutes)
                user.is_permanently_banned = False
                user.block_count += 1
            except ValueError:
                return Response({"error": "duration_minutes must be an integer"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Toggle permanent ban if nothing else provided
            user.is_permanently_banned = not user.is_permanently_banned
            if user.is_permanently_banned:
                user.blocked_until = None

        user.save()

        return Response({
            "id": user.id,
            "email": user.email,
            "blocked_until": user.blocked_until,
            "is_permanently_banned": user.is_permanently_banned
        }, status=status.HTTP_200_OK)

class AdminOrderListAPIView(ListAPIView):
    serializer_class = AdminOrderSerializer
    permission_classes = [IsAdmin]
    pagination_class = FlexiblePageSizePagination
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = [
        'order_number',"created_at", "updated_at", "delivered_at", "total",
        "user__first_name", "user__last_name",
        "status", "is_paid", "is_refunded", "refund_amount"
    ]
    ordering = ["-created_at"]
    search_fields = ["user__first_name", "user__last_name", "user__email", "tracking_number"]

    def get_queryset(self):
        queryset = Order.objects.all()

        # Filter by status
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filter by payment method
        payment_method = self.request.query_params.get("payment_method")
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        # Filter by boolean fields
        is_paid = self.request.query_params.get("is_paid")
        if is_paid is not None:
            try:
                queryset = queryset.filter(is_paid=str_to_bool(is_paid))
            except ValueError:
                raise ValidationError("Invalid is_paid value. Use true/false.")

        is_refunded = self.request.query_params.get("is_refunded")
        if is_refunded is not None:
            try:
                queryset = queryset.filter(is_refunded=str_to_bool(is_refunded))
            except ValueError:
                raise ValidationError("Invalid is_refunded value. Use true/false.")

        # Filter by date range
        start_date = self.request.query_params.get("start")
        end_date = self.request.query_params.get("end")
        if start_date:
            start = parse_date(start_date)
            if start:
                queryset = queryset.filter(created_at__date__gte=start)
        if end_date:
            end = parse_date(end_date)
            if end:
                queryset = queryset.filter(created_at__date__lte=end)

        # Filter by promoter
        promoter_id = self.request.query_params.get("promoter")
        if promoter_id:
            queryset = queryset.filter(promoter_id=promoter_id)

        return queryset

class AdminOrderDetailAPIView(RetrieveAPIView):
    serializer_class=AdminOrderSerializer
    permission_classes=[IsAdmin]
    lookup_field='order_number'
    queryset=Order.objects.all()
    

class AdminReturnRequestListAPIView(ListAPIView):
    serializer_class = ReturnRequestSerializer
    permission_classes = [IsAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    pagination_class = FlexiblePageSizePagination
    ordering_fields = ["created_at", "updated_at", "refund_amount", "status"]
    ordering = ["-created_at"]
    search_fields = ['id',
        "user__email",
        "order_item__product_variant__product__name",
        "order_item__product_variant__variant_name",
        "order__shipping_address__full_name",
    ]


    def get_queryset(self):
        params = self.request.query_params

        queryset = (
            ReturnRequest.objects
            .select_related(
                "user",
                "order",
                'order__shipping_address',
                "order_item__product_variant__product",
                "order_item__product_variant",
                "pickup_verified_by"
            )
            .prefetch_related("order_item__product_variant__images")
            .order_by("-created_at")
        )

        # Filter by status (supports comma-separated)
        status_param = params.get("status")
        if status_param:
            status_list = [s.strip() for s in status_param.split(",") if s.strip()]
            queryset = queryset.filter(status__in=status_list)

        # Filter by order ID
        order_id = params.get("order_id")
        if order_id:
            queryset = queryset.filter(order__id=order_id)

        # Filter by user email
        user_email = params.get("user_email")
        if user_email:
            queryset = queryset.filter(user__email__icontains=user_email)

        # Filter by product name
        product_name = params.get("product_name")
        if product_name:
            queryset = queryset.filter(
                order_item__product_variant__product__name__icontains=product_name
            )

        # Filter by variant name
        variant_name = params.get("variant_name")
        if variant_name:
            queryset = queryset.filter(
                order_item__product_variant__variant_name__icontains=variant_name
            )

        # Filter by created date range
        created_from = params.get("created_from")
        created_to = params.get("created_to")
        if created_from:
            created_from_date = parse_date(created_from)
            if created_from_date:
                queryset = queryset.filter(created_at__date__gte=created_from_date)
        if created_to:
            created_to_date = parse_date(created_to)
            if created_to_date:
                queryset = queryset.filter(created_at__date__lte=created_to_date)

        # Filter by refund amount range
        refund_min = params.get("refund_min")
        refund_max = params.get("refund_max")
        try:
            if refund_min:
                queryset = queryset.filter(refund_amount__gte=float(refund_min))
            if refund_max:
                queryset = queryset.filter(refund_amount__lte=float(refund_max))
        except ValueError:
            pass  # silently ignore invalid numbers

        return queryset

        
class AdminReturnRequestdetailAPIView(RetrieveAPIView):
    serializer_class=ReturnRequestSerializer
    permission_classes=[IsAdmin]
    queryset=ReturnRequest.objects.all()

class AdminReplacementRequestListAPIView(ListAPIView):
    serializer_class = ReplacementRequestSerializer
    permission_classes = [IsAdmin]
    pagination_class = FlexiblePageSizePagination
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = ['id',"created_at", "updated_at", "delivered_at", "status"]
    ordering = ["-created_at"]
    search_fields = [
        "user__first_name", "user__last_name", "user__email",
        "order_item__product_variant__product__name"
    ]

    def get_queryset(self):
        queryset = ReplacementRequest.objects.all().order_by("-created_at")

        # --- Status filter ---
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # --- Order ID filter ---
        order_id = self.request.query_params.get("order_id")
        if order_id:
            queryset = queryset.filter(order__id=order_id)

        # --- Product name filter ---
        product_name = self.request.query_params.get("product_name")
        if product_name:
            queryset = queryset.filter(order_item__product_variant__product__name__icontains=product_name)

        # --- Date range filter ---
        start_date = self.request.query_params.get("start")
        end_date = self.request.query_params.get("end")
        if start_date:
            start = parse_date(start_date)
            if start:
                queryset = queryset.filter(created_at__date__gte=start)
        if end_date:
            end = parse_date(end_date)
            if end:
                queryset = queryset.filter(created_at__date__lte=end)

        # --- Min/Max replacement days remaining filter ---
        min_days = self.request.query_params.get("min_days_remaining")
        max_days = self.request.query_params.get("max_days_remaining")
        if min_days or max_days:
            ids = []
            for r in queryset:
                remaining = r.get_replacement_days_remaining()
                if min_days and remaining < int(min_days):
                    continue
                if max_days and remaining > int(max_days):
                    continue
                ids.append(r.id)
            queryset = queryset.filter(id__in=ids)


        return queryset


class AdminReplacementRequestdetailAPIView(RetrieveAPIView):
    serializer_class=ReplacementRequestSerializer
    permission_classes=[IsAdmin]
    queryset=ReplacementRequest.objects.all()

class WarehouseLogListAPIView(ListAPIView):
    serializer_class=WarehouseLogSerializer
    permission_classes=[IsWarehouseStaffOrAdmin]
    filter_backends=[OrderingFilter,SearchFilter]
    pagination_class = FlexiblePageSizePagination
    # Which fields can be used for ordering
    ordering_fields = ['timestamp', 'action', 'order__order_number', 'order_item__id']
    ordering = ['-timestamp']  # default ordering

    # Which fields can be used for search
    search_fields = [
        'order__order_number',
        'order_item__product_variant__product__name',
        'order_item__product_variant__variant_name',
        'updated_by__first_name',
        'updated_by__last_name',
        'updated_by__email',
        'action'
    ]

    def get_queryset(self):
        queryset = WarehouseLog.objects.select_related(
            'order_item__product_variant__product',
            'order',
            'updated_by'
        ).all()
        

        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        order_number = self.request.query_params.get('order__order_number')
        if order_number:
            queryset = queryset.filter(order__order_number=order_number)

        updated_by_id = self.request.query_params.get('updated_by__id')
        if updated_by_id:
            queryset = queryset.filter(updated_by__id=updated_by_id)
        return queryset
    
class WarehouseLogDetailAPIView(RetrieveAPIView):
    serializer_class=WarehouseLogSerializer
    permission_classes=[IsWarehouseStaffOrAdmin]
    queryset=WarehouseLog.objects.select_related(
        'order_item__product_variant__product',
        'order',
        'updated_by'
    )
    lookup_field='id'

class WarehouseTimelineAPIView(ListAPIView):
    serializer_class = WarehouseTimeLineSerializer
    pagination_class = TimelinePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = WarehouseTimelineFilter

    def get_queryset(self):
        return WarehouseLog.objects.values('order__id', 'order__order_number').annotate(
            order_number=F('order__order_number'),
            picked_at=Max('timestamp', filter=Q(action='picked')),
            packed_at=Max('timestamp', filter=Q(action='packed')),
            shipped_at=Max('timestamp', filter=Q(action='shipped')),
            out_for_delivery_at=Max('timestamp', filter=Q(action='out_for_delivery')),
            delivered_at=Max('timestamp', filter=Q(action='delivered')),
        ).order_by('-picked_at')

class AdminDeliveryManRequestListAPIView(ListAPIView):
    permission_classes=[IsAdmin]
    serializer_class=DeliveryManRequestSerializer

    def get_queryset(self):
        queryset=DeliveryManRequest.objects.all().order_by('-applied_at')
        params=self.request.query_params
        status_filter=params.get('status')
        if status_filter:
            queryset=queryset.filter(status=status_filter.lower())
        user_id=params.get('user')
        if user_id:
            queryset=queryset.filter(user__id=user_id)
        phone=params.get('phone')
        if phone:
            queryset=queryset.filter(phone__icontains=phone.strip())
        start_date=params.get('start_date')
        end_date=params.get('end_date')
        if start_date:
            queryset=queryset.filter(applied_at__gte=parse_datetime(start_date))
        if end_date:
            queryset=queryset.filter(applied_at__lte=parse_datetime(end_date))

        return queryset
    
class AdminDeliveryManReuestDetailAPIView(RetrieveAPIView):
    permission_classes=[IsAdmin]
    serializer_class=DeliveryManRequestSerializer
    lookup_field='id'
    def get_queryset(self):
        return DeliveryManRequest.objects.all()

class AdminApproveDeliveryManRequestAPIView(APIView):
    permission_classes = [IsAdmin]

    @transaction.atomic
    def post(self, request, request_id):
        try:
            # Get the request without filtering status
            dm_request = DeliveryManRequest.objects.select_for_update().get(id=request_id)
        except DeliveryManRequest.DoesNotExist:
            raise NotFound("Deliveryman request not found.")

        if dm_request.status == 'approved':
            return Response({"error": "Request is already approved."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # If previously rejected, remove any old DeliveryMan profile and reset role
            if dm_request.status == 'rejected':
                deliveryman_profile = DeliveryMan.objects.filter(user=dm_request.user).first()
                if deliveryman_profile:
                    deliveryman_profile.delete()
                dm_request.user.role = 'customer'
                dm_request.user.save()

            # Create DeliveryMan profile
            DeliveryMan.objects.create(
                user=dm_request.user,
                phone=dm_request.phone or '',
                address=dm_request.address or '',
                vehicle_number=(dm_request.vehicle_number or '').upper()
            )

            # Update user role
            dm_request.user.role = 'deliveryman'
            dm_request.user.save()

            # Mark request as approved
            dm_request.status = 'approved'
            dm_request.reviewed_at = timezone.now()
            dm_request.save()

        except Exception as e:
            return Response({'error': f'Could not approve request: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Deliveryman request approved and profile created.'}, status=status.HTTP_200_OK)


class AdminRejectDeliveryManRequestAPIView(APIView):
    permission_classes = [IsAdmin]

    @transaction.atomic
    def post(self, request, request_id):
        try:
            dm_request = DeliveryManRequest.objects.get(id=request_id)
        except DeliveryManRequest.DoesNotExist:
            raise NotFound("DeliveryMan request not found.")

        # If already approved, rollback DeliveryMan profile + role
        if dm_request.status == "approved":
            deliveryman_profile = DeliveryMan.objects.filter(user=dm_request.user).first()
            if deliveryman_profile:
                deliveryman_profile.delete()

            # revert role back to customer (or whatever default)
            dm_request.user.role = "customer"
            dm_request.user.save()

        # Mark as rejected
        dm_request.status = "rejected"
        dm_request.reviewed_at = timezone.now()
        dm_request.save()

        return Response(
            {"message": "DeliveryMan request rejected."},
            status=status.HTTP_200_OK
        )

class AdminDeliveryManListAPIView(ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = DeliveryManSerializer
    pagination_class = FlexiblePageSizePagination  # optional, replace with your paginator

    def get_queryset(self):
        queryset = DeliveryMan.objects.select_related('user').all()
        params = self.request.query_params

        # Annotate full_name for filtering
        queryset = queryset.annotate(
            full_name=Concat('user__first_name', Value(' '), 'user__last_name', output_field=CharField())
        )

        # Filter by active / inactive
        status = params.get('status')
        if status:
            queryset = queryset.filter(user__is_active=(status.lower() == 'active'))

        # Filter by name (first + last)
        search = params.get('search')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(phone__icontains=search) |
                Q(address__icontains=search)
            )
        ordering = params.get('ordering')  # optional ordering from query param
        if ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('-joined_at')
        return queryset

class AdminDeliveryManDetailAPIView(RetrieveUpdateAPIView):
    permission_classes=[IsAdmin]
    serializer_class=DeliveryManSerializer
    lookup_field='id'

    def get_queryset(self):
        return DeliveryMan.objects.select_related('user').all()
    
class AdminToggleDeliveryManActiveAPIView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, deliveryman_id):
        deliveryman = get_object_or_404(DeliveryMan, id=deliveryman_id)
        # Flip the is_active flag
        deliveryman.user.is_active = not deliveryman.user.is_active
        deliveryman.user.save()

        message = "DeliveryMan activated successfully" if deliveryman.user.is_active else "DeliveryMan deactivated successfully"

        # Return updated info
        return Response({
            "id": deliveryman.id,
            "full_name": deliveryman.user.get_full_name(),
            "is_active": deliveryman.user.is_active,
            "message": message
        }, status=status.HTTP_200_OK)
    
class AdminDeliveryTrackingAPIView(ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = DeliveryTrackingSerializer

    def get_queryset(self):
        # Only consider items in delivery pipeline
        queryset = OrderItem.objects.filter(
            Q(status__in=['picked', 'packed', 'shipped', 'out_for_delivery'])
        ).select_related('order', 'order__delivered_by', 'product_variant')

        # Filter by deliveryman (order-level field)
        deliveryman_id = self.request.query_params.get('deliveryman')
        if deliveryman_id:
            queryset = queryset.filter(order__delivered_by_id=deliveryman_id)

        # Filter by order number
        order_number = self.request.query_params.get('order')
        if order_number:
            queryset = queryset.filter(order__order_number__icontains=order_number)

        # Optional: filter by item status
        item_status = self.request.query_params.get('status')
        if item_status:
            queryset = queryset.filter(status=item_status.lower())

        return queryset

class AdminDeliveryTrackingDetailAPIView(RetrieveAPIView):
    permission_classes=[IsAdmin]
    serializer_class=DeliveryTrackingSerializer
    lookup_field='id'
    def get_queryset(self):
        # Include all delivery items in delivery pipeline
        return OrderItem.objects.filter(
            status__in=['picked', 'packed', 'shipped', 'out_for_delivery']
        ).select_related('order', 'order__delivered_by', 'product_variant')

class AdminDeliveryManStatsAPIView(RetrieveAPIView):
    permission_classes = [IsAdmin]
    serializer_class = DeliveryManStatsSerializer  # custom serializer
    lookup_field = 'id'

    def get_queryset(self):
        return DeliveryMan.objects.select_related('user').all()


# ADMIN: list banners with filters, search, and ordering
class AdminBannerListAPIView(generics.ListAPIView):
    serializer_class = BannerSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active"]              # ?is_active=true/false
    search_fields = ["title", "subtitle"]         # ?search=summer
    ordering_fields = ["order", "created_at"]     # ?ordering=order or ?ordering=-created_at

    def get_queryset(self):
        return Banner.objects.all().order_by("order")


# ADMIN: create banners
class BannerCreateAPIView(generics.CreateAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    permission_classes = [IsAdmin]
    parser_classes = (MultiPartParser, FormParser)


# ADMIN: retrieve, update, delete banners
class BannerUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    permission_classes = [IsAdmin]
    parser_classes = (MultiPartParser, FormParser)