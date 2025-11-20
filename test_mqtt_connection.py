"""
Test de conexión MQTT básica
"""
import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado al broker MQTT")
        client.subscribe("devices/+/sensors")
        print("📡 Suscrito a topic: devices/+/sensors")
    else:
        print(f"❌ Error de conexión: {rc}")

def on_message(client, userdata, msg):
    print(f"\n📥 Mensaje recibido en topic: {msg.topic}")
    print(f"   Payload: {msg.payload.decode()}")

def on_disconnect(client, userdata, rc):
    print(f"⚠️  Desconectado. Código: {rc}")

print("=" * 60)
print("TEST DE CONEXIÓN MQTT")
print("=" * 60)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

try:
    print("\n🔄 Conectando a localhost:1883...")
    client.connect("localhost", 1883, 60)
    client.loop_start()
    
    print("✅ Cliente iniciado. Esperando mensajes...")
    print("Presiona Ctrl+C para detener\n")
    
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\n\n🛑 Deteniendo...")
    client.loop_stop()
    client.disconnect()
    print("✅ Desconectado")
except Exception as e:
    print(f"\n❌ Error: {e}")
