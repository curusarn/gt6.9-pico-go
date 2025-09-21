from machine import Pin, PWM
from Motor import PicoGo
import time

class PicoGoBuzzer:
    """Enhanced buzzer control for PicoGo robot with PWM tone generation"""
    
    def __init__(self):
        self.buzzer = PWM(Pin(4))
        self.buzzer.duty_u16(0)  # Start with buzzer off
        
        # Define common frequencies
        self.FREQ_LOW = 200
        self.FREQ_MID = 500
        self.FREQ_HIGH = 1000
        self.FREQ_ALARM = 800
        
    def beep(self, frequency=500, duration=0.1, duty=32768):
        """
        Generate a beep at specified frequency
        
        Args:
            frequency: Frequency in Hz (20-20000)
            duration: Duration in seconds
            duty: Duty cycle (0-65535), default is 50% (32768)
        """
        if 20 <= frequency <= 20000:
            self.buzzer.freq(frequency)
            self.buzzer.duty_u16(duty)
            time.sleep(duration)
            self.buzzer.duty_u16(0)
    
    def beep_pattern(self, pattern):
        """
        Play a beep pattern
        
        Args:
            pattern: List of tuples (frequency, duration, pause_after)
        """
        for freq, duration, pause in pattern:
            self.beep(freq, duration)
            time.sleep(pause)
    
    def startup_sound(self):
        """Play startup sound - ascending tones"""
        pattern = [
            (200, 0.1, 0.05),
            (400, 0.1, 0.05),
            (600, 0.1, 0.05),
            (800, 0.15, 0.1)
        ]
        self.beep_pattern(pattern)
    
    def shutdown_sound(self):
        """Play shutdown sound - descending tones"""
        pattern = [
            (800, 0.1, 0.05),
            (600, 0.1, 0.05),
            (400, 0.1, 0.05),
            (200, 0.15, 0.1)
        ]
        self.beep_pattern(pattern)
    
    def obstacle_detected_sound(self):
        """Play sound when obstacle is detected"""
        pattern = [
            (1000, 0.05, 0.05),
            (1000, 0.05, 0.05),
            (1000, 0.05, 0.1)
        ]
        self.beep_pattern(pattern)
    
    def line_detected_sound(self):
        """Play sound when line is detected"""
        self.beep(600, 0.05)
    
    def turn_sound(self):
        """Play sound when turning"""
        self.beep(400, 0.05)
    
    def error_sound(self):
        """Play error sound"""
        pattern = [
            (100, 0.3, 0.1),
            (100, 0.3, 0.1)
        ]
        self.beep_pattern(pattern)
    
    def success_sound(self):
        """Play success/completion sound"""
        pattern = [
            (523, 0.1, 0.05),   # C5
            (659, 0.1, 0.05),   # E5
            (784, 0.2, 0.1)     # G5
        ]
        self.beep_pattern(pattern)
    
    def proximity_alert(self, distance):
        """
        Play proximity alert based on distance
        Closer distance = higher frequency and faster beeping
        
        Args:
            distance: Distance in cm (0-100)
        """
        if distance < 10:
            freq = 1500
            delay = 0.1
        elif distance < 20:
            freq = 1000
            delay = 0.2
        elif distance < 30:
            freq = 700
            delay = 0.3
        elif distance < 50:
            freq = 500
            delay = 0.5
        else:
            return  # No sound for distances > 50cm
        
        self.beep(freq, 0.05)
        time.sleep(delay)
    
    def battery_low_warning(self):
        """Play battery low warning sound"""
        for _ in range(3):
            self.beep(300, 0.1)
            time.sleep(0.1)
            self.beep(200, 0.1)
            time.sleep(0.3)
    
    def communication_sound(self):
        """Play sound for successful communication"""
        pattern = [
            (800, 0.05, 0.02),
            (1200, 0.05, 0.02),
            (800, 0.05, 0.02)
        ]
        self.beep_pattern(pattern)
    
    def deinit(self):
        """Properly shut down the buzzer"""
        self.buzzer.duty_u16(0)
        self.buzzer.deinit()


# Example usage integrating with PicoGo robot
if __name__ == "__main__":
    # Initialize robot and buzzer
    robot = PicoGo()
    buzzer = PicoGoBuzzer()
    
    # Startup sequence
    print("PicoGo Robot with Enhanced Buzzer Starting...")
    buzzer.startup_sound()
    
    try:
        # Example movement with sound feedback
        print("Moving forward...")
        buzzer.beep(500, 0.1)
        robot.forward(50)
        time.sleep(2)
        
        print("Turning left...")
        buzzer.turn_sound()
        robot.left(30)
        time.sleep(1)
        
        print("Turning right...")
        buzzer.turn_sound()
        robot.right(30)
        time.sleep(1)
        
        print("Stopping...")
        robot.stop()
        buzzer.success_sound()
        
        # Simulate obstacle detection
        print("\nSimulating obstacle detection at various distances...")
        for distance in [50, 30, 20, 10, 5]:
            print(f"Obstacle at {distance}cm")
            buzzer.proximity_alert(distance)
            time.sleep(1)
        
        # Alert sounds demo
        print("\nTesting alert sounds...")
        
        print("Obstacle detected!")
        buzzer.obstacle_detected_sound()
        time.sleep(1)
        
        print("Communication established!")
        buzzer.communication_sound()
        time.sleep(1)
        
        print("Battery low warning!")
        buzzer.battery_low_warning()
        time.sleep(1)
        
    except KeyboardInterrupt:
        print("\nProgram interrupted")
        buzzer.error_sound()
        
    finally:
        print("Shutting down...")
        robot.stop()
        buzzer.shutdown_sound()
        buzzer.deinit()
        print("Robot stopped and buzzer deinitialized")