from Motor import PicoGo
import time

M = PicoGo()

print("Alternating Motor Test")
print("=====================")

# Use setMotor to control each motor independently
print("\n1. Left motor only forward (should move in arc)")
M.setMotor(50, 0)
time.sleep(3)
M.stop()
time.sleep(1)

print("\n2. Right motor only forward (should move in arc)")  
M.setMotor(0, 50)
time.sleep(3)
M.stop()
time.sleep(1)

print("\n3. Left motor forward, right motor backward (turn right)")
M.setMotor(50, -50)
time.sleep(3)
M.stop()
time.sleep(1)

print("\n4. Left motor backward, right motor forward (turn left)")
M.setMotor(-50, 50)
time.sleep(3)
M.stop()
time.sleep(1)

print("\n5. Using right() method")
M.right(30)
time.sleep(3)
M.stop()
time.sleep(1)

print("\n6. Using left() method")
M.left(30)
time.sleep(3)
M.stop()

print("\nTest complete!")
print("If rotation doesn't work, one motor may have power issues")