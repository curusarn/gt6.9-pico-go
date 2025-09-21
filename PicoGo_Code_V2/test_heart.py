from machine import Pin, PWM
import time
from ST7789 import ST7789

# Initialize LCD
lcd = ST7789()

# Clear the display
lcd.fill(lcd.BLACK)

# Show text
lcd.text("Put me down :(", 65, 20, lcd.WHITE)

# Test color values
RED_COLOR = 0x001F  # This might show as red on BGR display
# Alternative color values to test:
# RED_RGB = 0xF800  # Standard RGB red
# RED_BGR = 0x001F  # BGR red

print("Drawing heart with RED_COLOR = 0x001F")

# Draw the complete heart first
# Left bump
lcd.fill_rect(70, 50, 50, 20, RED_COLOR)
# Right bump  
lcd.fill_rect(100, 50, 50, 20, RED_COLOR)
# Main body
lcd.fill_rect(60, 65, 100, 60, RED_COLOR)
# Bottom point
lcd.fill_rect(75, 125, 70, 10, RED_COLOR)
lcd.fill_rect(85, 135, 50, 10, RED_COLOR)
lcd.fill_rect(95, 145, 30, 5, RED_COLOR)

# Now carve out the zigzag crack with black rectangles
# Creating a zigzag pattern down the middle
print("Drawing zigzag crack...")
lcd.fill_rect(108, 50, 4, 8, lcd.BLACK)    # Start at top
lcd.fill_rect(106, 58, 4, 8, lcd.BLACK)    # Zig left
lcd.fill_rect(110, 66, 4, 8, lcd.BLACK)    # Zag right
lcd.fill_rect(107, 74, 4, 8, lcd.BLACK)    # Zig left
lcd.fill_rect(111, 82, 4, 8, lcd.BLACK)    # Zag right
lcd.fill_rect(108, 90, 4, 8, lcd.BLACK)    # Center
lcd.fill_rect(105, 98, 4, 8, lcd.BLACK)    # Zig left
lcd.fill_rect(109, 106, 4, 8, lcd.BLACK)   # Zag right
lcd.fill_rect(106, 114, 4, 8, lcd.BLACK)   # Zig left
lcd.fill_rect(110, 122, 4, 8, lcd.BLACK)   # Zag right
lcd.fill_rect(108, 130, 4, 8, lcd.BLACK)   # Center
lcd.fill_rect(106, 138, 4, 8, lcd.BLACK)   # Zig left
lcd.fill_rect(108, 146, 4, 4, lcd.BLACK)   # Bottom

# Show the display
lcd.show()

print("Heart displayed!")

# Test different colors after 3 seconds
time.sleep(3)

# Try with standard RGB red
print("\nTesting with RGB red (0xF800)...")
lcd.fill(lcd.BLACK)
lcd.text("Testing RGB Red", 65, 20, lcd.WHITE)
lcd.fill_rect(70, 50, 50, 20, 0xF800)
lcd.fill_rect(100, 50, 50, 20, 0xF800)
lcd.show()

time.sleep(3)

# Let's also test what the LCD color constants actually show
print("\nTesting LCD color constants...")
lcd.fill(lcd.BLACK)
lcd.text("LCD.RED", 10, 10, lcd.WHITE)
lcd.fill_rect(10, 30, 60, 30, lcd.RED)

lcd.text("LCD.GREEN", 80, 10, lcd.WHITE)
lcd.fill_rect(80, 30, 60, 30, lcd.GREEN)

lcd.text("LCD.BLUE", 150, 10, lcd.WHITE)
lcd.fill_rect(150, 30, 60, 30, lcd.BLUE)

lcd.text("0x001F", 10, 70, lcd.WHITE)
lcd.fill_rect(10, 90, 60, 30, 0x001F)

lcd.text("0xF800", 80, 70, lcd.WHITE)
lcd.fill_rect(80, 90, 60, 30, 0xF800)

lcd.text("0x07E0", 150, 70, lcd.WHITE)
lcd.fill_rect(150, 90, 60, 30, 0x07E0)

lcd.show()

print("\nColor test complete!")
print("lcd.RED =", hex(lcd.RED))
print("lcd.GREEN =", hex(lcd.GREEN))
print("lcd.BLUE =", hex(lcd.BLUE))