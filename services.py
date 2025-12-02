import os
import threading
import time
from typing import Optional

# Configuration (mirrored from original app.py)
class Config:
    USE_GPIO = os.environ.get('USE_GPIO', 'false').lower() == 'true'
    PIN_ALARM_RELAY = 17
    PIN_PASS_LIGHT = 27
    PIN_FAIL_LIGHT = 22
    PIN_LINE_STOP = 23
    ALARM_DURATION = 3.0

class GPIOController:
    """Handles GPIO operations for relays and indicators"""
    
    def __init__(self):
        self.initialized = False
        self.gpio = None
        
        if Config.USE_GPIO:
            try:
                import RPi.GPIO as GPIO
                self.gpio = GPIO
                self._setup()
            except ImportError:
                print("[GPIO] RPi.GPIO not available - running in simulation mode")
    
    def _setup(self):
        try:
            self.gpio.setmode(self.gpio.BCM)
            self.gpio.setwarnings(False)
            pins = [Config.PIN_ALARM_RELAY, Config.PIN_PASS_LIGHT, 
                    Config.PIN_FAIL_LIGHT, Config.PIN_LINE_STOP]
            for pin in pins:
                self.gpio.setup(pin, self.gpio.OUT)
                self.gpio.output(pin, self.gpio.LOW)
            self.initialized = True
            print("[GPIO] Initialized successfully")
        except Exception as e:
            print(f"[GPIO] Setup failed: {e}")
    
    def trigger_pass(self):
        if not self.initialized:
            print("[GPIO SIM] PASS")
            return
        self.gpio.output(Config.PIN_PASS_LIGHT, self.gpio.HIGH)
        self.gpio.output(Config.PIN_FAIL_LIGHT, self.gpio.LOW)
        t = threading.Timer(1.0, lambda: self.gpio.output(Config.PIN_PASS_LIGHT, self.gpio.LOW))
        t.daemon = True
        t.start()
    
    def trigger_fail(self):
        if not self.initialized:
            print("[GPIO SIM] FAIL - ALARM!")
            return
        self.gpio.output(Config.PIN_FAIL_LIGHT, self.gpio.HIGH)
        self.gpio.output(Config.PIN_PASS_LIGHT, self.gpio.LOW)
        self._trigger_alarm()
    
    def _trigger_alarm(self):
        def alarm_sequence():
            if self.initialized:
                self.gpio.output(Config.PIN_ALARM_RELAY, self.gpio.HIGH)
                time.sleep(Config.ALARM_DURATION)
                self.gpio.output(Config.PIN_ALARM_RELAY, self.gpio.LOW)
                self.gpio.output(Config.PIN_FAIL_LIGHT, self.gpio.LOW)
        threading.Thread(target=alarm_sequence, daemon=True).start()
    
    def all_off(self):
        if self.initialized:
            pins = [Config.PIN_ALARM_RELAY, Config.PIN_PASS_LIGHT, 
                    Config.PIN_FAIL_LIGHT, Config.PIN_LINE_STOP]
            for pin in pins:
                self.gpio.output(pin, self.gpio.LOW)
    
    def cleanup(self):
        if self.initialized:
            self.all_off()
            self.gpio.cleanup()

# Singleton instance
gpio_controller = GPIOController()
