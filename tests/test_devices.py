"""
Tests for devices endpoints
"""
import pytest
from django.urls import reverse
from rest_framework import status
from tests.factories import DeviceFactory, UserFactory
from django.utils import timezone


@pytest.mark.django_db
class TestDeviceEndpoints:
    
    def test_create_device(self, authenticated_client, employee_user):
        """Test creating a device"""
        url = reverse('devices:device_list')
        data = {
            'device_type': 'WATCH',
            'hardware_id': 'TEST-DEVICE-001',
            'model_name': 'Test Watch',
            'firmware_version': '1.0.0'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['hardware_id'] == 'TEST-DEVICE-001'
    
    def test_list_devices(self, authenticated_client, employee_user):
        """Test listing devices"""
        # Create some devices
        DeviceFactory.create_batch(3, employee=employee_user)
        
        url = reverse('devices:device_list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
    
    def test_batch_sensor_data(self, authenticated_client, employee_user):
        """Test batch sensor data ingestion"""
        device = DeviceFactory(employee=employee_user)
        
        url = reverse('devices:sensor_data_batch')
        data = {
            'device_id': device.hardware_id,
            'firmware_version': '1.0.0',
            'samples': [
                {
                    'timestamp': timezone.now().isoformat(),
                    'hr': 75,
                    'spo2': 98.5,
                    'accel_x': 0.1,
                    'accel_y': 0.2,
                    'accel_z': 9.8,
                    'steps': 1500,
                    'battery': 85
                },
                {
                    'timestamp': timezone.now().isoformat(),
                    'hr': 78,
                    'spo2': 98.0,
                    'accel_x': 0.2,
                    'accel_y': 0.3,
                    'accel_z': 9.7,
                    'steps': 1505,
                    'battery': 85
                }
            ]
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['samples_count'] == 2


@pytest.mark.django_db
class TestStressEndpoints:
    
    def test_employee_stress_summary(self, authenticated_client, employee_user):
        """Test getting stress summary"""
        from tests.factories import StressAggregateFactory
        
        # Create some stress data
        StressAggregateFactory.create_batch(5, employee=employee_user)
        
        url = reverse('devices:employee_stress_summary', kwargs={'employee_id': employee_user.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'avg_stress' in response.data
        assert 'current_stress' in response.data
