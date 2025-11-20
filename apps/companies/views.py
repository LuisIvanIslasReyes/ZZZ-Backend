from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Company
from .serializers import (
    CompanySerializer,
    CompanyDetailSerializer,
    CompanyStatsSerializer
)
from apps.users.permissions import IsAdmin


class CompanyViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de empresas (solo Admin).
    
    Endpoints:
    - GET /api/admin/companies/ - Listar empresas
    - POST /api/admin/companies/ - Crear empresa
    - GET /api/admin/companies/{id}/ - Detalle de empresa
    - PUT/PATCH /api/admin/companies/{id}/ - Actualizar empresa
    - DELETE /api/admin/companies/{id}/ - Eliminar empresa
    - GET /api/admin/companies/{id}/stats/ - Estadísticas de empresa
    """
    permission_classes = [IsAuthenticated, IsAdmin]
    queryset = Company.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CompanyDetailSerializer
        elif self.action == 'stats':
            return CompanyStatsSerializer
        return CompanySerializer
    
    def list(self, request, *args, **kwargs):
        """Listar todas las empresas con filtros opcionales"""
        queryset = self.get_queryset()
        
        # Filtro por estado activo
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Ordenamiento
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Crear una nueva empresa"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Actualizar empresa completa"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Eliminar empresa (soft delete recomendado)"""
        instance = self.get_object()
        
        # Verificar si tiene usuarios asociados
        if instance.users.exists():
            return Response(
                {
                    'error': 'No se puede eliminar una empresa con usuarios asociados. '
                             'Desactívela en su lugar.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Obtener estadísticas detalladas de una empresa
        GET /api/admin/companies/{id}/stats/
        """
        company = self.get_object()
        serializer = CompanyStatsSerializer(company)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        Activar/desactivar empresa
        POST /api/admin/companies/{id}/toggle_active/
        """
        company = self.get_object()
        company.is_active = not company.is_active
        company.save()
        
        serializer = self.get_serializer(company)
        return Response(serializer.data)
