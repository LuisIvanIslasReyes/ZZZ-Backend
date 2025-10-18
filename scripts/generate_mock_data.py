"""
Script to generate mock sensor data and send to API
Usage: python scripts/generate_mock_data.py
"""
import requests
import random
import time
from datetime import datetime, timedelta
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api"
DEVICE_ID = "WATCH-EMP-001"  # Change to your device hardware_id
BATCH_SIZE = 60  # Send 60 samples per batch (1 minute of data at 1Hz)
SEND_INTERVAL = 60  # Send every 60 seconds

def generate_sensor_sample(timestamp, base_hr=75):
    """
    Generate a realistic sensor sample
    """
    # Simulate some variation
    hr = base_hr + random.randint(-10, 15)
    hr = max(50, min(150, hr))  # Keep in realistic range
    
    # SpO2 usually stays high unless there's an issue
    spo2 = random.uniform(95, 100)
    
    # Accelerometer - simulate some movement
    accel_x = random.uniform(-1, 1)
    accel_y = random.uniform(-1, 1)
    accel_z = random.uniform(8.5, 10.5)  # Gravity on z-axis
    
    # Steps increment slowly
    steps = random.randint(0, 5)
    
    # Battery drains slowly
    battery = random.randint(70, 100)
    
    return {
        'timestamp': timestamp.isoformat(),
        'hr': hr,
        'spo2': round(spo2, 1),
        'accel_x': round(accel_x, 3),
        'accel_y': round(accel_y, 3),
        'accel_z': round(accel_z, 3),
        'steps': steps,
        'battery': battery
    }


def login(email, password):
    """
    Login and get JWT token
    """
    response = requests.post(
        f"{API_BASE_URL}/auth/login/",
        json={'email': email, 'password': password}
    )
    
    if response.status_code == 200:
        return response.json()['access']
    else:
        print(f"Login failed: {response.text}")
        return None


def send_batch(token, device_id, samples):
    """
    Send batch of sensor samples to API
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'device_id': device_id,
        'firmware_version': '1.0.0',
        'samples': samples
    }
    
    response = requests.post(
        f"{API_BASE_URL}/sensor-data/",
        json=data,
        headers=headers
    )
    
    return response


def main():
    print("🔄 Mock Sensor Data Generator")
    print("=" * 50)
    
    # Login
    email = input("Enter email (default: juan.perez@stressmonitor.com): ").strip() or "juan.perez@stressmonitor.com"
    password = input("Enter password (default: employee123): ").strip() or "employee123"
    
    print("\n🔐 Logging in...")
    token = login(email, password)
    
    if not token:
        print("❌ Failed to login")
        return
    
    print("✅ Login successful!")
    
    device_id = input(f"Enter device ID (default: {DEVICE_ID}): ").strip() or DEVICE_ID
    
    print(f"\n📱 Generating data for device: {device_id}")
    print(f"📊 Batch size: {BATCH_SIZE} samples")
    print(f"⏱️  Send interval: {SEND_INTERVAL} seconds")
    print("\nPress Ctrl+C to stop\n")
    
    base_hr = 75
    total_steps = 0
    
    try:
        batch_count = 0
        while True:
            batch_count += 1
            
            # Generate samples
            samples = []
            start_time = datetime.now()
            
            for i in range(BATCH_SIZE):
                timestamp = start_time + timedelta(seconds=i)
                
                # Simulate stress patterns (higher HR during certain hours)
                hour = timestamp.hour
                if 14 <= hour <= 16:  # Afternoon stress peak
                    base_hr = 85
                elif 10 <= hour <= 12:  # Morning active
                    base_hr = 80
                else:
                    base_hr = 70
                
                sample = generate_sensor_sample(timestamp, base_hr)
                total_steps += sample['steps']
                sample['steps'] = total_steps
                samples.append(sample)
            
            # Send batch
            print(f"📤 Sending batch #{batch_count} ({len(samples)} samples)...", end=' ')
            
            response = send_batch(token, device_id, samples)
            
            if response.status_code == 201:
                print(f"✅ Success! (Avg HR: {sum(s['hr'] for s in samples) / len(samples):.1f})")
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
            
            # Wait before next batch
            time.sleep(SEND_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped by user")
        print(f"📊 Total batches sent: {batch_count}")


if __name__ == '__main__':
    main()
