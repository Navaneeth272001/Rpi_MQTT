import time
import bme680
from bh1745 import BH1745
import paho.mqtt.client as mqtt

# MQTT Broker Settings
broker_address = "192.168.1.134"
port = 1883
topic = "sensors"

# Initialize BME680 sensor
try:
    bme_sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except (RuntimeError, IOError):
    bme_sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

# Initialize BH1745 sensor
bh1745 = BH1745()
bh1745.setup()
bh1745.set_leds(1)
time.sleep(1.0)  # Skip the reading that happened before the LEDs were enabled

# MQTT Setup
client = mqtt.Client("sensor_publisher")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
    else:
        print("Failed to connect to MQTT broker, return code:", rc)

client.on_connect = on_connect
client.connect(broker_address, port)

try:
    while True:
        # Check if the client is connected to the MQTT broker
        if client.is_connected():
            # Read BME680 sensor data
            if bme_sensor.get_sensor_data():
                bme_temperature = bme_sensor.data.temperature
                bme_pressure = bme_sensor.data.pressure
                bme_humidity = bme_sensor.data.humidity

            # Read BH1745 sensor data
            r, g, b, c = bh1745.get_rgbc_raw()

            # Prepare payload
            payload = f"BME680: Temperature={bme_temperature:.2f}C, Pressure={bme_pressure:.2f}hPa, Humidity={bme_humidity:.2f}%RH | BH1745: RGBC={r:.1f} {g:.1f} {b:.1f} {c:.1f}"

            # Publish sensor readings to MQTT topic
            client.publish(topic, payload)

            # Print sensor readings
            print(payload)

        else:
            print("Not connected to MQTT broker. Reconnecting...")
            client.reconnect()

        time.sleep(0.5)

except KeyboardInterrupt:
    bh1745.set_leds(0)
    client.disconnect()
