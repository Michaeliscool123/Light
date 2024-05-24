import digitalio
import ssl
import wifi
import socketpool
import adafruit_requests
import time
import board
import terminalio
import displayio
from adafruit_bme680 import Adafruit_BME680_I2C
from adafruit_display_text import label
from digitalio import DigitalInOut, Direction

# Create a variable to control pin D10
relay = DigitalInOut(board.D10)
relay.direction = Direction.OUTPUT

LED_PIN = board.D13
PIR_PIN = board.D5

pir = digitalio.DigitalInOut(PIR_PIN)
pir.direction = digitalio.Direction.INPUT

led = digitalio.DigitalInOut(LED_PIN)
led.direction = digitalio.Direction.OUTPUT

i2c = board.I2C()
bme680 = Adafruit_BME680_I2C(i2c)

WIFI_SSID = "CodingMinds"
WIFI_PASSWORD = "codingmindsgo!"

wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

FIREBASE_URL = "https://myprojectlamp-default-rtdb.firebaseio.com/"
firebase_path = FIREBASE_URL + "data.json"

# Initialize the default display
display = board.DISPLAY

# Set up the display group
g = displayio.Group()

# Create displayio.Label elements with the terminalio font
temp_text = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=10, y=10)
gas_text = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=10, y=25)
humidity_text = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=10, y=40)
pressure_text = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=10, y=55)

motion_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=65, y=90)

g.append(temp_text)
g.append(gas_text)
g.append(humidity_text)
g.append(pressure_text)
g.append(motion_label)
display.show(g)

motion_detected = False
motion_timer = None  # Added this line to initialize motion_timer

cooldown_period = 10
cooldown_timer = None

while True:
    temperature = bme680.temperature
    gas = bme680.gas
    humidity = bme680.relative_humidity
    pressure = bme680.pressure
    pir_value = pir.value

    if pir_value:
        led.value = True
        if not motion_detected:
            print('Motion detected!')
            relay.value = True  # Turn on the relay
            if relay.value == True: 
                print("The lamp is turning on")
            motion_detected = True

            motion_label.text = "Motion Detected!"  # Update display label

            print("\nTemperature: %0.1f C" % temperature)
            print("Gas: %d ohm" % gas)
            print("Humidity: %0.1f %%" % humidity)
            print("Pressure: %0.3f hPa" % pressure)

            data = {
                'temperature': temperature,
                'gas': gas,
                'humidity': humidity,
                'pressure': pressure
            }

            requests.post(firebase_path, json=data)

            # Update display
            temp_text.text = "Temperature: %0.1f C" % temperature
            gas_text.text = "Gas: %d ohm" % gas
            humidity_text.text = "Humidity: %0.1f %%" % humidity
            pressure_text.text = "Pressure: %0.3f hPa" % pressure

            # Set a timer for quick checks (adjust the sleep interval as needed)
            motion_timer = time.monotonic() + 2  # Check every 2 seconds (Changed line)

    elif motion_detected and motion_timer is not None and time.monotonic() > motion_timer:
        # Motion has stopped, perform actions for motion end
        if cooldown_timer is None:
            cooldown_timer = time.monotonic() + cooldown_period
            print('Motion ended, cooldown period beginning')
        elif time.monotonic() > cooldown_timer:
            print("Cooldown period has ended, the lamp is turning off")
            relay.value = False  # Turn off the relay
            if relay.value == False:
                print("The light is turning off ")
            motion_detected = False

            motion_label.text = "Motion Ended!"  # Update display label

            # Clear sensor data on the display
            temp_text.text = gas_text.text = humidity_text.text = pressure_text.text = ""
            cooldown_timer = None # Resets the timer
            motion_timer = None  # Reset the timer

    time.sleep(0.01)
