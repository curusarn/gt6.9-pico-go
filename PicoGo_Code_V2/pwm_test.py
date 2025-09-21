from machine import Pin, PWM
import time

print("Testing PWM on both motor pins")
print("==============================")

# Test PWM on Pin 16 (Motor A)
print("\nTesting Pin 16 (Motor A PWM)...")
try:
    pwm16 = PWM(Pin(16))
    pwm16.freq(1000)
    pwm16.duty_u16(32768)  # 50% duty cycle
    print("✓ Pin 16 PWM initialized successfully")
    time.sleep(0.5)
    pwm16.duty_u16(0)
    pwm16.deinit()
except Exception as e:
    print(f"✗ Pin 16 PWM error: {e}")

# Test PWM on Pin 21 (Motor B)
print("\nTesting Pin 21 (Motor B PWM)...")
try:
    pwm21 = PWM(Pin(21))
    pwm21.freq(1000)
    pwm21.duty_u16(32768)  # 50% duty cycle
    print("✓ Pin 21 PWM initialized successfully")
    time.sleep(0.5)
    pwm21.duty_u16(0)
    pwm21.deinit()
except Exception as e:
    print(f"✗ Pin 21 PWM error: {e}")

# Try alternative pin for Motor B if Pin 21 has issues
print("\nTesting Pin 19 as alternative PWM...")
try:
    pwm19 = PWM(Pin(19))
    pwm19.freq(1000)
    pwm19.duty_u16(32768)  # 50% duty cycle
    print("✓ Pin 19 PWM initialized successfully")
    time.sleep(0.5)
    pwm19.duty_u16(0)
    pwm19.deinit()
except Exception as e:
    print(f"✗ Pin 19 PWM error: {e}")

print("\nPWM test complete!")