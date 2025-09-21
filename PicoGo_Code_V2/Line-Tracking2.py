from machine import Pin, PWM
from TRSensor import TRSensor
from Motor import PicoGo
from ws2812 import NeoPixel
from ST7789 import ST7789
import time


M = PicoGo()
# Initialize buzzer with PWM for Imperial March
buzzer_pwm = PWM(Pin(4))
DSR = Pin(2, Pin.IN)
DSL = Pin(3, Pin.IN)

# Initialize LCD
lcd = ST7789()
lcd.fill(lcd.BLACK)
lcd.text("Line Tracking", 60, 10, lcd.WHITE)
lcd.text("Initializing...", 55, 30, lcd.YELLOW)
lcd.show()

# Imperial March notes and melody
A4 = 440
F4 = 349
C5 = 523
E5 = 659
F5 = 698
Ab4 = 415
Eb5 = 622
D5 = 587
B4 = 494
Bb4 = 466
G5 = 784
Ab5 = 831
A5 = 880
G4 = 392

# Imperial March melody - full version for background play
# Each tuple is (note_frequency, duration_in_beats)
# 0 frequency means rest/silence
imperial_march = [
    # First phrase - the iconic opening
    (A4, 4), (A4, 4), (A4, 4), 
    (F4, 3), (C5, 1),
    (A4, 4), (F4, 3), (C5, 1), (A4, 8),
    (0, 4),  # Rest
    
    # Second phrase - rising tension
    (E5, 4), (E5, 4), (E5, 4),
    (F5, 3), (C5, 1),
    (Ab4, 4), (F4, 3), (C5, 1), (A4, 8),
    (0, 4),  # Rest
    
    # Third phrase - the dramatic high section
    (A5, 4), (A4, 3), (A4, 1),
    (A5, 4), (Ab5, 3), (G5, 1),
    (F5, 1), (E5, 1), (F5, 2), (0, 2), (Bb4, 2),
    (Eb5, 4), (D5, 3), (C5, 1),
    
    # Fourth phrase - melodic bridge
    (B4, 1), (C5, 1), (D5, 2), (0, 2), (F4, 2),
    (G5, 4), (F5, 3), (A4, 1),
    (C5, 4), (A4, 3), (C5, 1), (E5, 8),
    (0, 4),  # Rest
    
    # Final phrase - return to main theme
    (A4, 4), (A4, 4), (A4, 4),
    (F4, 3), (C5, 1),
    (A4, 4), (F4, 3), (C5, 1), (A4, 8),
    (0, 8),  # Long rest before loop
]

# Music playback variables
music_index = 0
music_timer = 0
note_duration = 150  # milliseconds per beat
current_note_start = 0
is_playing_note = False

strip = NeoPixel()
strip.pixels_set(0, strip.RED)
strip.pixels_set(1, strip.GREEN)
strip.pixels_set(2, strip.BLUE)
strip.pixels_set(3, strip.YELLOW)
strip.pixels_show()  
time.sleep(2)

TRS=TRSensor()

# Show calibration status on LCD
lcd.fill(lcd.BLACK)
lcd.text("Calibrating...", 55, 50, lcd.YELLOW)
lcd.text("Please wait", 65, 70, lcd.WHITE)
lcd.show()

for i in range(100):
    if(i<25 or i>= 75):
        M.setMotor(30,-30)
    else:
        M.setMotor(-30,30)
    TRS.calibrate()
print("\ncalibrate done\r\n")
print(TRS.calibratedMin)
print(TRS.calibratedMax)
print("\ncalibrate done\r\n")
maximum = 20  # Reduced to 1/5th of original speed (100 -> 20)
integral = 0
last_proportional = 0
j=0
lcd_update_counter = 0

# Clear LCD and prepare for tracking
lcd.fill(lcd.BLACK)
lcd.text("Line Tracking", 60, 5, lcd.WHITE)
lcd.show()

while True:
    position,Sensors = TRS.readLine()
    DR_status = DSR.value()
    DL_status = DSL.value()
    
    # Update LCD every 10 iterations to avoid slowing down
    lcd_update_counter += 1
    if lcd_update_counter >= 10:
        lcd_update_counter = 0
        lcd.fill_rect(0, 25, 240, 110, lcd.BLACK)
        
        # Display position
        lcd.text(f"Position: {position}", 10, 25, lcd.GREEN)
        
        # Display sensor values
        lcd.text("Sensors:", 10, 45, lcd.YELLOW)
        sensor_str = f"{Sensors[0]:3d} {Sensors[1]:3d} {Sensors[2]:3d} {Sensors[3]:3d} {Sensors[4]:3d}"
        lcd.text(sensor_str, 10, 60, lcd.WHITE)
        
        # Display status
        if (Sensors[0] + Sensors[1] + Sensors[2]+ Sensors[3]+ Sensors[4]) > 4000:
            lcd.text("Status: END LINE", 10, 80, lcd.RED)
        elif (DL_status == 0) or (DR_status == 0):
            lcd.text("Status: OBSTACLE", 10, 80, lcd.RED)
            lcd.text(f"L:{DL_status} R:{DR_status}", 10, 95, lcd.YELLOW)
        else:
            lcd.text("Status: TRACKING", 10, 80, lcd.GREEN)
            if position < 1500:
                lcd.text("Turning LEFT", 10, 95, lcd.GBLUE)
            elif position > 2500:
                lcd.text("Turning RIGHT", 10, 95, lcd.GBLUE)
            else:
                lcd.text("Going STRAIGHT", 10, 95, lcd.GBLUE)
        
        # Display speed
        lcd.text(f"Speed: {maximum}", 10, 115, lcd.WHITE)
        lcd.show()
    
    # Handle Imperial March playback
    current_time = time.ticks_ms()
    
    # Check if it's time to play next note
    if not is_playing_note or time.ticks_diff(current_time, current_note_start) > imperial_march[music_index][1] * note_duration:
        # Stop current note
        buzzer_pwm.duty_u16(0)
        
        # Move to next note
        if is_playing_note:
            music_index = (music_index + 1) % len(imperial_march)
        
        # Start new note if not in alarm state
        if not ((Sensors[0] + Sensors[1] + Sensors[2]+ Sensors[3]+ Sensors[4]) > 4000) and not ((DL_status == 0) or (DR_status == 0)):
            freq, beats = imperial_march[music_index]
            if freq > 0:  # Not a rest
                buzzer_pwm.freq(freq)
                buzzer_pwm.duty_u16(16384)  # 25% volume for background music
            else:
                buzzer_pwm.duty_u16(0)  # Silence for rests
            current_note_start = current_time
            is_playing_note = True
    
    if((Sensors[0] + Sensors[1] + Sensors[2]+ Sensors[3]+ Sensors[4]) > 4000):
        buzzer_pwm.duty_u16(0)  # Stop music
        is_playing_note = False
        M.setMotor(0,0)
    elif((DL_status == 0) or (DR_status == 0)):
        # Alarm beep overrides music
        buzzer_pwm.freq(800)
        buzzer_pwm.duty_u16(32768)  # Full volume for alarm
        is_playing_note = False
        M.setMotor(0,0)
    else:
        # The "proportional" term should be 0 when we are on the line.
        proportional = position - 2000

        # Compute the derivative (change) and integral (sum) of the position.
        derivative = proportional - last_proportional
        #integral += proportional

        # Remember the last position.
        last_proportional = proportional
        
        '''
        // Compute the difference between the two motor power settings,
        // m1 - m2.  If this is a positive number the robot will turn
        // to the right.  If it is a negative number, the robot will
        // turn to the left, and the magnitude of the number determines
        // the sharpness of the turn.  You can adjust the constants by which
        // the proportional, integral, and derivative terms are multiplied to
        // improve performance.
        '''
        power_difference = proportional/30  + derivative*2;  

        if (power_difference > maximum):
            power_difference = maximum
        if (power_difference < - maximum):
            power_difference = - maximum

        if (power_difference < 0):
            M.setMotor(maximum + power_difference, maximum)
        else:
            M.setMotor(maximum, maximum - power_difference)

    for i in range(strip.num):
        strip.pixels_set(i, strip.wheel(((i * 256 // strip.num) + j) & 255))
    strip.pixels_show()
    j += 1
    if(j > 256): 
        j = 0
