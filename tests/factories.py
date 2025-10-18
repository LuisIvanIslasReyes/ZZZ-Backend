"""
Factories for creating test data
"""
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from apps.authentication.models import Employee
from apps.devices.models import Device, SensorPacket, SensorSample, StressAggregate
from django.utils import timezone

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f'user{n}@test.com')
    username = factory.Sequence(lambda n: f'user{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    role = User.Role.EMPLOYEE


class EmployeeFactory(DjangoModelFactory):
    class Meta:
        model = Employee
    
    user = factory.SubFactory(UserFactory)
    employee_id = factory.Sequence(lambda n: f'EMP-{n:04d}')
    position = factory.Faker('job')
    department = factory.Faker('word')
    phone = factory.Faker('phone_number')


class DeviceFactory(DjangoModelFactory):
    class Meta:
        model = Device
    
    employee = factory.SubFactory(UserFactory)
    device_type = Device.DeviceType.WATCH
    hardware_id = factory.Sequence(lambda n: f'DEVICE-{n:08d}')
    model_name = 'Test Watch'
    firmware_version = '1.0.0'
    is_active = True


class SensorPacketFactory(DjangoModelFactory):
    class Meta:
        model = SensorPacket
    
    device = factory.SubFactory(DeviceFactory)
    packet_timestamp = factory.LazyFunction(timezone.now)
    raw_payload = factory.Dict({'test': 'data'})
    processed = False


class SensorSampleFactory(DjangoModelFactory):
    class Meta:
        model = SensorSample
    
    packet = factory.SubFactory(SensorPacketFactory)
    sample_time = factory.LazyFunction(timezone.now)
    heart_rate = factory.Faker('pyint', min_value=60, max_value=120)
    spo2 = factory.Faker('pyfloat', min_value=95, max_value=100)
    accel_x = factory.Faker('pyfloat', min_value=-2, max_value=2)
    accel_y = factory.Faker('pyfloat', min_value=-2, max_value=2)
    accel_z = factory.Faker('pyfloat', min_value=8, max_value=11)
    steps = factory.Faker('pyint', min_value=0, max_value=10000)
    battery_level = factory.Faker('pyint', min_value=20, max_value=100)


class StressAggregateFactory(DjangoModelFactory):
    class Meta:
        model = StressAggregate
    
    employee = factory.SubFactory(UserFactory)
    window_start = factory.LazyFunction(timezone.now)
    window_end = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(minutes=5))
    stress_score = factory.Faker('pyfloat', min_value=0, max_value=100)
    confidence = factory.Faker('pyfloat', min_value=0.5, max_value=1.0)
    avg_heart_rate = factory.Faker('pyfloat', min_value=60, max_value=120)
    heart_rate_variability = factory.Faker('pyfloat', min_value=5, max_value=30)
    movement_intensity = factory.Faker('pyfloat', min_value=0, max_value=10)
    sample_count = factory.Faker('pyint', min_value=10, max_value=100)
