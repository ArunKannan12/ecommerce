# users/permissions.py

from rest_framework.permissions import BasePermission,SAFE_METHODS

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated and
                 getattr(request.user, 'role', '') == 'customer')


class IsPromoter(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'role', '') == 'promoter'


class IsInvestor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'role', '') == 'investor'


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            getattr(request.user, 'role', '') == 'admin' or request.user.is_staff
        )
class IsAdminOrCustomer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or getattr(request.user, 'role', '') == 'admin' or getattr(request.user, 'role', '') == 'customer'
        )
    
class IsAdminOrPromoter(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.role in ['promoter', 'admin']
        )

class IsWarehouseStaffOrAdmin(BasePermission):
    def has_permission(self, request, view):
        user=request.user
        return user.is_authenticated and (
            user.is_staff or getattr(user,'role',None) in ['admin','warehouse']
        )
    
class IsWarehouseStaff(BasePermission):
    def has_permission(self, request, view):
        user=request.user
        return user.is_authenticated and getattr(user,'role',None) == 'warehouse'
     
class IsInvestorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or getattr(request.user,'role','') in ['admin','investor']
        )

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return IsAdmin().has_permission(request,view)