from machine import Pin, PWM
import time

# Initialize buzzer with PWM
buzzer = PWM(Pin(4))

def play_tone(frequency, duration):
    """Play a tone at given frequency for duration seconds"""
    buzzer.freq(frequency)
    buzzer.duty_u16(32768)  # 50% duty cycle
    time.sleep(duration)
    buzzer.duty_u16(0)  # Turn off
    time.sleep(0.05)  # Small gap between notes

def play_scale():
    """Play a musical scale"""
    print("Playing scale...")
    notes = [262, 294, 330, 349, 392, 440, 494, 523]  # C4 to C5
    for note in notes:
        play_tone(note, 0.3)

def play_alarm():
    """Play an alarm sound"""
    print("Playing alarm...")
    for _ in range(3):
        play_tone(800, 0.2)
        play_tone(600, 0.2)

def play_startup():
    """Play a startup sound"""
    print("Playing startup sound...")
    play_tone(523, 0.1)  # C5
    play_tone(659, 0.1)  # E5
    play_tone(784, 0.2)  # G5

def play_success():
    """Play a success sound"""
    print("Playing success sound...")
    play_tone(523, 0.15)  # C5
    play_tone(784, 0.15)  # G5
    play_tone(1047, 0.3)  # C6

def play_error():
    """Play an error sound"""
    print("Playing error sound...")
    play_tone(200, 0.3)
    play_tone(150, 0.3)

def play_beeps():
    """Play simple beeps at different frequencies"""
    print("Playing beeps at different frequencies...")
    frequencies = [300, 500, 800, 1200, 2000]
    for freq in frequencies:
        print(f"  {freq} Hz")
        play_tone(freq, 0.2)
        time.sleep(0.1)

# Run all tests
print("=== PicoGo Buzzer PWM Test ===")
print()

print("Test 1: Musical Scale")
play_scale()
time.sleep(0.5)

print("\nTest 2: Startup Sound")
play_startup()
time.sleep(0.5)

print("\nTest 3: Success Sound")
play_success()
time.sleep(0.5)

print("\nTest 4: Error Sound")
play_error()
time.sleep(0.5)

print("\nTest 5: Alarm")
play_alarm()
time.sleep(0.5)

print("\nTest 6: Frequency Range")
play_beeps()

print("\nTest complete!")
buzzer.deinit()  # Clean up PWM