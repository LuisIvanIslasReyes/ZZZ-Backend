import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """API client for making requests"""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create an admin user"""
    return User.objects.create_user(
        email='admin@test.com',
        username='admin',
        password='testpass123',
        first_name='Admin',
        last_name='User',
        role=User.Role.ADMIN
    )


@pytest.fixture
def supervisor_user(db):
    """Create a supervisor user"""
    return User.objects.create_user(
        email='supervisor@test.com',
        username='supervisor',
        password='testpass123',
        first_name='Super',
        last_name='Visor',
        role=User.Role.SUPERVISOR
    )


@pytest.fixture
def employee_user(db):
    """Create an employee user"""
    return User.objects.create_user(
        email='employee@test.com',
        username='employee',
        password='testpass123',
        first_name='John',
        last_name='Doe',
        role=User.Role.EMPLOYEE
    )


@pytest.fixture
def authenticated_client(api_client, employee_user):
    """API client authenticated as employee"""
    api_client.force_authenticate(user=employee_user)
    return api_client
