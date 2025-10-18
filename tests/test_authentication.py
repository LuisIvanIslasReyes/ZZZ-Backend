"""
Tests for authentication endpoints
"""
import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAuthenticationEndpoints:
    
    def test_register_user(self, api_client):
        """Test user registration"""
        url = reverse('authentication:register')
        data = {
            'email': 'newuser@test.com',
            'username': 'newuser',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'EMPLOYEE',
            'employee_id': 'EMP-001'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email='newuser@test.com').exists()
    
    def test_login_user(self, api_client, employee_user):
        """Test user login"""
        url = reverse('authentication:token_obtain_pair')
        data = {
            'email': 'employee@test.com',
            'password': 'testpass123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    def test_get_profile(self, authenticated_client, employee_user):
        """Test get user profile"""
        url = reverse('authentication:profile')
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == employee_user.email
    
    def test_change_password(self, authenticated_client):
        """Test password change"""
        url = reverse('authentication:change_password')
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass456',
            'new_password_confirm': 'newpass456'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
