from machine import Pin, PWM
import time
from Motor import PicoGo
from ST7789 import ST7789
from ws2812 import NeoPixel

# Initialize logging
log_file = open("curved_follower.log", "w")
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

# IR Sensor Filtering Class
class IRFilter:
    def __init__(self):
        self.left_history = [1, 1, 1, 1, 1]  # 5-sample history
        self.right_history = [1, 1, 1, 1, 1]
        self.last_update = time.ticks_ms()
    
    def update(self):
        """Update IR sensor readings with rate limiting"""
        # Only update every 20ms to avoid over-sampling
        if time.ticks_diff(time.ticks_ms(), self.last_update) < 20:
            return
            
        self.left_history.append(DSL.value())
        self.right_history.append(DSR.value())
        self.left_history.pop(0)
        self.right_history.pop(0)
        self.last_update = time.ticks_ms()
    
    def get_filtered(self):
        """Return filtered IR detection status"""
        # Need 3/5 readings to confirm detection
        left_count = sum(1 for x in self.left_history if x == 0)
        right_count = sum(1 for x in self.right_history if x == 0)
        
        left_detected = left_count >= 3
        right_detected = right_count >= 3
        
        return left_detected, right_detected
    
    def get_confidence(self):
        """Return detection confidence 0-100%"""
        left_conf = (5 - sum(self.left_history)) * 20
        right_conf = (5 - sum(self.right_history)) * 20
        return left_conf, right_conf

# Anti-Distraction Logic
class FollowingContext:
    def __init__(self):
        self.last_good_distance = None
        self.last_good_time = 0
        self.following_side = None  # 'left', 'right', or None
        self.confidence_threshold = 50
    
    def update_good_lock(self, distance):
        """Update last good lock when we have solid ultrasonic reading"""
        if MIN_DISTANCE <= distance <= MAX_DISTANCE:
            self.last_good_distance = distance
            self.last_good_time = time.ticks_ms()
    
    def should_ignore_ir(self, current_distance, ir_side, ir_confidence):
        """
        Ignore IR detection if:
        1. We have good ultrasonic lock AND
        2. IR detection is sudden (not gradual) AND
        3. Object distance hasn't changed much
        """
        if self.last_good_distance is None:
            return False
            
        time_since_good = time.ticks_diff(time.ticks_ms(), self.last_good_time)
        
        # If we had good lock recently
        if time_since_good < 1000:  # Within 1 second
            distance_change = abs(current_distance - self.last_good_distance)
            
            # If distance stable but sudden IR, might be false trigger
            if distance_change < 5 and ir_confidence < 60:  # Less than 5cm change
                log(f"Ignoring sudden {ir_side} IR detection - distance stable")
                return True
        
        return False

def calculate_following_movement(distance, left_ir, right_ir, left_conf, right_conf, context):
    """
    Calculate differential motor speeds based on sensor inputs
    Returns (left_speed, right_speed, state_name)
    """
    
    # Safety check - too close
    if distance < MIN_DISTANCE:
        return (0, 0, "TOO_CLOSE")
    
    # Lost completely
    if distance > MAX_DISTANCE and not left_ir and not right_ir:
        return (0, 0, "LOST")
    
    # Calculate base speed from distance
    if distance < FOLLOW_DISTANCE:
        base_speed = BASE_SPEED - int((FOLLOW_DISTANCE - distance) * 0.5)
    else:
        base_speed = BASE_SPEED + int((distance - FOLLOW_DISTANCE) * 0.3)
    
    base_speed = max(10, min(base_speed, 27))  # Clamp speed
    
    # Case 1: Straight following (ultrasonic only)
    if distance <= MAX_DISTANCE and not left_ir and not right_ir:
        context.update_good_lock(distance)
        return (base_speed, base_speed, "STRAIGHT")
    
    # Case 2: Object drifting left (left IR + ultrasonic)
    if distance <= MAX_DISTANCE and left_ir and not right_ir:
        # Check if we should ignore this IR detection
        if context.should_ignore_ir(distance, "left", left_conf):
            return (base_speed, base_speed, "STRAIGHT")
        
        # Gentle curve left - reduce left wheel speed
        left_speed = base_speed - int(5 + left_conf * 0.1)  # 5-15 reduction
        right_speed = base_speed
        context.following_side = 'left'
        return (left_speed, right_speed, "DRIFT_LEFT")
    
    # Case 3: Object drifting right (right IR + ultrasonic)
    if distance <= MAX_DISTANCE and right_ir and not left_ir:
        # Check if we should ignore this IR detection
        if context.should_ignore_ir(distance, "right", right_conf):
            return (base_speed, base_speed, "STRAIGHT")
        
        # Gentle curve right - reduce right wheel speed
        left_speed = base_speed
        right_speed = base_speed - int(5 + right_conf * 0.1)  # 5-15 reduction
        context.following_side = 'right'
        return (left_speed, right_speed, "DRIFT_RIGHT")
    
    # Case 4: Wide object (both IR + ultrasonic)
    if distance <= MAX_DISTANCE and left_ir and right_ir:
        # Object is wide or very close - follow straight but slower
        slow_speed = int(base_speed * 0.7)
        return (slow_speed, slow_speed, "WIDE_OBJECT")
    
    # Case 5: Lost ultrasonic but have left IR
    if distance > MAX_DISTANCE and left_ir and not right_ir:
        # Turn left to reacquire - stronger turn
        if left_conf > 80:  # High confidence
            return (5, 20, "REACQUIRE_LEFT_STRONG")
        else:
            return (10, 20, "REACQUIRE_LEFT_GENTLE")
    
    # Case 6: Lost ultrasonic but have right IR  
    if distance > MAX_DISTANCE and right_ir and not left_ir:
        # Turn right to reacquire - stronger turn
        if right_conf > 80:  # High confidence
            return (20, 5, "REACQUIRE_RIGHT_STRONG")
        else:
            return (20, 10, "REACQUIRE_RIGHT_GENTLE")
    
    # Default - shouldn't reach here
    return (0, 0, "UNKNOWN")

def apply_differential_speeds(left_speed, right_speed):
    """Apply differential motor speeds for curved motion"""
    if left_speed == 0 and right_speed == 0:
        M.stop()
    elif left_speed == right_speed:
        # Straight movement
        if left_speed > 0:
            M.forward(left_speed)
        else:
            M.backward(abs(left_speed))
    else:
        # Differential movement - use setMotor for different speeds
        M.setMotor(left_speed, right_speed)

def update_following_lcd(state, distance, left_ir, right_ir, left_conf, right_conf, movement_state):
    """Enhanced LCD display with IR sensor information"""
    lcd.fill(lcd.BLACK)
    
    # Title
    lcd.text("Curved Following", 50, 5, lcd.WHITE)
    
    # Distance bar with direction indicator
    bar_width = min(int((distance / 100) * 200), 200)
    lcd.rect(20, 25, 200, 15, lcd.WHITE)
    if distance <= MAX_DISTANCE:
        bar_color = lcd.GREEN if MIN_DISTANCE <= distance <= MAX_DISTANCE else lcd.YELLOW
        lcd.fill_rect(20, 25, bar_width, 15, bar_color)
    
    # IR indicators
    if left_ir:
        lcd.fill_rect(5, 25, 10, 15, lcd.YELLOW)  # Left indicator
        lcd.text(f"{left_conf}%", 5, 42, lcd.YELLOW)
    if right_ir:
        lcd.fill_rect(225, 25, 10, 15, lcd.YELLOW)  # Right indicator
        lcd.text(f"{right_conf}%", 190, 42, lcd.YELLOW)
    
    # Status text
    lcd.text(f"Dist: {distance:.1f}cm", 10, 60, lcd.WHITE)
    lcd.text(f"State: {movement_state}", 10, 75, lcd.GREEN)
    
    # IR confidence
    lcd.text(f"IR L:{left_conf}% R:{right_conf}%", 10, 90, lcd.BLUE)
    
    # Movement indicator
    if "LEFT" in movement_state:
        lcd.text("<--", 10, 105, lcd.YELLOW)
    elif "RIGHT" in movement_state:
        lcd.text("-->", 190, 105, lcd.YELLOW)
    elif "STRAIGHT" in movement_state:
        lcd.text("^^^", 105, 105, lcd.GREEN)
    elif "WIDE" in movement_state:
        lcd.text("<->", 105, 105, lcd.BLUE)
    
    lcd.show()

def log_following_state(distance, left_ir, right_ir, left_conf, right_conf, 
                       movement_state, left_speed, right_speed):
    """Detailed logging for debugging"""
    log(f"FOLLOW: dist={distance:.1f}cm, IR_L={left_ir}({left_conf}%), " +
        f"IR_R={right_ir}({right_conf}%), state={movement_state}, " +
        f"motors=L{left_speed}/R{right_speed}")

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

def scan_for_obstacle(ir_filter):
    """Enhanced scanning with IR hints"""
    scan_speed = 13  # Reduced speed
    consecutive_detections = 0
    log(f"Starting scan sequence with speed {scan_speed}")
    
    # Update LCD
    lcd.fill_rect(0, 25, 240, 110, lcd.BLACK)
    lcd.text("SCANNING...", 65, 40, lcd.YELLOW)
    lcd.text("Looking for target", 40, 60, lcd.WHITE)
    
    # Get current IR status
    ir_filter.update()
    left_ir, right_ir = ir_filter.get_filtered()
    left_conf, right_conf = ir_filter.get_confidence()
    
    # If we have IR hint, scan in that direction first
    if left_ir and left_conf > 60:
        log(f"IR hint: target likely on left (confidence: {left_conf}%)")
        lcd.text("IR hint: left", 60, 80, lcd.YELLOW)
        lcd.show()
        M.left(scan_speed)
        scan_direction = "left"
    elif right_ir and right_conf > 60:
        log(f"IR hint: target likely on right (confidence: {right_conf}%)")
        lcd.text("IR hint: right", 60, 80, lcd.YELLOW)
        lcd.show()
        M.right(scan_speed)
        scan_direction = "right"
    else:
        # No IR hint - do normal scan
        lcd.text("Quick scan...", 60, 80, lcd.BLUE)
        lcd.show()
        M.right(scan_speed)
        scan_direction = "right"
    
    # Scan with IR hint priority
    scan_start_time = time.ticks_ms()
    max_scan_duration = 60000  # 60 seconds max
    
    while time.ticks_diff(time.ticks_ms(), scan_start_time) < max_scan_duration:
        distance = get_distance()
        
        # Update IR readings
        ir_filter.update()
        left_ir, right_ir = ir_filter.get_filtered()
        left_conf, right_conf = ir_filter.get_confidence()
        
        # Update LCD
        lcd.fill_rect(50, 100, 140, 40, lcd.BLACK)
        lcd.text(f"Dist: {distance:.1f}cm", 50, 100, lcd.WHITE)
        if left_ir or right_ir:
            lcd.text(f"IR: L{left_conf}% R{right_conf}%", 50, 115, lcd.YELLOW)
        lcd.show()
        
        if MIN_DISTANCE <= distance <= MAX_DISTANCE:
            consecutive_detections += 1
            log(f"Scan: Valid target at {distance:.1f}cm, consecutive: {consecutive_detections}")
            if consecutive_detections >= 3:
                M.stop()
                log(f"Target confirmed during scan at {distance:.1f}cm")
                time.sleep(0.2)
                return True
        else:
            consecutive_detections = 0
        
        # Switch direction if we've been scanning too long in one direction
        if time.ticks_diff(time.ticks_ms(), scan_start_time) > 10000:  # 10 seconds
            if scan_direction == "right":
                M.left(scan_speed)
                scan_direction = "left"
            else:
                M.right(scan_speed)
                scan_direction = "right"
    
    M.stop()
    log("Scan timeout - no target found")
    return False

# Initialize LCD
lcd.fill(lcd.BLACK)
lcd.text("Curved Follower", 50, 10, lcd.WHITE)
lcd.show()

# Set initial LED pattern
for i in range(4):
    strip.pixels_set(i, strip.BLUE)
strip.pixels_show()

# Initialize components
ir_filter = IRFilter()
context = FollowingContext()

# Main state machine
state = "SCANNING"
last_distance = 0
stopped_time = 0
last_scan_time = 0
scan_cooldown = 2000  # 2 seconds between scan attempts
follow_log_counter = 0
last_detailed_log = 0

log("Starting curved follower main loop")
log(f"Target range: {MIN_DISTANCE}-{MAX_DISTANCE}cm, Follow distance: {FOLLOW_DISTANCE}cm")
log("IR sensors enabled with filtering for curved path following")

try:
    while True:
        # Update IR filter
        ir_filter.update()
        
        # Get sensor readings
        distance = get_distance()
        left_ir, right_ir = ir_filter.get_filtered()
        left_conf, right_conf = ir_filter.get_confidence()
        
        if state == "SCANNING":
            M.stop()
            
            if MIN_DISTANCE <= distance <= MAX_DISTANCE:
                log(f"Immediate target found at {distance:.1f}cm, switching to FOLLOWING")
                state = "FOLLOWING"
                context.update_good_lock(distance)
                last_scan_time = time.ticks_ms()
            else:
                # Scan for obstacle with cooldown
                current_time = time.ticks_ms()
                if time.ticks_diff(current_time, last_scan_time) > scan_cooldown:
                    if scan_for_obstacle(ir_filter):
                        log("Scan successful, switching to FOLLOWING")
                        state = "FOLLOWING"
                        context.update_good_lock(distance)
                    last_scan_time = current_time
                else:
                    # Show waiting message
                    wait_time = (scan_cooldown - time.ticks_diff(current_time, last_scan_time)) / 1000
                    lcd.fill_rect(0, 60, 240, 20, lcd.BLACK)
                    lcd.text(f"Next scan in {wait_time:.1f}s", 40, 60, lcd.WHITE)
                    lcd.show()
            
            update_following_lcd(state, distance, left_ir, right_ir, left_conf, right_conf, "SCANNING")
        
        elif state == "FOLLOWING":
            # Calculate movement based on all sensors
            left_speed, right_speed, movement_state = calculate_following_movement(
                distance, left_ir, right_ir, left_conf, right_conf, context
            )
            
            # Handle state transitions
            if movement_state == "TOO_CLOSE":
                log(f"Too close! Distance: {distance:.1f}cm, switching to STOPPED")
                state = "STOPPED"
                stopped_time = time.ticks_ms()
                M.stop()
                
                # Flash red LEDs
                for i in range(4):
                    strip.pixels_set(i, strip.RED)
                strip.pixels_show()
            
            elif movement_state == "LOST":
                log(f"Lost target completely, switching to SCANNING")
                state = "SCANNING"
                context.following_side = None
            
            else:
                # Apply calculated speeds
                apply_differential_speeds(left_speed, right_speed)
                
                # Set LED color based on movement state
                if "STRAIGHT" in movement_state:
                    led_color = strip.GREEN
                elif "DRIFT" in movement_state:
                    led_color = strip.YELLOW
                elif "REACQUIRE" in movement_state:
                    led_color = strip.ORANGE
                elif "WIDE" in movement_state:
                    led_color = strip.BLUE
                else:
                    led_color = strip.BLUE
                
                for i in range(4):
                    strip.pixels_set(i, led_color)
                strip.pixels_show()
                
                # Periodic detailed logging
                current_time = time.ticks_ms()
                if time.ticks_diff(current_time, last_detailed_log) > 500:  # Every 500ms
                    log_following_state(distance, left_ir, right_ir, left_conf, right_conf,
                                      movement_state, left_speed, right_speed)
                    last_detailed_log = current_time
            
            # Update LCD
            update_following_lcd(state, distance, left_ir, right_ir, 
                               left_conf, right_conf, movement_state)
        
        elif state == "STOPPED":
            M.stop()
            update_following_lcd("STOPPED", distance, left_ir, right_ir,
                               left_conf, right_conf, "STOPPED")
            
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
    M.stop()
    raise

except KeyboardInterrupt:
    log("Program interrupted by user")
    log("Closing log file")
    log_file.close()
    M.stop()
    buzzer_pwm.deinit()