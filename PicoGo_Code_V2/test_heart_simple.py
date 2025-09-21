from machine import Pin, PWM
import time
from ST7789 import ST7789

# Initialize LCD
lcd = ST7789()

# Clear the display
lcd.fill(lcd.BLACK)

# Show text
lcd.text("Put me down :(", 65, 20, lcd.WHITE)

# Draw broken heart
RED_COLOR = 0x07E0  # Red color for this LCD

# Draw mathematical heart shape
import math

# Heart parameters
n = 24  # Size factor (doubled for larger heart)
center_x = 120  # Center of screen
center_y = 70   # Vertical position (moved up to fit on screen)

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
print("Drawing zigzag crack...")
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

# Show the display
lcd.show()

print("Heart with zigzag crack displayed!")