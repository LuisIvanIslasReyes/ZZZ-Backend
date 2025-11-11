from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a administradores.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin()


class IsSupervisor(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a supervisores.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_supervisor()


class IsEmployee(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a empleados.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_employee()


class IsAdminOrSupervisor(permissions.BasePermission):
    """
    Permiso personalizado para permitir a administradores y supervisores.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_admin() or request.user.is_supervisor())
        )


class IsOwnerOrSupervisor(permissions.BasePermission):
    """
    Permiso personalizado que permite:
    - Al dueño del objeto acceder a sus propios datos
    - Al supervisor acceder a los datos de sus empleados
    - A los admins acceder a todo
    """
    
    def has_object_permission(self, request, view, obj):
        # Admins tienen acceso total
        if request.user.is_admin():
            return True
        
        # El dueño tiene acceso a sus propios datos
        if obj == request.user:
            return True
        
        # Supervisores tienen acceso a datos de sus empleados
        if request.user.is_supervisor() and hasattr(obj, 'supervisor'):
            return obj.supervisor == request.user
        
        return False


class CanManageEmployees(permissions.BasePermission):
    """
    Permiso para gestionar empleados.
    Solo supervisores y admins pueden crear/editar empleados.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            # Lectura: todos los autenticados
            return request.user and request.user.is_authenticated
        
        # Escritura: solo supervisores y admins
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_supervisor() or request.user.is_admin())
        )
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            # Lectura permitida si es el dueño, su supervisor o admin
            if request.user.is_admin():
                return True
            if obj == request.user:
                return True
            if request.user.is_supervisor() and obj.supervisor == request.user:
                return True
            return False
        
        # Escritura: solo el supervisor del empleado o admin
        if request.user.is_admin():
            return True
        if request.user.is_supervisor() and obj.supervisor == request.user:
            return True
        
        return False


class CanManageSupervisors(permissions.BasePermission):
    """
    Permiso para gestionar supervisores.
    Solo administradores pueden crear/editar supervisores.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin()
