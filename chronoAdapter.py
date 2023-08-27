# Adapater for LMBR chrony

import bluetooth
import random
import struct
import time
import queue
from ble_advertising import advertising_payload
from micropython import const
from machine import Pin,UART

"""
Adapter code for Pi Pico W & LMBR chronograph

LMBR uses a DE9 connector to output data over serial; Pico can do Bluetooth (as of Jun 2023)
This implements a simple polling loop to read lines off the UART (pins 4 & 5 on the Pico - remember
this will need a level shifter or you'll fry the Pico), printing it to the USB serial (so that can
be connected if needed) and transmitting it via BLE as a simple UART peripheral.
Buffering is provided by a queue - micropython does not include queue as standard, try

https://github.com/peterhinch/micropython-async/blob/master/v3/primitives/queue.py

Device will adverties as pyLMBR by default
Serial port settings on LMBR are 19200/8/no/1, no flow control according to the manual

Possible issues:
If the Bluetooth does not connect, the queue will eventually run out of memory.
If the LMBR does not output a complete line the read will stall.

Please note that the BT lib in particular is not free for commercial use.
"""
deviceName = "pyLMBR"

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)


class BLESimplePeripheral:
    """
    Simple peripheral example of Bluetooth (BLE) comms from
    https://electrocredible.com/raspberry-pi-pico-w-bluetooth-ble-micropython/
    """
    def __init__(self, ble, name="mpy-uart"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._write_callback = None
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            # print("New connection", conn_handle)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            # print("Disconnected", conn_handle)
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=500000):
        # print("Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def on_write(self, callback):
        self._write_callback = callback

def lmbrAdapter():
    """
    Quick & dirty adapter code - read the UART, buffer any data & print it on
    the default serial port, then try to send it out via BLE
    """
    ble = bluetooth.BLE()
    peripheral = BLESimplePeripheral(ble, deviceName)

    # Configure the serial port
    uart = UART(1, baudrate=19200, tx=Pin(4), rx=Pin(5))
    uart.init(bits=8, parity=None, stop=1)

    serialBuffer = queue.Queue()
    
    while True:
        # Poll the serial port
        if uart.any():
            # Too lazy to build this char by char
            speedData = uart.readline()
            # Assumes the link will be up before we blow the memory out of the water
            serialBuffer.put(speedData)
            print(speedData)
        
        if peripheral.is_connected():
            while not serialBuffer.empty():
                # Blithely assuming the link stays up all the way through - OK as first pass, not so good for a robust system
                peripheral.write(serialBuffer.get())
           
        time.sleep_ms(1000)
        
if __name__ == "__main__":
    lmbrAdapter()