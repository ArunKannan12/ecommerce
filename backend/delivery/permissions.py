from rest_framework.permissions import BasePermission
from .models import DeliveryMan
class IsDeliveryManOrAdmin(BasePermission):
    def has_permission(self, request, view):
        
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.role in ['admin','deliveryman']
        )

class IsDeliveryMan(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'deliveryman'