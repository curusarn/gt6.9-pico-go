from machine import Pin, PWM
import time

# Initialize buzzer with PWM
buzzer = PWM(Pin(4))

# Note frequencies
C4 = 262
D4 = 294
E4 = 330
F4 = 349
G4 = 392
A4 = 440
Bb4 = 466
B4 = 494
C5 = 523
D5 = 587
E5 = 659
F5 = 698
G5 = 784
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

def play_black_parade():
    """Play the main melody from Welcome to the Black Parade"""
    # Tempo
    tempo = 100  # BPM
    beat = 60000 / tempo / 4  # milliseconds per quarter beat
    
    # The opening piano/guitar melody
    # Each tuple is (note_frequency, duration_in_quarter_beats)
    melody = [
        # Opening piano intro (simplified)
        (G4, 4), (G4, 2), (F4, 2),
        (G4, 4), (G4, 2), (F4, 2),
        (G4, 2), (G4, 2), (A4, 2), (G4, 2),
        (F4, 8),
        (0, 4),  # Rest
        
        # Main theme
        (C5, 2), (C5, 2), (C5, 2), (D5, 2),
        (E5, 4), (D5, 4),
        (C5, 2), (C5, 2), (C5, 2), (D5, 2),
        (E5, 2), (D5, 2), (C5, 4),
        (0, 2),  # Rest
        
        # Second part
        (G4, 2), (A4, 2), (C5, 4),
        (D5, 2), (C5, 2), (A4, 4),
        (G4, 2), (A4, 2), (C5, 4),
        (A4, 8),
        (0, 4),  # Rest
        
        # Bridge section
        (F4, 4), (G4, 4),
        (A4, 4), (C5, 4),
        (D5, 2), (C5, 2), (A4, 2), (G4, 2),
        (F4, 8),
        
        # Ending phrase
        (C5, 2), (C5, 2), (D5, 2), (E5, 2),
        (G5, 4), (E5, 4),
        (D5, 4), (C5, 4),
        (G4, 8),
    ]
    
    print("Playing Welcome to the Black Parade melody...")
    print("When I was a young boy...")
    
    # Play the melody
    for note, duration in melody:
        play_note(note, beat * duration)
    
    print("Song complete!")

# Play the Black Parade
play_black_parade()

# Clean up
buzzer.deinit()