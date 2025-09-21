from machine import Pin, PWM
import time

# Initialize buzzer with PWM
buzzer = PWM(Pin(4))

# Note frequencies
C3 = 131
D3 = 147
Eb3 = 156
E3 = 165
F3 = 175
G3 = 196
Ab3 = 208
A3 = 220
B3 = 247
C4 = 262
D4 = 294
Eb4 = 311
E4 = 330
F4 = 349
G4 = 392
Ab4 = 415
A4 = 440

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

def play_hell_march():
    """Play Hell March from C&C Red Alert"""
    # Tempo - aggressive march
    tempo = 120  # BPM
    beat = 60000 / tempo / 4  # milliseconds per quarter beat
    
    print("Playing Hell March from Red Alert...")
    print("Establishing battlefield control...")
    
    # Main Hell March theme - simplified for buzzer
    # Each tuple is (note_frequency, duration_in_quarter_beats)
    
    # The iconic opening riff
    for _ in range(2):  # Repeat twice
        melody = [
            # Main riff pattern
            (E3, 1), (E3, 1), (E3, 1), (E3, 1),
            (G3, 1), (E3, 1), (D3, 1), (E3, 1),
            (E3, 1), (E3, 1), (E3, 1), (E3, 1),
            (Ab3, 1), (G3, 1), (F3, 1), (E3, 1),
        ]
        
        for note, duration in melody:
            play_note(note, beat * duration)
    
    # Main theme section
    main_theme = [
        # Rising tension
        (E3, 4), (G3, 4), 
        (A3, 4), (B3, 4),
        (C4, 2), (B3, 2), (A3, 2), (G3, 2),
        (E3, 8),
        (0, 2),  # Rest
        
        # Aggressive march rhythm
        (E4, 1), (E4, 1), (E4, 2),
        (E4, 1), (E4, 1), (E4, 2),
        (G4, 2), (E4, 2), (D4, 2), (C4, 2),
        (B3, 8),
        (0, 4),  # Rest
        
        # Final power section
        (C4, 2), (C4, 2), (D4, 2), (E4, 2),
        (E4, 4), (D4, 4),
        (C4, 2), (B3, 2), (A3, 2), (G3, 2),
        (E3, 8),
    ]
    
    for note, duration in main_theme:
        play_note(note, beat * duration)
    
    # Ending - dramatic finish
    ending = [
        (E3, 1), (E3, 1), (E3, 1), (E3, 1),
        (E3, 2), (0, 2), (E3, 2), (0, 2),
        (E3, 8),
    ]
    
    for note, duration in ending:
        play_note(note, beat * duration)
    
    print("Mission accomplished, Commander!")

# Play Hell March
play_hell_march()

# Clean up
buzzer.deinit()