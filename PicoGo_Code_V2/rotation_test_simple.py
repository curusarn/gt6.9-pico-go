from Motor import PicoGo
import time

M = PicoGo()

print("Simple Rotation Test")
print("===================")

# Test 1: Exact copy of Motor.py test
print("\nTest 1: Exact Motor.py method - M.right(30) for 0.5s")
M.right(30)
time.sleep(0.5)
M.stop()
print("Did it rotate right?")
time.sleep(2)

# Test 2: Longer duration
print("\nTest 2: M.right(30) for 3 seconds")
M.right(30)
time.sleep(3)
M.stop()
print("Did it rotate right for 3 seconds?")
time.sleep(2)

# Test 3: Left rotation
print("\nTest 3: M.left(30) for 3 seconds")
M.left(30)
time.sleep(3)
M.stop()
print("Did it rotate left?")
time.sleep(2)

# Test 4: Check if we need to call it repeatedly
print("\nTest 4: Calling M.right(30) in a loop")
start = time.ticks_ms()
while time.ticks_diff(time.ticks_ms(), start) < 3000:
    M.right(30)  # Call it repeatedly
    time.sleep(0.01)
M.stop()
print("Did continuous calling work?")
time.sleep(2)

# Test 5: Direct motor control
print("\nTest 5: Using setMotor(30, -30) for rotation")
M.setMotor(30, -30)
time.sleep(3)
M.stop()
print("Did setMotor rotation work?")

print("\nTest complete!")