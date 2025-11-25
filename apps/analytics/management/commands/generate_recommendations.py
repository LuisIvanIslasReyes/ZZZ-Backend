"""
Comando Django para generar recomendaciones automáticas.
Uso: python manage.py generate_recommendations [--supervisor-id ID] [--all]
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.analytics.recommendation_service import RecommendationService

User = get_user_model()


class Command(BaseCommand):
    help = 'Genera recomendaciones automáticas de optimización de rutinas'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--supervisor-id',
            type=int,
            help='ID del supervisor para el cual generar recomendaciones'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generar recomendaciones para todos los supervisores'
        )
    
    def handle(self, *args, **options):
        supervisor_id = options.get('supervisor_id')
        generate_all = options.get('all')
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('GENERACIÓN DE RECOMENDACIONES AUTOMÁTICAS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        
        # Determinar supervisores a procesar
        if supervisor_id:
            try:
                supervisor = User.objects.get(id=supervisor_id, role='supervisor')
                self.stdout.write(f"📊 Generando recomendaciones para: {supervisor.get_full_name()}")
                service = RecommendationService(supervisor=supervisor)
            except User.DoesNotExist:
                raise CommandError(f"Supervisor con ID {supervisor_id} no encontrado")
        elif generate_all:
            self.stdout.write("📊 Generando recomendaciones para todos los supervisores")
            service = RecommendationService()
        else:
            raise CommandError(
                'Debe especificar --supervisor-id ID o --all\n'
                'Ejemplo: python manage.py generate_recommendations --all'
            )
        
        # Generar recomendaciones
        try:
            result = service.generate_all_recommendations()
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✅ GENERACIÓN COMPLETADA'))
            self.stdout.write(self.style.SUCCESS('-' * 80))
            self.stdout.write(f"📈 Total de recomendaciones generadas: {result['total']}")
            self.stdout.write(f"👥 Supervisores analizados: {result['supervisors_analyzed']}")
            self.stdout.write('')
            self.stdout.write('📊 Recomendaciones por tipo:')
            for rec_type, count in result['by_type'].items():
                self.stdout.write(f"   - {rec_type}: {count}")
            self.stdout.write('')
            
            # Mostrar resumen
            if supervisor_id:
                summary = service.get_recommendation_summary(supervisor=supervisor)
            else:
                summary = service.get_recommendation_summary()
            
            self.stdout.write('📋 Estado de recomendaciones:')
            self.stdout.write(f"   - Total: {summary['total']}")
            self.stdout.write(f"   - Pendientes: {summary['pending']}")
            self.stdout.write(f"   - Aplicadas: {summary['applied']}")
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('=' * 80))
            
        except Exception as e:
            raise CommandError(f'Error al generar recomendaciones: {str(e)}')
