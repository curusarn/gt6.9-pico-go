from Motor import PicoGo
import time

M = PicoGo()

print("Direct Motor Test - Using exact methods from working examples")

# Test 1: Forward (from Ultrasonic_Obstacle_Avoidance.py)
print("\nTest 1: M.forward(20) for 3 seconds")
M.forward(20)
time.sleep(3)
M.stop()
time.sleep(1)

# Test 2: Right turn (from Ultrasonic_Obstacle_Avoidance.py)  
print("\nTest 2: M.right(20) for 3 seconds")
M.right(20)
time.sleep(3)
M.stop()
time.sleep(1)

# Test 3: Left turn (from bluetooth.py)
print("\nTest 3: M.left(20) for 3 seconds")
M.left(20)
time.sleep(3)
M.stop()
time.sleep(1)

# Test 4: Higher speed forward
print("\nTest 4: M.forward(50) for 3 seconds")
M.forward(50)
time.sleep(3)
M.stop()
time.sleep(1)

# Test 5: Test setMotor directly (from Line-Tracking.py)
print("\nTest 5: M.setMotor(30, -30) - spin right for 3 seconds")
M.setMotor(30, -30)
time.sleep(3)
M.stop()

print("\nAll tests complete!")
print("If motors didn't move, check:")
print("1. Battery level")
print("2. Motor connections") 
print("3. Power switch on robot")