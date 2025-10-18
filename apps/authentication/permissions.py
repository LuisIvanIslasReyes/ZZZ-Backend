"""
Custom permissions for role-based access control
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission check for Admin role
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsSupervisor(permissions.BasePermission):
    """
    Permission check for Supervisor role (and Admin)
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            (request.user.is_supervisor or request.user.is_admin)
        )


class IsEmployee(permissions.BasePermission):
    """
    Permission check for Employee role (any authenticated user)
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_employee


class IsOwnerOrSupervisor(permissions.BasePermission):
    """
    Object-level permission to only allow owners or their supervisors to access
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.is_admin:
            return True
        
        # Owner can access their own data
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Supervisor can access their supervised employees
        if request.user.is_supervisor:
            if hasattr(obj, 'user'):
                employee = getattr(obj.user, 'employee_profile', None)
                if employee and employee.supervisor == request.user:
                    return True
        
        return False
