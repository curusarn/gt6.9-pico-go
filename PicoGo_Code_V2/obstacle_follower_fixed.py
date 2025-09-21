from machine import Pin, PWM
import time
from Motor import PicoGo
from ST7789 import ST7789
from ws2812 import NeoPixel

# Initialize logging
log_file = open("obstacle_follower.log", "w")
log_start_time = time.ticks_ms()

def log(message):
    """Write timestamped message to log file"""
    timestamp = time.ticks_diff(time.ticks_ms(), log_start_time) / 1000.0
    log_entry = f"[{timestamp:8.3f}] {message}\n"
    log_file.write(log_entry)
    log_file.flush()  # Ensure it's written immediately

# Initialize hardware
log("Initializing hardware")
M = PicoGo()
lcd = ST7789()
strip = NeoPixel()
buzzer_pwm = PWM(Pin(4))

# Ultrasonic sensor pins
Echo = Pin(15, Pin.IN)
Trig = Pin(14, Pin.OUT)

# IR sensors for close obstacle detection
DSR = Pin(2, Pin.IN)
DSL = Pin(3, Pin.IN)

# Constants
MIN_DISTANCE = 15  # cm
MAX_DISTANCE = 80  # cm
FOLLOW_DISTANCE = 30  # Target following distance in cm
BASE_SPEED = 17  # Base motor speed (reduced by 3x from 50)

# Imperial March setup
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

imperial_march = [
    # First phrase
    (A4, 4), (A4, 4), (A4, 4), 
    (F4, 3), (C5, 1),
    (A4, 4), (F4, 3), (C5, 1), (A4, 8),
    (0, 4),  # Rest
    
    # Second phrase
    (E5, 4), (E5, 4), (E5, 4),
    (F5, 3), (C5, 1),
    (Ab4, 4), (F4, 3), (C5, 1), (A4, 8),
]

# Music variables
music_index = 0
note_duration = 150  # milliseconds per beat
current_note_start = 0
is_playing_note = False

def get_distance():
    """Measure distance using ultrasonic sensor with averaging"""
    distances = []
    
    for _ in range(3):  # Take 3 readings
        # Send trigger pulse
        Trig.value(0)
        Trig.value(1)
        time.sleep_us(10)
        Trig.value(0)
        
        timeout_start = time.ticks_us()
        timeout = 30000  # 30ms timeout
        
        # Wait for echo to go high
        while Echo.value() == 0:
            if time.ticks_diff(time.ticks_us(), timeout_start) > timeout:
                distances.append(999)
                break
        else:
            time1 = time.ticks_us()
            
            # Wait for echo to go low
            while Echo.value() == 1:
                if time.ticks_diff(time.ticks_us(), time1) > timeout:
                    distances.append(999)
                    break
            else:
                time2 = time.ticks_us()
                during = time2 - time1
                distance = during * 0.034 / 2
                distances.append(distance)
        
        time.sleep_ms(30)  # Short delay between readings
    
    # Simple average of all readings
    if len(distances) > 0:
        avg_distance = sum(distances) / len(distances)
        return avg_distance
    else:
        return 999

def scan_for_obstacle():
    """Scan by rotating slowly to find obstacle in range"""
    scan_speed = 13  # Reduced to 16 * 0.8 ≈ 13
    consecutive_detections = 0  # Need multiple detections to confirm
    log(f"Starting scan sequence with speed {scan_speed}")
    
    # Update LCD
    lcd.fill_rect(0, 25, 240, 110, lcd.BLACK)
    lcd.text("SCANNING...", 65, 40, lcd.YELLOW)
    lcd.text("Looking for target", 40, 60, lcd.WHITE)
    
    # Quick scan left and right first
    lcd.text("Quick scan...", 60, 80, lcd.BLUE)
    lcd.show()
    
    # Look slightly right
    log("Quick scan right")
    M.right(scan_speed)
    for _ in range(3):  # 3 quick measurements
        distance = get_distance()
        if MIN_DISTANCE <= distance <= MAX_DISTANCE:
            log(f"Target found in quick right scan at {distance:.1f}cm")
            M.stop()
            return True
        time.sleep(0.2)
    
    # Look slightly left (past center)
    log("Quick scan left")
    M.left(scan_speed)
    for _ in range(6):  # 6 measurements to go past center
        distance = get_distance()
        if MIN_DISTANCE <= distance <= MAX_DISTANCE:
            log(f"Target found in quick left scan at {distance:.1f}cm")
            M.stop()
            return True
        time.sleep(0.2)
    
    # Return to center
    log("Returning to center")
    M.right(scan_speed)
    time.sleep(0.6)
    M.stop()
    time.sleep(0.2)
    
    # Full continuous scan with decreasing speed
    lcd.fill_rect(0, 80, 240, 20, lcd.BLACK)
    lcd.text("Full 360 scan...", 50, 80, lcd.BLUE)
    lcd.show()
    log("Starting full 360 degree scan")
    
    scan_start_time = time.ticks_ms()
    max_scan_duration = 60000  # 60 seconds max for full rotation
    initial_speed = scan_speed
    min_speed = 8  # Minimum rotation speed
    
    # Start rotating right
    current_speed = initial_speed
    M.right(current_speed)
    last_speed_update = time.ticks_ms()
    
    while time.ticks_diff(time.ticks_ms(), scan_start_time) < max_scan_duration:
        distance = get_distance()
        elapsed_time = time.ticks_diff(time.ticks_ms(), scan_start_time)
        
        # Gradually reduce speed over time
        if time.ticks_diff(time.ticks_ms(), last_speed_update) > 2000:  # Update speed every 2 seconds
            # Calculate new speed based on elapsed time
            speed_reduction = (elapsed_time / max_scan_duration) * (initial_speed - min_speed)
            current_speed = int(initial_speed - speed_reduction)
            current_speed = max(current_speed, min_speed)  # Don't go below minimum
            
            M.right(current_speed)
            log(f"Reduced rotation speed to {current_speed}")
            last_speed_update = time.ticks_ms()
        
        # Update LCD with distance and current speed
        lcd.fill_rect(50, 100, 140, 40, lcd.BLACK)
        lcd.text(f"Dist: {distance:.1f}cm", 50, 100, lcd.WHITE)
        lcd.text(f"Speed: {current_speed}", 50, 115, lcd.YELLOW)
        lcd.show()
        
        if MIN_DISTANCE <= distance <= MAX_DISTANCE:
            consecutive_detections += 1
            log(f"360 scan: Valid target at {distance:.1f}cm, consecutive: {consecutive_detections}")
            if consecutive_detections >= 3:  # Need 3 consecutive readings
                M.stop()
                log(f"Target confirmed during 360 scan at {distance:.1f}cm")
                time.sleep(0.2)  # Brief pause to stabilize
                return True
        else:
            if consecutive_detections > 0:
                log(f"Lost target during 360 scan, distance: {distance:.1f}cm")
            consecutive_detections = 0
    
    # Scan timeout - no target found
    lcd.fill_rect(40, 60, 160, 60, lcd.BLACK)
    lcd.text("No target found", 50, 70, lcd.RED)
    lcd.text("360 scan complete", 45, 90, lcd.WHITE)
    lcd.show()
    log("360 degree scan complete - no target found")
    
    return False

def update_lcd(state, distance, speed_left, speed_right):
    """Update LCD with current state"""
    lcd.fill_rect(0, 25, 240, 110, lcd.BLACK)
    
    # State display
    state_color = lcd.GREEN if state == "FOLLOWING" else lcd.YELLOW if state == "SCANNING" else lcd.RED
    lcd.text(f"State: {state}", 10, 25, state_color)
    
    # Distance display
    if distance < 999:
        lcd.text(f"Distance: {distance:.1f} cm", 10, 45, lcd.WHITE)
        
        # Visual distance bar
        bar_length = int((distance / 100) * 200)
        if MIN_DISTANCE <= distance <= MAX_DISTANCE:
            bar_color = lcd.GREEN
        else:
            bar_color = lcd.RED
        lcd.fill_rect(20, 65, bar_length, 10, bar_color)
        lcd.rect(20, 65, 200, 10, lcd.WHITE)
    else:
        lcd.text("Distance: No Target", 10, 45, lcd.RED)
    
    # Speed display
    lcd.text(f"Motors: L:{speed_left} R:{speed_right}", 10, 85, lcd.BLUE)
    
    # Target range indicator
    lcd.text(f"Target: {MIN_DISTANCE}-{MAX_DISTANCE}cm", 10, 105, lcd.WHITE)
    lcd.show()

def play_imperial_march():
    """Handle Imperial March playback"""
    # COMMENTED OUT TO AVOID TIMING ISSUES
    pass
    # global music_index, current_note_start, is_playing_note
    # 
    # current_time = time.ticks_ms()
    # 
    # if not is_playing_note or time.ticks_diff(current_time, current_note_start) > imperial_march[music_index][1] * note_duration:
    #     buzzer_pwm.duty_u16(0)
    #     
    #     if is_playing_note:
    #         music_index = (music_index + 1) % len(imperial_march)
    #     
    #     freq, beats = imperial_march[music_index]
    #     if freq > 0:
    #         buzzer_pwm.freq(freq)
    #         buzzer_pwm.duty_u16(16384)  # 25% volume
    #     current_note_start = current_time
    #     is_playing_note = True

def stop_music():
    """Stop music playback"""
    # COMMENTED OUT TO AVOID TIMING ISSUES
    pass
    # global is_playing_note
    # buzzer_pwm.duty_u16(0)
    # is_playing_note = False

# Initialize LCD
lcd.fill(lcd.BLACK)
lcd.text("Obstacle Follower", 45, 10, lcd.WHITE)
lcd.show()

# Set initial LED pattern
for i in range(4):
    strip.pixels_set(i, strip.BLUE)
strip.pixels_show()

# Main state machine
state = "SCANNING"
last_distance = 0
stopped_time = 0
last_scan_time = 0
scan_cooldown = 2000  # 2 seconds between scan attempts
follow_log_counter = 0  # Log following details periodically

log("Starting main loop")
log(f"Target range: {MIN_DISTANCE}-{MAX_DISTANCE}cm, Follow distance: {FOLLOW_DISTANCE}cm")

# Force initial scan to test rotation
log("Forcing initial scan to test rotation")
scan_for_obstacle()
time.sleep(2)

try:
    while True:
        distance = get_distance()
        dr_status = DSR.value()
        dl_status = DSL.value()
        
        if state == "SCANNING":
            stop_music()
            M.stop()
            
            if MIN_DISTANCE <= distance <= MAX_DISTANCE:
                log(f"Immediate target found at {distance:.1f}cm, switching to FOLLOWING")
                state = "FOLLOWING"
                last_scan_time = time.ticks_ms()
            else:
                # Scan for obstacle with cooldown
                current_time = time.ticks_ms()
                if time.ticks_diff(current_time, last_scan_time) > scan_cooldown:
                    if scan_for_obstacle():
                        log("Scan successful, switching to FOLLOWING")
                        state = "FOLLOWING"
                    last_scan_time = current_time
                else:
                    # Show waiting message
                    wait_time = (scan_cooldown - time.ticks_diff(current_time, last_scan_time)) / 1000
                    lcd.fill_rect(0, 60, 240, 20, lcd.BLACK)
                    lcd.text(f"Next scan in {wait_time:.1f}s", 40, 60, lcd.WHITE)
                    lcd.show()
            
            update_lcd(state, distance, 0, 0)
        
        elif state == "FOLLOWING":
            # Check if we're too close (ultrasonic < MIN_DISTANCE)
            # Disabled IR sensors as they're too sensitive
            if distance < MIN_DISTANCE:
                log(f"Too close! Distance: {distance:.1f}cm, IR_L: {dl_status}, IR_R: {dr_status}, switching to STOPPED")
                state = "STOPPED"
                stopped_time = time.ticks_ms()
                M.stop()
                stop_music()
                
                # Flash red LEDs
                for i in range(4):
                    strip.pixels_set(i, strip.RED)
                strip.pixels_show()
            
            # Check if we lost the target
            elif distance > MAX_DISTANCE:
                log(f"Lost target, distance {distance:.1f}cm > {MAX_DISTANCE}cm, switching to SCANNING")
                state = "SCANNING"
            
            # Follow the obstacle
            else:
                play_imperial_march()
                
                # Calculate motor speeds based on distance
                error = distance - FOLLOW_DISTANCE
                
                # Add dead zone to prevent oscillation
                if abs(error) < 3:  # Within 3cm is good enough
                    speed = BASE_SPEED
                    led_color = strip.GREEN
                elif error > 0:  # Too far - speed up
                    # Gentler acceleration
                    speed = BASE_SPEED + int(error * 0.3)
                    speed = min(speed, 27)  # Cap reduced by 3x from 80
                    led_color = strip.CYAN
                else:  # Too close - slow down or reverse
                    # Gentler deceleration
                    speed = BASE_SPEED + int(error * 0.4)
                    speed = max(speed, -15)  # Gentle reverse max
                    led_color = strip.YELLOW
                
                # Apply speeds using high-level methods
                if speed > 0:
                    log(f"Calling M.forward({speed})")
                    M.forward(speed)
                    # Quick beep to confirm forward command
                    buzzer_pwm.freq(1000)
                    buzzer_pwm.duty_u16(32768)
                    time.sleep(0.05)
                    buzzer_pwm.duty_u16(0)
                elif speed < 0:
                    log(f"Calling M.backward({abs(speed)})")
                    M.backward(abs(speed))
                    # Lower beep for backward
                    buzzer_pwm.freq(500)
                    buzzer_pwm.duty_u16(32768)
                    time.sleep(0.05)
                    buzzer_pwm.duty_u16(0)
                else:
                    log("Calling M.stop()")
                    M.stop()
                
                # Set LED color based on action
                for i in range(4):
                    strip.pixels_set(i, led_color)
                strip.pixels_show()
                
                # Periodic logging during following
                follow_log_counter += 1
                if follow_log_counter >= 20:  # Log every ~1 second
                    log(f"Following: distance={distance:.1f}cm, speed={speed}, error={error:.1f}")
                    follow_log_counter = 0
                
                update_lcd(state, distance, speed, speed)
        
        elif state == "STOPPED":
            stop_music()
            update_lcd("STOPPED", distance, 0, 0)
            
            # Wait 1 second then start scanning
            if time.ticks_diff(time.ticks_ms(), stopped_time) > 1000:
                state = "SCANNING"
                
                # Reset LEDs to blue
                for i in range(4):
                    strip.pixels_set(i, strip.BLUE)
                strip.pixels_show()
        
        time.sleep(0.05)  # 50ms loop delay

except Exception as e:
    log(f"ERROR: {e}")
    log("Closing log file")
    log_file.close()
    raise

except KeyboardInterrupt:
    log("Program interrupted by user")
    log("Closing log file")
    log_file.close()
    M.stop()
    buzzer_pwm.deinit()