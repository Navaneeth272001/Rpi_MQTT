#!/usr/bin/env python
import os
import sys
import paho.mqtt.client as mqtt
import json
import bme680
from bh1745 import BH1745
import time

bh1745 = BH1745()
bh1745.setup()
bh1745.set_leds(1)
time.sleep(1.0)

THINGSBOARD_HOST = 'nganou.internet-box.ch'
INTERVAL=2


print("""read-all.py - Displays temperature, pressure, humidity, and gas.

Press Ctrl+C to exit!

""")

sensor_data = {'temperature': 0, 'humidity': 0}

next_reading = time.time() 

client = mqtt.Client()

client.connect(THINGSBOARD_HOST, 1883, 60)

client.loop_start()

try:
    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except (RuntimeError, IOError):
    sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

# These calibration data can safely be commented
# out, if desired.

print('Calibration data:')
for name in dir(sensor.calibration_data):

    if not name.startswith('_'):
        value = getattr(sensor.calibration_data, name)

        if isinstance(value, int):
            print('{}: {}'.format(name, value))

# These oversampling settings can be tweaked to
# change the balance between accuracy and noise in
# the data.

sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

print('\n\nInitial reading:')
for name in dir(sensor.data):
    value = getattr(sensor.data, name)

    if not name.startswith('_'):
        print('{}: {}'.format(name, value))

sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)

# Up to 10 heater profiles can be configured, each
# with their own temperature and duration.
# sensor.set_gas_heater_profile(200, 150, nb_profile=1)
# sensor.select_gas_heater_profile(1)

print('\n\nPolling:')
try:
    while True:
        if sensor.get_sensor_data():
            output = '{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH'.format(
                sensor.data.temperature,
                sensor.data.pressure,
                sensor.data.humidity)
            sensor_data['temperature'] = sensor.data.temperature
            sensor_data['humidity'] = sensor.data.humidity
            
            client.publish('v1/devices/me/telemetry', json.dumps(sensor_data), 1)

            if sensor.data.heat_stable:
                print('{0},{1} Ohms'.format(
                    output,
                    sensor.data.gas_resistance))

            else:
                print(output)
                
        r, g, b, c = bh1745.get_rgbc_raw()
        print('RGBC: {:10.1f} {:10.1f} {:10.1f} {:10.1f}'.format(r, g, b, c))
        time.sleep(0.5)
        next_reading += INTERVAL
        sleep_time = next_reading-time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)

except KeyboardInterrupt:
    pass

bh1745.set_leds(0)
client.loop_stop()
client.disconnect()