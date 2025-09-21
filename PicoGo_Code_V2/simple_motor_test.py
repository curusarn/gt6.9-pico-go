from machine import Pin, PWM
import time

# Test motors directly without using Motor class
# Motor A
AIN1 = Pin(18, Pin.OUT)
AIN2 = Pin(17, Pin.OUT)
PWMA = PWM(Pin(16))
PWMA.freq(1000)

# Motor B  
BIN1 = Pin(21, Pin.OUT)
BIN2 = Pin(20, Pin.OUT)
PWMB = PWM(Pin(19))
PWMB.freq(1000)

print("Direct Motor Test")

# Test Motor A forward
print("Motor A forward...")
AIN1.value(0)
AIN2.value(1)
PWMA.duty_u16(int(30 * 0xFFFF / 100))
time.sleep(2)

# Stop Motor A
print("Stop Motor A")
PWMA.duty_u16(0)
time.sleep(1)

# Test Motor B forward
print("Motor B forward...")
BIN1.value(0)
BIN2.value(1)
PWMB.duty_u16(int(30 * 0xFFFF / 100))
time.sleep(2)

# Stop Motor B
print("Stop Motor B")
PWMB.duty_u16(0)
time.sleep(1)

# Test both motors
print("Both motors forward...")
AIN1.value(0)
AIN2.value(1)
BIN1.value(0)
BIN2.value(1)
PWMA.duty_u16(int(30 * 0xFFFF / 100))
PWMB.duty_u16(int(30 * 0xFFFF / 100))
time.sleep(2)

# Stop all
print("Stop all")
PWMA.duty_u16(0)
PWMB.duty_u16(0)
AIN1.value(0)
AIN2.value(0)
BIN1.value(0)
BIN2.value(0)

print("Test complete!")

# Now test with Motor class
print("\nTesting with Motor class...")
from Motor import PicoGo
M = PicoGo()

print("M.forward(30)...")
M.forward(30)
time.sleep(2)

print("M.stop()...")
M.stop()
time.sleep(1)

print("M.right(20)...")
M.right(20)
time.sleep(2)

print("M.stop()...")
M.stop()

print("Motor class test complete!")