"""
Celery tasks for sensor data processing
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
import numpy as np

logger = logging.getLogger(__name__)


@shared_task
def process_sensor_packet(packet_id):
    """
    Process a sensor packet: extract features and calculate stress score
    """
    from .models import SensorPacket, StressAggregate
    
    try:
        packet = SensorPacket.objects.get(id=packet_id)
        
        # Get samples from this packet
        samples = packet.samples.all()
        
        if not samples.exists():
            logger.warning(f"No samples found for packet {packet_id}")
            return
        
        # Extract features
        hr_values = [s.heart_rate for s in samples if s.heart_rate]
        accel_values = [(s.accel_x, s.accel_y, s.accel_z) 
                       for s in samples if all([s.accel_x, s.accel_y, s.accel_z])]
        
        if not hr_values:
            logger.warning(f"No valid HR data in packet {packet_id}")
            packet.processed = True
            packet.processed_at = timezone.now()
            packet.save()
            return
        
        # Calculate features
        avg_hr = np.mean(hr_values)
        hr_std = np.std(hr_values) if len(hr_values) > 1 else 0
        
        # Movement intensity (magnitude of acceleration)
        movement_intensity = 0
        if accel_values:
            magnitudes = [np.sqrt(x**2 + y**2 + z**2) for x, y, z in accel_values]
            movement_intensity = np.mean(magnitudes)
        
        # Calculate stress score (simple heuristic for v1.0)
        stress_score = calculate_stress_score(avg_hr, hr_std, movement_intensity)
        
        # Create or update stress aggregate
        window_start = samples.first().sample_time
        window_end = samples.last().sample_time
        
        StressAggregate.objects.update_or_create(
            employee=packet.device.employee,
            window_start=window_start,
            window_end=window_end,
            defaults={
                'stress_score': stress_score,
                'confidence': 0.8,  # Base confidence
                'avg_heart_rate': avg_hr,
                'heart_rate_variability': hr_std,
                'movement_intensity': movement_intensity,
                'sample_count': len(hr_values),
                'method_version': 'v1.0'
            }
        )
        
        # Mark packet as processed
        packet.processed = True
        packet.processed_at = timezone.now()
        packet.save()
        
        logger.info(f"Processed packet {packet_id} - Stress score: {stress_score:.2f}")
        
        # Check if notification should be sent
        if stress_score > 75:  # High stress threshold
            send_stress_alert.delay(packet.device.employee.id, stress_score)
        
    except Exception as e:
        logger.error(f"Error processing packet {packet_id}: {str(e)}")
        raise


def calculate_stress_score(avg_hr, hr_variability, movement_intensity):
    """
    Calculate stress score based on physiological indicators
    
    This is a simple heuristic model (v1.0). In production, this would be
    replaced with a trained ML model.
    
    Score ranges:
    - 0-30: Low stress
    - 31-60: Moderate stress
    - 61-80: High stress
    - 81-100: Very high stress
    """
    score = 0
    
    # Heart rate component (40% weight)
    # Assuming resting HR ~70, stressed HR ~100+
    if avg_hr < 60:
        hr_score = 10
    elif avg_hr < 80:
        hr_score = 30
    elif avg_hr < 100:
        hr_score = 60
    else:
        hr_score = 90
    
    score += hr_score * 0.4
    
    # HRV component (30% weight) - lower HRV = higher stress
    if hr_variability < 5:
        hrv_score = 80  # Very low variability = high stress
    elif hr_variability < 10:
        hrv_score = 50
    elif hr_variability < 20:
        hrv_score = 30
    else:
        hrv_score = 10  # High variability = low stress
    
    score += hrv_score * 0.3
    
    # Movement component (30% weight)
    # High movement with high HR might indicate physical activity, not stress
    # Low movement with high HR might indicate mental stress
    if movement_intensity < 2:  # Low movement
        if avg_hr > 85:
            movement_score = 80  # Sedentary + high HR = potential stress
        else:
            movement_score = 20
    else:  # High movement
        movement_score = 40  # Physical activity
    
    score += movement_score * 0.3
    
    # Normalize to 0-100
    return min(100, max(0, score))


@shared_task
def send_stress_alert(employee_id, stress_score):
    """
    Send stress alert notification via FCM
    """
    from django.contrib.auth import get_user_model
    from apps.authentication.models import Employee
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=employee_id)
        employee = user.employee_profile
        
        if not employee.notifications_enabled or not employee.fcm_token:
            logger.info(f"Notifications disabled or no FCM token for employee {employee_id}")
            return
        
        # TODO: Implement actual FCM push notification
        # For now, just log
        logger.info(
            f"ALERT: High stress detected for {user.get_full_name()} - "
            f"Score: {stress_score:.1f}"
        )
        
        # Also notify supervisor if exists
        if employee.supervisor:
            supervisor_profile = getattr(employee.supervisor, 'employee_profile', None)
            if supervisor_profile and supervisor_profile.fcm_token:
                logger.info(
                    f"ALERT: Notifying supervisor {employee.supervisor.get_full_name()} "
                    f"about {user.get_full_name()}'s high stress"
                )
        
    except Exception as e:
        logger.error(f"Error sending stress alert for employee {employee_id}: {str(e)}")


@shared_task
def cleanup_old_data():
    """
    Periodic task to clean up old sensor data
    Run this daily via celery beat
    """
    from .models import SensorPacket, SensorSample
    
    try:
        # Delete raw packets older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        
        deleted_packets = SensorPacket.objects.filter(
            received_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Cleaned up old sensor data: {deleted_packets[0]} packets deleted")
        
    except Exception as e:
        logger.error(f"Error cleaning up old data: {str(e)}")
