from Motor import PicoGo
import time

M = PicoGo()

print("Motor Test")
print("Forward 30...")
M.forward(30)
time.sleep(2)

print("Stop...")
M.stop()
time.sleep(1)

print("Backward 30...")
M.backward(30)
time.sleep(2)

print("Stop...")
M.stop()
time.sleep(1)

print("Right 20...")
M.right(20)
time.sleep(2)

print("Left 20...")
M.left(20)
time.sleep(2)

print("Stop...")
M.stop()
print("Test complete!")