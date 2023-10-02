import time
from micropython import const
from machine import Pin,UART

# Configure the serial port
uart = UART(1, baudrate=19200, tx=Pin(4), rx=Pin(5))
uart.init(bits=8, parity=None, stop=1)

while True:
    # Poll the serial port
    if uart.any():
        inData = uart.readline()
        print(inData)
        
    time.sleep_ms(500)