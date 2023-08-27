# lmbrAdapter

The LMBR chronograph ( https://lmbr.pl/ ) is a useful tool, but marred slightly by the lack of support for modern interfaces.
It uses a simple UART led out via a DE9 connector (I'd call it RS232, but the levels aren't technically correct).
There is a Bluetooth adapater that is unavailable at time of writing, so I'm looking at the recently added BLE functionality extending the Pi Pico W ( https://www.raspberrypi.com/products/raspberry-pi-pico/ ) under MicroPython ( https://micropython.org/ )

Hardware requirements are a Pi Pico W, a level shifter connected to pins 4 & 5/UART0 (please don't put > 3V3 into a Pico GPIO, they don't like it) and, of course, a DE9 male connector.

The BLE code is used from https://electrocredible.com/raspberry-pi-pico-w-bluetooth-ble-micropython/ as an intro point; this implements a simple UART device that can be read by e.g. https://play.google.com/store/apps/details?id=de.kai_morich.serial_bluetooth_terminal&hl=en_GB&gl=US
The queue code (micropython doesn't currently implement queues, although for this example I could have used a list) is at https://github.com/peterhinch/micropython-async/blob/master/v3/primitives/queue.py

This is under development only.  I'm hoping there's enough power available to run the Pico from the port, but that remains to be seen.
The code itself is crude; it's just a polling loop.  
It's not meant to be pretty, it's just for a demonstration.
