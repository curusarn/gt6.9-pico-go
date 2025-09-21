# IR Sensor Integration Plan for Improved Obstacle Following

## Current Limitations
- Robot only uses ultrasonic sensor (straight ahead)
- Cannot detect obstacles to the sides
- Follows in straight line only
- IR sensors are disabled due to over-sensitivity

## Proposed Solution

### 1. **Re-enable IR Sensors with Smart Filtering**
- Use IR sensors for lateral obstacle detection
- Implement debouncing to avoid false triggers
- Only use IR sensors when in FOLLOWING state

### 2. **Three-Zone Following Strategy**
```
     [L]  [U]  [R]
      |    |    |
   Left  Ultra  Right
    IR   sonic   IR
```

### 3. **Movement Logic**

#### When Following:
- **Ultrasonic only** (straight): Continue forward
- **Left IR triggered**: Object veering left → Adjust slightly left
- **Right IR triggered**: Object veering right → Adjust slightly right
- **Both IR triggered**: Object is wide → Use ultrasonic for distance
- **Ultrasonic lost + Left IR**: Object moved left → Turn left to reacquire
- **Ultrasonic lost + Right IR**: Object moved right → Turn right to reacquire

### 4. **Implementation Steps**

#### Step 1: Add IR Sensor Debouncing
```python
# Track IR sensor states over time
ir_left_history = [1, 1, 1]  # Last 3 readings
ir_right_history = [1, 1, 1]

def get_filtered_ir():
    # Update history
    ir_left_history.append(DSL.value())
    ir_right_history.append(DSR.value())
    ir_left_history.pop(0)
    ir_right_history.pop(0)
    
    # Only trigger if 2/3 readings show detection
    left_detected = sum(ir_left_history) <= 1
    right_detected = sum(ir_right_history) <= 1
    
    return left_detected, right_detected
```

#### Step 2: Modify Following Logic
```python
if state == "FOLLOWING":
    left_ir, right_ir = get_filtered_ir()
    
    if distance < MIN_DISTANCE:
        # Too close - stop
        state = "STOPPED"
    elif distance > MAX_DISTANCE:
        # Lost target with ultrasonic
        if left_ir:
            # Object went left - turn left
            M.left(15)
            log("Object moved left, turning to follow")
        elif right_ir:
            # Object went right - turn right  
            M.right(15)
            log("Object moved right, turning to follow")
        else:
            # Completely lost - go to scanning
            state = "SCANNING"
    else:
        # In following range
        if left_ir and not right_ir:
            # Object is to our left - adjust heading
            M.setMotor(speed - 5, speed + 5)  # Slight left turn while moving
        elif right_ir and not left_ir:
            # Object is to our right - adjust heading
            M.setMotor(speed + 5, speed - 5)  # Slight right turn while moving
        else:
            # Straight ahead or both sides
            M.forward(speed)
```

#### Step 3: Add Predictive Scanning
When ultrasonic loses target but IR detected it moving:
- Scan in the direction indicated by IR
- Shorter scan duration in that direction
- Return to following once reacquired

### 5. **Benefits**
- Can follow objects that move in curves
- Better tracking when object moves laterally
- Smoother following with gradual adjustments
- Can reacquire lost targets more intelligently

### 6. **Testing Approach**
1. Test IR sensor filtering alone
2. Test basic left/right adjustments
3. Test full integration with scanning
4. Fine-tune speeds and thresholds