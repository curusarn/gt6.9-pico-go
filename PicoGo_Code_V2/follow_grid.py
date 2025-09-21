from machine import Pin, PWM
import time
import random
import math
from Motor import PicoGo
from ST7789 import ST7789
from ws2812 import NeoPixel
from TRSensor import TRSensor

# Initialize hardware
M = PicoGo()
lcd = ST7789()
strip = NeoPixel()
buzzer = PWM(Pin(4))
TRS = TRSensor()

# Constants
LINE_THRESHOLD = 480      # Values below this indicate a line
NO_LINE_THRESHOLD = 500   # Values above this indicate no line
BASE_SPEED = 9           # Even slower forward speed
TURN_SPEED = 12          # Speed for searching turns (back to original)
SEARCH_ANGLE = 10        # Small rotation steps when searching
LINE_LOST_TOLERANCE = 0.15 # Only tolerate missing line for 150ms

# State machine states
STATE_SEARCHING = "SEARCHING"
STATE_FOLLOWING = "FOLLOWING"
STATE_INTERSECTION = "INTERSECTION"
STATE_TURNING = "TURNING"
STATE_MOVING_FORWARD = "MOVING_FORWARD"

# Global variables
current_state = STATE_SEARCHING
last_line_position = 0  # Start assuming line was centered (position 0)
search_direction = 1    # 1 for right, -1 for left
search_count = 0
last_sensor_values = [0, 0, 0, 0, 0]
line_lost_time = 0      # Time when line was first lost
stuck_values = None     # Saved sensor values for stuck detection
stuck_time = 0          # Time when stuck was first detected
stuck_power_boost = 0   # Additional power when stuck
turn_start_time = 0     # Time when turn started
turn_direction = ""     # Current turn direction
turn_duration = 0       # How long to turn
next_state = STATE_SEARCHING  # State after turn completes
search_start_time = 0   # Time when current search motion started
buzzer_on = False       # Track buzzer state
buzzer_start_time = 0   # When buzzer was turned on
last_intersection_choice = ""  # Remember last intersection decision

def beep(frequency, duration):
    """Play a beep sound"""
    buzzer.freq(frequency)
    buzzer.duty_u16(32768)  # 50% duty cycle
    time.sleep(duration)
    buzzer.duty_u16(0)

def detect_line_pattern(sensor_values):
    """
    Analyze sensor values to detect line pattern
    Returns: (num_sensors_on_line, line_position, is_intersection)
    """
    sensors_on_line = []
    
    for i, value in enumerate(sensor_values):
        if value < LINE_THRESHOLD:
            sensors_on_line.append(i)
    
    num_on_line = len(sensors_on_line)
    
    # Check for intersection (all or most sensors see line)
    is_intersection = num_on_line >= 4
    
    # Calculate line position (-2 to +2, with 0 being center)
    if num_on_line == 0:
        line_position = None
    elif num_on_line == 1:
        line_position = sensors_on_line[0] - 2  # Convert to -2 to +2 range
    else:
        # Average position of all sensors on line
        avg_pos = sum(sensors_on_line) / num_on_line
        line_position = avg_pos - 2
    
    return num_on_line, line_position, is_intersection

def update_lcd(state, sensor_values, line_position):
    """Update LCD with current status"""
    lcd.fill(lcd.BLACK)
    
    # Title
    lcd.text("Grid Follower", 65, 5, lcd.WHITE)
    
    # State
    if "HOME" in state:
        state_color = lcd.GREEN
        lcd.text(state, 10, 25, state_color)
    else:
        state_color = lcd.GREEN if state == STATE_FOLLOWING else lcd.YELLOW if state == STATE_SEARCHING else lcd.RED
        lcd.text(f"State: {state}", 10, 25, state_color)
    
    # Sensor values with visual indicators
    lcd.text("Sensors:", 10, 45, lcd.WHITE)
    for i in range(5):
        x = 20 + i * 40
        value = sensor_values[i]
        
        # Show value
        color = lcd.GREEN if value < LINE_THRESHOLD else lcd.WHITE
        lcd.text(str(value), x, 60, color)
        
        # Visual indicator
        if value < LINE_THRESHOLD:
            lcd.fill_rect(x + 5, 80, 20, 10, lcd.GREEN)  # Line detected
        else:
            lcd.rect(x + 5, 80, 20, 10, lcd.WHITE)       # No line
    
    # Line position indicator
    if line_position is not None:
        # Convert position to screen coordinates
        indicator_x = 120 + int(line_position * 30)
        lcd.fill_rect(indicator_x - 5, 100, 10, 10, lcd.YELLOW)
        lcd.text("^", indicator_x - 3, 112, lcd.YELLOW)
    
    # Show last intersection choice if any
    global last_intersection_choice
    if last_intersection_choice:
        lcd.text(f"Last turn: {last_intersection_choice}", 10, 120, lcd.GREEN)
    
    lcd.show()

def start_search_motion():
    """Start a search motion (non-blocking)"""
    global search_direction, search_count, search_start_time
    
    # Very slow forward movement while searching
    creep_speed = 5  # Very slow forward speed
    
    # Alternate between left and right with increasing angles
    if search_count % 2 == 0:
        # Turn in search direction while creeping forward
        if search_direction > 0:
            M.setMotor(creep_speed + TURN_SPEED//2, creep_speed - TURN_SPEED//2)  # Right turn + forward
        else:
            M.setMotor(creep_speed - TURN_SPEED//2, creep_speed + TURN_SPEED//2)  # Left turn + forward
    else:
        # Turn opposite direction while creeping forward
        if search_direction > 0:
            M.setMotor(creep_speed - TURN_SPEED//2, creep_speed + TURN_SPEED//2)  # Left turn + forward
        else:
            M.setMotor(creep_speed + TURN_SPEED//2, creep_speed - TURN_SPEED//2)  # Right turn + forward
    
    # Record start time
    search_start_time = time.ticks_ms()

def update_search():
    """Update search state (called each loop iteration)"""
    global search_count, search_direction, search_start_time
    
    # Calculate how long this motion should last
    motion_duration = 100 + (search_count // 10) * 50  # 100-600ms
    
    # Check if current motion is complete
    if time.ticks_diff(time.ticks_ms(), search_start_time) > motion_duration:
        search_count += 1
        
        # Switch main search direction after every 20 attempts
        if search_count % 20 == 0:
            search_direction *= -1
        
        # Start next motion
        start_search_motion()

def follow_line(line_position):
    """Follow the line using proportional control"""
    global last_line_position
    
    if line_position is None:
        # Lost line, use last known position
        line_position = last_line_position
    else:
        last_line_position = line_position
    
    # Proportional control
    # line_position ranges from -2 (far left) to +2 (far right)
    # If line is on right (+), we need to turn right (reduce right wheel speed)
    # If line is on left (-), we need to turn left (reduce left wheel speed)
    
    error = line_position  # Positive = line is right, negative = line is left
    
    # Gentler correction for smoother following
    if abs(error) > 0.1:  # If line is not centered
        turn_factor = error * 3  # Reduced from 8 to 3 for gentler turns
        
        # Small minimum turn speed
        if error > 0:
            turn_factor = max(turn_factor, 1)  # Small right turn
        elif error < 0:
            turn_factor = min(turn_factor, -1)  # Small left turn
    else:
        turn_factor = 0  # Go straight if centered
    
    # Apply differential steering - FIXED DIRECTION
    # To turn right when line is on right: speed up left wheel, slow right
    # To turn left when line is on left: slow left wheel, speed up right
    if abs(error) > 0.1:  # Not centered - slow down overall
        base = BASE_SPEED - 2  # Reduce speed when turning
        left_speed = base + turn_factor   # Speed up left to turn right
        right_speed = base - turn_factor  # Slow right to turn right
    else:
        # Centered - go at normal speed
        left_speed = BASE_SPEED
        right_speed = BASE_SPEED
    
    # Ensure speeds are within valid range
    left_speed = max(0, min(25, left_speed))
    right_speed = max(0, min(25, right_speed))
    
    # Apply motor speeds
    M.setMotor(int(left_speed), int(right_speed))

def check_if_stuck(sensor_values):
    """Check if robot is stuck (same sensor readings)"""
    global stuck_values, stuck_time, stuck_power_boost
    
    # First check if we're even on a line
    on_line = False
    for value in sensor_values:
        if value < LINE_THRESHOLD:
            on_line = True
            break
    
    # If no line detected, we can't be stuck - reset and return
    if not on_line:
        stuck_values = None
        stuck_time = 0
        stuck_power_boost = 0
        return False
    
    if stuck_values is None:
        # First reading with line detected
        stuck_values = sensor_values.copy()
        stuck_time = time.ticks_ms()
        stuck_power_boost = 0
        return False
    
    # Check if all values are within 30 of saved values
    all_similar = True
    for i in range(5):
        if abs(sensor_values[i] - stuck_values[i]) > 30:
            all_similar = False
            break
    
    if all_similar:
        # Still stuck
        if time.ticks_diff(time.ticks_ms(), stuck_time) > 3000:
            # Stuck for too long (3 seconds)
            return True
    else:
        # Values changed significantly - reset everything
        stuck_values = sensor_values.copy()
        stuck_time = time.ticks_ms()
        stuck_power_boost = 0  # Reset power boost
    
    return False

def handle_stuck():
    """Start moving based on last sensor values with increasing power"""
    global current_state, next_state, turn_start_time, turn_duration, stuck_values, stuck_time
    global last_sensor_values, stuck_power_boost
    
    # Increase power each time we're called
    power = min(stuck_power_boost, 10)  # Start at 0, max boost of 10
    stuck_power_boost += 1
    
    print(f"Stuck detected! Power boost: {power}, Last sensors: {last_sensor_values}")
    lcd.fill_rect(0, 120, 240, 15, lcd.BLACK)
    
    # Count which sensors saw the line (values < LINE_THRESHOLD)
    left_sensors = 0   # Sensors 0, 1
    right_sensors = 0  # Sensors 3, 4
    center_sensor = 0  # Sensor 2
    
    if last_sensor_values[0] < LINE_THRESHOLD: left_sensors += 2
    if last_sensor_values[1] < LINE_THRESHOLD: left_sensors += 1
    if last_sensor_values[2] < LINE_THRESHOLD: center_sensor = 1
    if last_sensor_values[3] < LINE_THRESHOLD: right_sensors += 1
    if last_sensor_values[4] < LINE_THRESHOLD: right_sensors += 2
    
    # Decide action based on sensor pattern
    if left_sensors > right_sensors:
        # More line detected on left - turn left
        lcd.text(f"STUCK! Left +{power}", 45, 120, lcd.YELLOW)
        M.setMotor(BASE_SPEED - 3 + power, BASE_SPEED + 3 + power)  # Stronger left turn with boost
        action = "left"
    elif right_sensors > left_sensors:
        # More line detected on right - turn right
        lcd.text(f"STUCK! Right +{power}", 40, 120, lcd.YELLOW)
        M.setMotor(BASE_SPEED + 3 + power, BASE_SPEED - 3 + power)  # Stronger right turn with boost
        action = "right"
    elif center_sensor > 0 or (left_sensors == 0 and right_sensors == 0):
        # Line was centered or no line at all - go straight
        lcd.text(f"STUCK! Fwd +{power}", 50, 120, lcd.YELLOW)
        M.forward(BASE_SPEED + 2 + power)
        action = "forward"
    else:
        # Equal on both sides - go straight
        lcd.text(f"STUCK! Fwd +{power}", 50, 120, lcd.YELLOW)
        M.forward(BASE_SPEED + 2 + power)
        action = "forward"
    
    lcd.show()
    print(f"Stuck action: {action}, L:{left_sensors} C:{center_sensor} R:{right_sensors}")
    
    # Set up timed state
    current_state = STATE_MOVING_FORWARD
    turn_start_time = time.ticks_ms()
    turn_duration = 400  # 400ms to help get unstuck
    next_state = STATE_SEARCHING  # Return to searching after
    
    # DO NOT reset stuck detection here - wait for sensors to change!

def handle_intersection():
    """Start handling intersection (non-blocking)"""
    global current_state, turn_direction, turn_start_time, turn_duration, next_state
    global buzzer_on, buzzer_start_time, last_intersection_choice
    
    # Stop
    M.stop()
    
    # Visual feedback - flash LEDs
    for i in range(4):
        strip.pixels_set(i, strip.RED)
    strip.pixels_show()
    
    # Audio feedback (quick non-blocking beep)
    buzzer.freq(880)
    buzzer.duty_u16(32768)
    buzzer_on = True
    buzzer_start_time = time.ticks_ms()
    
    # Weighted random choice - favor turns over straight
    choices = ["STRAIGHT", "LEFT", "LEFT", "RIGHT", "RIGHT"]  # 40% straight, 60% turns
    choice = random.choice(choices)
    
    # Display choice on LCD
    lcd.fill_rect(0, 100, 240, 35, lcd.BLACK)
    lcd.text("INTERSECTION!", 60, 100, lcd.RED)
    lcd.text(f"Going: {choice}", 70, 115, lcd.YELLOW)
    lcd.show()
    
    print(f"Intersection! Choosing: {choice}")
    
    # Save choice and set up the turn
    last_intersection_choice = choice
    turn_direction = choice
    turn_start_time = time.ticks_ms()
    
    if choice == "STRAIGHT":
        # Move straight through
        M.forward(BASE_SPEED)
        current_state = STATE_MOVING_FORWARD
        turn_duration = 500  # 500ms forward
        next_state = STATE_FOLLOWING
    elif choice == "LEFT":
        # Rotate 90 degrees left around own axis
        M.setMotor(-TURN_SPEED, TURN_SPEED)  # Left wheel backward, right forward
        current_state = STATE_TURNING
        turn_duration = 765  # 765ms for 90 degree turn
        next_state = STATE_SEARCHING  # Go straight to searching after turn
    else:  # RIGHT
        # Rotate 90 degrees right around own axis
        M.setMotor(TURN_SPEED, -TURN_SPEED)  # Left wheel forward, right backward
        current_state = STATE_TURNING
        turn_duration = 765  # 765ms for 90 degree turn
        next_state = STATE_SEARCHING  # Go straight to searching after turn

# Initialize LCD
lcd.fill(lcd.BLACK)
lcd.text("Grid Follower", 65, 10, lcd.WHITE)
lcd.text("Initializing...", 55, 60, lcd.YELLOW)
lcd.show()

# Initialize LEDs
for i in range(4):
    strip.pixels_set(i, strip.BLUE)
strip.pixels_show()

# Main loop
print("Grid Follower starting...")
time.sleep(1)

try:
    while True:
        # Read sensors
        sensor_values = TRS.AnalogRead()
        
        # Check if robot is in "Home sweet home" (all sensors < 160 and at least one > 100)
        all_below_160 = all(value < 160 for value in sensor_values)
        at_least_one_above_100 = any(value > 100 for value in sensor_values)
        
        if all_below_160 and at_least_one_above_100:
            # Home sweet home - suspend wheels but keep reading
            M.stop()
            
            # Update display with sensor values
            update_lcd("HOME SWEET HOME :)", sensor_values, None)
            
            # Set calm blue LEDs
            for i in range(4):
                strip.pixels_set(i, strip.BLUE)
            strip.pixels_show()
            
            print(f"Home state - sensors: {sensor_values}")
            time.sleep(0.1)
            continue
        
        # Check if robot is picked up (extremely low sensor values)
        picked_up = True
        for value in sensor_values:
            if value >= 30:  # At least one sensor reads normal
                picked_up = False
                break
        
        if picked_up:
            # Robot is picked up - stop motors and SCREAM!
            M.stop()
            
            # Clear LCD and show message
            lcd.fill(lcd.BLACK)
            lcd.text("Put me down :(", 65, 20, lcd.WHITE)
            
            # Draw mathematical heart shape
            # Heart parameters
            n = 24  # Size factor (doubled for larger heart)
            center_x = 120  # Center of screen
            center_y = 70   # Vertical position (moved up to fit on screen)
            RED_COLOR = 0x07E0  # Red color for this LCD
            
            # Draw the heart using the mathematical formula
            for y in range(-n, 2 * n + 1):
                for x in range(-2 * n, 2 * n + 1):
                    # Check if point is inside heart shape
                    if y <= 0:
                        # Upper part - two circles
                        left_circle = math.sqrt((x + n) * (x + n) + y * y) <= n
                        right_circle = math.sqrt((x - n) * (x - n) + y * y) <= n
                        if left_circle or right_circle:
                            # Draw pixel
                            lcd.fill_rect(center_x + x, center_y + y, 1, 1, RED_COLOR)
                    else:
                        # Lower part - triangle
                        if abs(x) <= 2 * n - y:
                            # Draw pixel
                            lcd.fill_rect(center_x + x, center_y + y, 1, 1, RED_COLOR)
            
            # Now carve out the zigzag crack with black rectangles
            # Adjusted with 1 pixel taller blocks (12 instead of 10)
            lcd.fill_rect(116, 45, 8, 12, lcd.BLACK)    # Start at top
            lcd.fill_rect(112, 56, 8, 12, lcd.BLACK)    # Zig left
            lcd.fill_rect(120, 67, 8, 12, lcd.BLACK)    # Zag right
            lcd.fill_rect(114, 78, 8, 12, lcd.BLACK)    # Zig left
            lcd.fill_rect(122, 89, 8, 12, lcd.BLACK)    # Zag right
            lcd.fill_rect(116, 100, 8, 12, lcd.BLACK)   # Center
            lcd.fill_rect(112, 111, 8, 12, lcd.BLACK)   # Zig left
            lcd.fill_rect(120, 122, 8, 10, lcd.BLACK)   # Zag right
            lcd.fill_rect(116, 131, 8, 10, lcd.BLACK)   # Center bottom
            
            lcd.show()
            
            # SCREAM with buzzer!
            buzzer.freq(2000)  # High pitch
            buzzer.duty_u16(65535)  # Maximum volume
            time.sleep(0.3)
            buzzer.freq(1500)  # Lower pitch
            time.sleep(0.2)
            buzzer.freq(2500)  # Even higher
            time.sleep(0.2)
            buzzer.duty_u16(0)  # Stop screaming
            
            # Flash red LEDs
            for i in range(4):
                strip.pixels_set(i, strip.RED)
            strip.pixels_show()
            
            print("Robot picked up - HELP ME!")
            time.sleep(0.3)  # Wait a bit before continuing
            
            # Reset LEDs
            for i in range(4):
                strip.pixels_set(i, strip.BLUE)
            strip.pixels_show()
            continue
        
        # Check if stuck
        if check_if_stuck(sensor_values):
            handle_stuck()
            continue
        
        # Manage buzzer
        if buzzer_on and time.ticks_diff(time.ticks_ms(), buzzer_start_time) > 100:
            buzzer.duty_u16(0)  # Turn off buzzer after 100ms
            buzzer_on = False
        
        # Detect line pattern
        num_on_line, line_position, is_intersection = detect_line_pattern(sensor_values)
        
        # Update last line position and sensor values if we have a valid reading
        if line_position is not None:
            last_line_position = line_position
        
        # Save sensor values when we detect a line (for stuck recovery)
        if num_on_line > 0:
            last_sensor_values = sensor_values.copy()
        
        # State machine logic
        if current_state == STATE_SEARCHING:
            if num_on_line > 0 and not is_intersection:
                # Found line!
                current_state = STATE_FOLLOWING
                search_count = 0
                search_start_time = 0  # Reset search timer
                M.stop()
                # Quick beep
                buzzer.freq(523)
                buzzer.duty_u16(32768)
                buzzer_on = True
                buzzer_start_time = time.ticks_ms()
                print(f"Line found! Position: {line_position}")
            else:
                # Keep searching
                if search_start_time == 0:
                    start_search_motion()
                else:
                    update_search()
        
        elif current_state == STATE_FOLLOWING:
            if is_intersection:
                # Intersection detected
                current_state = STATE_INTERSECTION
                line_lost_time = 0  # Reset lost time
                print("Intersection detected!")
            elif num_on_line == 0:
                # Line not visible
                if line_lost_time == 0:
                    # First time losing line - record time
                    line_lost_time = time.ticks_ms()
                    print("Line temporarily lost, continuing straight...")
                    # Continue straight
                    M.forward(BASE_SPEED)
                elif time.ticks_diff(time.ticks_ms(), line_lost_time) > int(LINE_LOST_TOLERANCE * 1000):
                    # Lost line for too long - start searching
                    current_state = STATE_SEARCHING
                    M.stop()
                    line_lost_time = 0
                    print(f"Line lost for >{LINE_LOST_TOLERANCE*1000}ms, searching...")
                else:
                    # Still within tolerance - keep going straight
                    M.forward(BASE_SPEED)
            else:
                # Following the line normally
                line_lost_time = 0  # Reset lost time
                follow_line(line_position)
        
        elif current_state == STATE_INTERSECTION:
            # Start intersection handling
            print(f"STATE_INTERSECTION: Starting intersection handling")
            handle_intersection()
        
        elif current_state == STATE_TURNING:
            # Check if turn is complete
            elapsed = time.ticks_diff(time.ticks_ms(), turn_start_time)
            if elapsed > turn_duration:
                print(f"Turn complete after {elapsed}ms")
                M.stop()  # Stop turning
                current_state = next_state
                # Reset search parameters for fresh start
                if next_state == STATE_SEARCHING:
                    search_start_time = 0
                    search_count = 0
                    # Reset LEDs to blue
                    for i in range(4):
                        strip.pixels_set(i, strip.BLUE)
                    strip.pixels_show()
        
        elif current_state == STATE_MOVING_FORWARD:
            # Check if forward movement is complete
            if time.ticks_diff(time.ticks_ms(), turn_start_time) > turn_duration:
                current_state = next_state
                # Reset LEDs when done with intersection
                if next_state == STATE_FOLLOWING:
                    for i in range(4):
                        strip.pixels_set(i, strip.BLUE)
                    strip.pixels_show()
        
        # Update display
        update_lcd(current_state, sensor_values, line_position)
        
        # Small delay
        time.sleep(0.01)  # 10ms loop time for responsiveness

except KeyboardInterrupt:
    print("\nGrid Follower stopped by user")
    M.stop()
    buzzer.deinit()
    # Turn off LEDs
    for i in range(4):
        strip.pixels_set(i, strip.BLACK)
    strip.pixels_show()

except Exception as e:
    print(f"Error: {e}")
    M.stop()
    buzzer.deinit()
    raise