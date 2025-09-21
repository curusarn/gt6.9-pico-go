from machine import Pin, PWM
import time

# Create a PWM object on Pin 4 (buzzer pin)
buzzer = PWM(Pin(4))

# Define musical note frequencies (in Hz)
# These are standard musical note frequencies
NOTE_C4 = 262
NOTE_D4 = 294
NOTE_E4 = 330
NOTE_F4 = 349
NOTE_G4 = 392
NOTE_A4 = 440
NOTE_B4 = 494
NOTE_C5 = 523
NOTE_D5 = 587
NOTE_E5 = 659
NOTE_F5 = 698
NOTE_G5 = 784
NOTE_A5 = 880
NOTE_B5 = 988
NOTE_C6 = 1047

# Function to play a tone
def play_tone(frequency, duration):
    """
    Play a tone at the specified frequency for the specified duration.
    
    Args:
        frequency: Frequency in Hz
        duration: Duration in seconds
    """
    if frequency > 0:
        buzzer.freq(frequency)
        buzzer.duty_u16(32768)  # 50% duty cycle (32768/65535)
    time.sleep(duration)
    buzzer.duty_u16(0)  # Turn off buzzer

# Function to play a melody
def play_melody(notes, durations, tempo=1.0):
    """
    Play a melody given a list of notes and durations.
    
    Args:
        notes: List of frequencies (use 0 for rest)
        durations: List of durations for each note
        tempo: Speed multiplier (1.0 = normal, 0.5 = double speed, 2.0 = half speed)
    """
    for i in range(len(notes)):
        if notes[i] > 0:
            buzzer.freq(notes[i])
            buzzer.duty_u16(32768)  # 50% duty cycle
        time.sleep(durations[i] * tempo)
        buzzer.duty_u16(0)  # Turn off buzzer
        time.sleep(0.05 * tempo)  # Small gap between notes

# Example: Play a simple scale
def play_scale():
    """Play a C major scale up and down"""
    print("Playing C major scale...")
    scale = [NOTE_C4, NOTE_D4, NOTE_E4, NOTE_F4, NOTE_G4, NOTE_A4, NOTE_B4, NOTE_C5,
             NOTE_C5, NOTE_B4, NOTE_A4, NOTE_G4, NOTE_F4, NOTE_E4, NOTE_D4, NOTE_C4]
    for note in scale:
        play_tone(note, 0.2)
        time.sleep(0.05)  # Small gap between notes

# Example: Play a simple tune (Mary Had a Little Lamb)
def play_mary_had_a_little_lamb():
    """Play Mary Had a Little Lamb"""
    print("Playing Mary Had a Little Lamb...")
    notes = [
        NOTE_E4, NOTE_D4, NOTE_C4, NOTE_D4, NOTE_E4, NOTE_E4, NOTE_E4, 0,  # Mary had a little lamb
        NOTE_D4, NOTE_D4, NOTE_D4, 0, NOTE_E4, NOTE_G4, NOTE_G4, 0,       # Little lamb, little lamb
        NOTE_E4, NOTE_D4, NOTE_C4, NOTE_D4, NOTE_E4, NOTE_E4, NOTE_E4,    # Mary had a little lamb
        NOTE_E4, NOTE_D4, NOTE_D4, NOTE_E4, NOTE_D4, NOTE_C4              # Its fleece was white as snow
    ]
    
    durations = [
        0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.8, 0.2,
        0.4, 0.4, 0.8, 0.2, 0.4, 0.4, 0.8, 0.2,
        0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4,
        0.4, 0.4, 0.4, 0.4, 0.4, 0.8
    ]
    
    play_melody(notes, durations, tempo=1.2)

# Example: Sound effects
def play_startup_sound():
    """Play a startup sound effect"""
    print("Playing startup sound...")
    for freq in range(200, 1000, 100):
        play_tone(freq, 0.05)

def play_shutdown_sound():
    """Play a shutdown sound effect"""
    print("Playing shutdown sound...")
    for freq in range(1000, 200, -100):
        play_tone(freq, 0.05)

def play_alert_sound():
    """Play an alert/warning sound"""
    print("Playing alert sound...")
    for _ in range(3):
        play_tone(800, 0.1)
        time.sleep(0.1)
        play_tone(600, 0.1)
        time.sleep(0.1)

def play_error_sound():
    """Play an error sound"""
    print("Playing error sound...")
    play_tone(100, 0.5)

def play_success_sound():
    """Play a success/completion sound"""
    print("Playing success sound...")
    play_tone(523, 0.1)  # C5
    play_tone(659, 0.1)  # E5
    play_tone(784, 0.2)  # G5

# Main program
if __name__ == "__main__":
    print("Raspberry Pi Pico Buzzer PWM Demo")
    print("==================================")
    print("This demo shows how to generate different tones using PWM")
    print()
    
    try:
        # Play different sounds
        play_startup_sound()
        time.sleep(1)
        
        play_scale()
        time.sleep(1)
        
        play_mary_had_a_little_lamb()
        time.sleep(1)
        
        play_success_sound()
        time.sleep(1)
        
        play_alert_sound()
        time.sleep(1)
        
        play_shutdown_sound()
        
    except KeyboardInterrupt:
        print("\nProgram interrupted")
    finally:
        # Make sure buzzer is off
        buzzer.duty_u16(0)
        buzzer.deinit()
        print("Buzzer demo completed!")