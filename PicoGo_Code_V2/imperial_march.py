from machine import Pin, PWM
import time

# Initialize buzzer with PWM
buzzer = PWM(Pin(4))

# Note frequencies
C4 = 262
D4 = 294
Eb4 = 311
E4 = 330
F4 = 349
G4 = 392
Ab4 = 415
A4 = 440
Bb4 = 466
B4 = 494
C5 = 523
D5 = 587
Eb5 = 622
E5 = 659
F5 = 698
G5 = 784
Ab5 = 831
A5 = 880

def play_note(frequency, duration):
    """Play a note at given frequency for duration milliseconds"""
    if frequency == 0:  # Rest
        time.sleep(duration / 1000)
    else:
        buzzer.freq(frequency)
        buzzer.duty_u16(32768)  # 50% duty cycle
        time.sleep(duration / 1000)
        buzzer.duty_u16(0)  # Turn off
    time.sleep(0.02)  # Small gap between notes

def play_imperial_march():
    """Play the Imperial March from Star Wars"""
    # Tempo
    tempo = 120  # BPM
    beat = 60000 / tempo / 4  # milliseconds per quarter beat
    
    # The Imperial March melody
    # Each tuple is (note_frequency, duration_in_quarter_beats)
    melody = [
        # First phrase
        (A4, 4), (A4, 4), (A4, 4), 
        (F4, 3), (C5, 1),
        (A4, 4), (F4, 3), (C5, 1), (A4, 8),
        (0, 4),  # Rest
        
        (E5, 4), (E5, 4), (E5, 4),
        (F5, 3), (C5, 1),
        (Ab4, 4), (F4, 3), (C5, 1), (A4, 8),
        (0, 4),  # Rest
        
        # Second phrase
        (A5, 4), (A4, 3), (A4, 1),
        (A5, 4), (Ab5, 3), (G5, 1),
        (F5, 1), (E5, 1), (F5, 2), (0, 2), (Bb4, 2),
        (Eb5, 4), (D5, 3), (C5, 1),
        
        # Third phrase
        (B4, 1), (C5, 1), (D5, 2), (0, 2), (F4, 2),
        (G4, 4), (F4, 3), (A4, 1),
        (C5, 4), (A4, 3), (C5, 1), (E5, 8),
        (0, 4),  # Rest
        
        # Repeat first phrase (simplified ending)
        (A4, 4), (A4, 4), (A4, 4),
        (F4, 3), (C5, 1),
        (A4, 4), (F4, 3), (C5, 1), (A4, 8),
    ]
    
    print("Playing Imperial March (Star Wars)...")
    print("The Force is strong with this buzzer!")
    
    # Play the melody
    for note, duration in melody:
        play_note(note, beat * duration)
    
    print("May the Force be with you!")

# Play the Imperial March
play_imperial_march()

# Clean up
buzzer.deinit()