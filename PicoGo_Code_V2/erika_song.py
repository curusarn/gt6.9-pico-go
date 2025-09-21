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
B4 = 494
C5 = 523

def play_note(frequency, duration):
    """Play a note at given frequency for duration milliseconds"""
    if frequency == 0:  # Rest
        time.sleep(duration / 1000)
    else:
        buzzer.freq(frequency)
        buzzer.duty_u16(32768)  # 50% duty cycle
        time.sleep(duration / 1000)
        buzzer.duty_u16(0)  # Turn off
    time.sleep(0.01)  # Small gap between notes

def play_erika():
    """Play the Erika marching song melody"""
    # Tempo
    beat = 300  # milliseconds per beat
    
    # Melody - simplified version of Erika
    # Each tuple is (note_frequency, duration_in_beats)
    melody = [
        # First phrase
        (G4, 1), (G4, 0.5), (G4, 0.5), (E4, 1), (G4, 1),
        (C5, 2), (B4, 1), (A4, 1),
        (G4, 1), (G4, 0.5), (G4, 0.5), (E4, 1), (G4, 1),
        (A4, 3), (0, 1),  # Rest
        
        # Second phrase
        (A4, 1), (A4, 0.5), (A4, 0.5), (F4, 1), (A4, 1),
        (C5, 2), (B4, 1), (A4, 1),
        (G4, 1), (G4, 0.5), (G4, 0.5), (E4, 1), (G4, 1),
        (G4, 3), (0, 1),  # Rest
        
        # Third phrase (repeat of first)
        (G4, 1), (G4, 0.5), (G4, 0.5), (E4, 1), (G4, 1),
        (C5, 2), (B4, 1), (A4, 1),
        (G4, 1), (G4, 0.5), (G4, 0.5), (E4, 1), (G4, 1),
        (C4, 3),
    ]
    
    print("Playing Erika marching song...")
    
    # Play the melody
    for note, beats in melody:
        play_note(note, beat * beats)
    
    print("Song complete!")

# Play the song
play_erika()

# Clean up
buzzer.deinit()