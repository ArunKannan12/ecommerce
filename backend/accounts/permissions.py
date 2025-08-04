# users/permissions.py

from rest_framework.permissions import BasePermission

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'customer'


class IsPromoter(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'promoter'


class IsInvestor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'investor'


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.role == 'admin' or request.user.is_superuser
        )
class IsAdminOrCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.role == 'admin' or request.user.role == 'customer'
        )
    
class IsAdminOrPromoter(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.role in ['promoter', 'admin']
        )

class IsWarehouseStaffOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or getattr(request.user,'role','') in ['admin','warehouse_staff']
        )
class IsInvestorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or getattr(request.user,'role','') in ['admin','investor']
        )
