# boot.py - Runs on boot
import network
import time

# Configure WiFi here
SSID = "YOUR_WIFI_SSID"
PASSWORD = "YOUR_WIFI_PASSWORD"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(SSID, PASSWORD)
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            time.sleep(1)
            
    if wlan.isconnected():
        print('Network config:', wlan.ifconfig())
    else:
        print('WiFi connection failed, starting AP mode...')
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid='BarcodeScanner-AP')
        print('AP active at:', ap.ifconfig())

# connect_wifi() # Uncomment to enable WiFi
