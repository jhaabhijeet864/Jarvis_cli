"""
Jarvis Voice Assistant GUI
Creates a visualizer window with an animated orb that reflects the assistant's state.
"""
import pygame
import sys
import math
import threading
import queue

# --- Constants ---
# Window
WIDTH, HEIGHT = 400, 300
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
ORB_COLOR_IDLE = (0, 100, 255)       # Blue
ORB_COLOR_LISTENING = (100, 255, 100) # Green
ORB_COLOR_SPEAKING = (255, 100, 0)    # Orange

# Orb settings
ORB_RADIUS_MIN = 30
ORB_RADIUS_MAX = 40
ORB_BREATHE_SPEED = 0.02
ORB_PULSE_SPEED = 0.1

class Visualizer:
    """
    Manages the Pygame GUI window and all animations.
    """
    def __init__(self, comm_queue: queue.Queue):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Jarvis")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)

        self.comm_queue = comm_queue
        
        # State
        self.state = "IDLE"  # IDLE, LISTENING, SPEAKING
        self.display_text = ""

        # Animation variables
        self.angle = 0
        self.orb_radius = ORB_RADIUS_MIN
        self.orb_color = ORB_COLOR_IDLE
        
        # For speaking animation
        self.speaking_pulse = 0
        self.speaking_text = ""

    def _check_queue(self):
        """Check for messages from the backend bot."""
        try:
            message = self.comm_queue.get_nowait()
            new_state = message.get("state")
            if new_state:
                self.state = new_state
                self.angle = 0 # Reset animation angle on state change
                
                if self.state == "SPEAKING":
                    self.speaking_text = message.get("text", "")
                    self.speaking_pulse = 1.0 # Start pulse
                else:
                    self.speaking_text = ""

        except queue.Empty:
            pass

    def _update_animations(self):
        """Update animation values based on the current state."""
        self.angle += ORB_BREATHE_SPEED

        if self.state == "IDLE":
            self.orb_color = ORB_COLOR_IDLE
            # Breathing effect
            self.orb_radius = ORB_RADIUS_MIN + (ORB_RADIUS_MAX - ORB_RADIUS_MIN) * (0.5 * (1 + math.sin(self.angle)))
        
        elif self.state == "LISTENING":
            self.orb_color = ORB_COLOR_LISTENING
            # Glow effect
            self.orb_radius = ORB_RADIUS_MAX
        
        elif self.state == "SPEAKING":
            self.orb_color = ORB_COLOR_SPEAKING
            # Pulsing effect for text
            if self.speaking_pulse > 0:
                self.speaking_pulse -= 0.02
            self.orb_radius = ORB_RADIUS_MIN + (ORB_RADIUS_MAX - ORB_RADIUS_MIN) * self.speaking_pulse
            
    def _draw(self):
        """Draw all elements to the screen."""
        self.screen.fill(BLACK)

        # Draw the orb
        pygame.draw.circle(self.screen, self.orb_color, (WIDTH // 2, HEIGHT // 2), int(self.orb_radius))

        # Draw state text
        state_surface = self.font.render(self.state, True, WHITE)
        self.screen.blit(state_surface, (10, 10))

        # Draw speaking text
        if self.speaking_text:
            text_surface = self.font.render(self.speaking_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT - 40))
            self.screen.blit(text_surface, text_rect)

        pygame.display.flip()

    def run(self):
        """The main loop of the GUI."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            self._check_queue()
            self._update_animations()
            self._draw()
            
            self.clock.tick(FPS)
        
        # When the loop exits, we signal the backend to shut down
        self.comm_queue.put({"state": "SHUTDOWN"})
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    # Example of running the GUI standalone for testing
    q = queue.Queue()
    
    def test_backend(q):
        import time
        time.sleep(3)
        q.put({"state": "LISTENING"})
        time.sleep(3)
        q.put({"state": "SPEAKING", "text": "Hello, this is a test."})
        time.sleep(4)
        q.put({"state": "IDLE"})
        time.sleep(3)
        q.put({"state": "SHUTDOWN"})

    threading.Thread(target=test_backend, args=(q,), daemon=True).start()
    
    visualizer = Visualizer(q)
    visualizer.run()
