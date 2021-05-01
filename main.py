from __future__ import print_function
import time
import sys

import board
import busio
import qwiic_ccs811
import qwiic_micro_oled
import adafruit_scd30
from adafruit_pm25.i2c import PM25_I2C
from digitalio import DigitalInOut, Direction, Pull
from prometheus_client import start_http_server, Gauge


try:
    oled = qwiic_micro_oled.QwiicMicroOled()
except:
    oled = None


reset_pin = None
# Create library object, use 'slow' 100KHz frequency!
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
# Connect to a PM2.5 sensor over I2C
pm25 = PM25_I2C(i2c, reset_pin)
scd = adafruit_scd30.SCD30(i2c)

ccs = qwiic_ccs811.QwiicCcs811()
ccs.begin()

if ccs.is_connected() == False:
    print("The Qwiic CCS811 device isn't connected to the system. Please check your connection", \
    file=sys.stderr)


def oled_print(shit, font=0):
    try:
        oled.clear(oled.PAGE)
        oled.set_font_type(font)
        oled.set_cursor(0, 0)
        for line in shit:
            oled.print(line)
            oled.write("\n")
        oled.display()
    except:
        print("oled not connected")
    for line in shit:
        print(line)
    return


eco2 = Gauge('eCO2', 'Effective CO2 estimated by Volatile Organic Compounds')
co2 = Gauge('CO2', 'Actual measured CO2')
temp = Gauge('temperature_c', 'Tempurature measured in C')
relative_humidity = Gauge('relative_humidity', 'Relative Humidity')
tvoc = Gauge('tvoc', 'Total volatile organic compounds measured') 
pm1 = Gauge('pm1', 'PM 1.0 air quality')
pm25g = Gauge('pm2_5', 'PM 2.5 air quality')
pm100 = Gauge('pm10', 'PM 10 air quality')


def collect():
    ccs.read_algorithm_results()
    aqdata = pm25.read()

    new_lines = []
    
    # get eCO2 measurement
    eco2m = ccs.get_co2()
    eco2.set(eco2m)
    new_lines.append(f"eCO2:\t%d" % eco2m)
    
    # Get tvoc measurment 
    tvocm = ccs.get_tvoc()
    tvoc.set(tvocm)
    new_lines.append(f"tVOC:\t%.2f" % tvocm)	
    
    # Measure particulate in the air
    pm1m = aqdata["pm10 standard"]
    pm1.set(pm1m)
    pm25m = aqdata["pm25 standard"]
    pm25g.set(pm25m)
    pm100m = aqdata["pm100 standard"]
    pm100.set(pm100m)
    new_lines.append(f"PM 1.0: %d\tPM2.5: %d\tPM10: %d" % (pm1m, pm25m, pm100m))

    # Measure CO2
    co2m = scd.CO2
    co2.set(co2m)
    new_lines.append(f"CO2: %d" % (co2m))

    # Measure Temp
    tempm = scd.temperature
    temp.set(tempm)
    new_lines.append(f"Temp: %d" % (tempm))

    # Measure humidity
    relative_humidity_m = scd.relative_humidity
    relative_humidity.set(relative_humidity_m)
    new_lines.append(f"RH: %d" % (relative_humidity_m))

    oled_print(new_lines)


def loop():
    
    while True:
        try: 
            collect()
        except Exception as e:
            print("error collecting stats")
            print(e)
        time.sleep(1)


if __name__ == '__main__':
    start_http_server(8000) 
    try:
        loop()
    except (KeyboardInterrupt, SystemExit) as exErr:
        print("\nEnding Basic Example")
        sys.exit(0)
