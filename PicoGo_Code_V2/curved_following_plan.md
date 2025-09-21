# Curved Path Following Implementation Plan

## Key Findings
- IR sensors are **binary only** (no distance measurement)
- Detection range: ~5-20cm (close proximity)
- DSL = Left sensor (Pin 3), DSR = Right sensor (Pin 2)
- Return 0 when detecting, 1 when clear

## Implementation Strategy

### 1. **Multi-Zone Detection Model**
```
    [IR-L]  [Ultrasonic]  [IR-R]
      |          |           |
   5-20cm    15-80cm     5-20cm
```

### 2. **State Machine Enhancement**

#### States:
- **FOLLOWING_STRAIGHT**: Object centered (ultrasonic only)
- **FOLLOWING_LEFT**: Object drifting left (left IR + ultrasonic)
- **FOLLOWING_RIGHT**: Object drifting right (right IR + ultrasonic)
- **REACQUIRING_LEFT**: Lost ultrasonic, but left IR active
- **REACQUIRING_RIGHT**: Lost ultrasonic, but right IR active

### 3. **Filtered IR Reading System**

```python
class IRFilter:
    def __init__(self):
        self.left_history = [1, 1, 1, 1, 1]  # 5-sample history
        self.right_history = [1, 1, 1, 1, 1]
        self.last_update = time.ticks_ms()
    
    def update(self):
        # Only update every 20ms to avoid over-sampling
        if time.ticks_diff(time.ticks_ms(), self.last_update) < 20:
            return
            
        self.left_history.append(DSL.value())
        self.right_history.append(DSR.value())
        self.left_history.pop(0)
        self.right_history.pop(0)
        self.last_update = time.ticks_ms()
    
    def get_filtered(self):
        # Need 3/5 readings to confirm detection
        left_count = sum(1 for x in self.left_history if x == 0)
        right_count = sum(1 for x in self.right_history if x == 0)
        
        left_detected = left_count >= 3
        right_detected = right_count >= 3
        
        return left_detected, right_detected
    
    def get_confidence(self):
        # Return detection confidence 0-100%
        left_conf = (5 - sum(self.left_history)) * 20
        right_conf = (5 - sum(self.right_history)) * 20
        return left_conf, right_conf
```

### 4. **Movement Control Logic**

```python
def calculate_following_movement(distance, left_ir, right_ir, left_conf, right_conf):
    """
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
        return (base_speed, base_speed, "STRAIGHT")
    
    # Case 2: Object drifting left (left IR + ultrasonic)
    if distance <= MAX_DISTANCE and left_ir and not right_ir:
        # Gentle curve left - reduce left wheel speed
        left_speed = base_speed - int(5 + left_conf * 0.1)  # 5-15 reduction
        right_speed = base_speed
        return (left_speed, right_speed, "DRIFT_LEFT")
    
    # Case 3: Object drifting right (right IR + ultrasonic)
    if distance <= MAX_DISTANCE and right_ir and not left_ir:
        # Gentle curve right - reduce right wheel speed
        left_speed = base_speed
        right_speed = base_speed - int(5 + right_conf * 0.1)  # 5-15 reduction
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
```

### 5. **Anti-Distraction Logic**

To prevent turning into random closer objects:

```python
class FollowingContext:
    def __init__(self):
        self.last_good_distance = None
        self.last_good_time = 0
        self.following_side = None  # 'left', 'right', or None
        self.confidence_threshold = 50
    
    def should_ignore_ir(self, current_distance, ir_side):
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
            if distance_change < 5:  # Less than 5cm change
                log(f"Ignoring sudden {ir_side} IR detection - distance stable")
                return True
        
        return False
```

### 6. **LCD Display Information**

```python
def update_following_lcd(state, distance, left_ir, right_ir, left_conf, right_conf, movement_state):
    lcd.fill(lcd.BLACK)
    
    # Title
    lcd.text("Following Mode", 60, 5, lcd.WHITE)
    
    # Distance bar with direction indicator
    bar_width = int((distance / 100) * 200)
    lcd.rect(20, 25, 200, 15, lcd.WHITE)
    lcd.fill_rect(20, 25, bar_width, 15, lcd.GREEN)
    
    # IR indicators
    if left_ir:
        lcd.fill_rect(5, 25, 10, 15, lcd.YELLOW)  # Left indicator
    if right_ir:
        lcd.fill_rect(225, 25, 10, 15, lcd.YELLOW)  # Right indicator
    
    # Status text
    lcd.text(f"Dist: {distance:.1f}cm", 10, 45, lcd.WHITE)
    lcd.text(f"State: {movement_state}", 10, 60, lcd.GREEN)
    
    # IR confidence
    lcd.text(f"IR L:{left_conf}% R:{right_conf}%", 10, 75, lcd.CYAN)
    
    # Movement indicator
    if "LEFT" in movement_state:
        lcd.text("<--", 10, 90, lcd.YELLOW)
    elif "RIGHT" in movement_state:
        lcd.text("-->", 200, 90, lcd.YELLOW)
    else:
        lcd.text("^^^", 105, 90, lcd.GREEN)
    
    lcd.show()
```

### 7. **Detailed Logging**

```python
def log_following_state(distance, left_ir, right_ir, left_conf, right_conf, 
                       movement_state, left_speed, right_speed):
    log(f"FOLLOW: dist={distance:.1f}cm, IR_L={left_ir}({left_conf}%), " +
        f"IR_R={right_ir}({right_conf}%), state={movement_state}, " +
        f"motors=L{left_speed}/R{right_speed}")
```

### 8. **Integration Points**

1. Replace current `if distance < MIN_DISTANCE:` check
2. Add IR filtering at start of main loop
3. Replace simple `M.forward(speed)` with differential control
4. Add periodic state logging (every 500ms)
5. Update LCD with richer information

### 9. **Testing Strategy**

1. **Straight line test**: Verify no false turns
2. **Gentle curve test**: Object moves in arc
3. **Sharp turn test**: Object makes 90° turn
4. **Distraction test**: Another object passes by
5. **Reacquisition test**: Lose and reacquire target

This implementation provides smooth curved following while avoiding false triggers and maintaining stable tracking.