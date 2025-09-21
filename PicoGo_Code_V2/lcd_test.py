from ST7789 import ST7789
import time

# Initialize the LCD
lcd = ST7789()

# Clear the screen with white
lcd.fill(lcd.WHITE)
lcd.show()

# Display some text
lcd.text("LCD Test!", 80, 10, lcd.BLUE)
lcd.text("PicoGo Robot", 65, 30, lcd.RED)
lcd.text("Display Working", 50, 50, lcd.GREEN)
lcd.show()

time.sleep(2)

# Draw some shapes
lcd.fill(lcd.BLACK)
# Draw a rectangle
lcd.rect(10, 10, 220, 115, lcd.YELLOW)
# Draw filled rectangles
lcd.fill_rect(30, 30, 40, 40, lcd.RED)
lcd.fill_rect(90, 30, 40, 40, lcd.GREEN)
lcd.fill_rect(150, 30, 40, 40, lcd.BLUE)
# Draw some lines
lcd.line(30, 90, 210, 90, lcd.GBLUE)
lcd.line(120, 20, 120, 110, lcd.YELLOW)
lcd.show()

time.sleep(2)

# Color gradient test
lcd.fill(lcd.BLACK)
lcd.text("Color Test", 70, 10, lcd.WHITE)
colors = [lcd.RED, lcd.GREEN, lcd.BLUE, lcd.YELLOW, lcd.GBLUE, lcd.WHITE]
for i, color in enumerate(colors):
    lcd.fill_rect(20 + i*35, 40, 30, 60, color)
lcd.show()

print("LCD test completed!")