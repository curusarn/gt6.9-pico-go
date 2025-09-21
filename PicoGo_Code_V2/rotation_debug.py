from machine import Pin, PWM
import time

# Initialize pins directly
PWMA = PWM(Pin(16))
PWMA.freq(1000)
AIN1 = Pin(18, Pin.OUT)
AIN2 = Pin(17, Pin.OUT)

PWMB = PWM(Pin(21))
PWMB.freq(1000)
BIN1 = Pin(19, Pin.OUT)
BIN2 = Pin(20, Pin.OUT)

def stop_all():
    PWMA.duty_u16(0)
    PWMB.duty_u16(0)
    AIN1.value(0)
    AIN2.value(0)
    BIN1.value(0)
    BIN2.value(0)

print("Rotation Debug Test")
print("==================")

# Test each motor individually first
print("\n1. Testing Motor A only - Forward")
stop_all()
AIN1.value(0)
AIN2.value(1)
PWMA.duty_u16(int(30 * 0xFFFF / 100))
time.sleep(2)
stop_all()
time.sleep(1)

print("\n2. Testing Motor A only - Backward")
AIN1.value(1)
AIN2.value(0)
PWMA.duty_u16(int(30 * 0xFFFF / 100))
time.sleep(2)
stop_all()
time.sleep(1)

print("\n3. Testing Motor B only - Forward")
BIN1.value(0)
BIN2.value(1)
PWMB.duty_u16(int(30 * 0xFFFF / 100))
time.sleep(2)
stop_all()
time.sleep(1)

print("\n4. Testing Motor B only - Backward")
BIN1.value(1)
BIN2.value(0)
PWMB.duty_u16(int(30 * 0xFFFF / 100))
time.sleep(2)
stop_all()
time.sleep(1)

print("\n5. Testing rotation - A forward, B backward (should turn one way)")
AIN1.value(0)
AIN2.value(1)
BIN1.value(1)
BIN2.value(0)
PWMA.duty_u16(int(30 * 0xFFFF / 100))
PWMB.duty_u16(int(30 * 0xFFFF / 100))
time.sleep(3)
stop_all()
time.sleep(1)

print("\n6. Testing rotation - A backward, B forward (should turn other way)")
AIN1.value(1)
AIN2.value(0)
BIN1.value(0)
BIN2.value(1)
PWMA.duty_u16(int(30 * 0xFFFF / 100))
PWMB.duty_u16(int(30 * 0xFFFF / 100))
time.sleep(3)
stop_all()

print("\nTest complete!")
print("Note which tests worked and which didn't")