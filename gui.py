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
WIDTH, HEIGHT = 800, 600  # Increased size for code display
FPS = 60

# Colors
BLACK = (10, 10, 20)
WHITE = (230, 230, 230)
CODE_BG = (20, 20, 30)
ORB_COLOR_IDLE = (0, 100, 255)       # Blue
ORB_COLOR_LISTENING = (100, 255, 100) # Green
ORB_COLOR_SPEAKING = (255, 100, 0)    # Orange
ORB_COLOR_CODING = (160, 32, 240)     # Purple

# Orb settings
ORB_RADIUS_MIN = 30
ORB_RADIUS_MAX = 40
ORB_BREATHE_SPEED = 0.02

class Visualizer:
    """
    Manages the Pygame GUI window and all animations.
    """
    def __init__(self, comm_queue: queue.Queue):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Jarvis")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.code_font = pygame.font.SysFont("Consolas", 18)

        self.comm_queue = comm_queue
        
        # State
        self.state = "IDLE"  # IDLE, LISTENING, SPEAKING, DISPLAY_CODE
        self.speaking_text = ""
        self.code_to_display = ""

        # Animation variables
        self.angle = 0
        self.orb_radius = ORB_RADIUS_MIN
        self.orb_color = ORB_COLOR_IDLE
        self.speaking_pulse = 0

    def _check_queue(self):
        """Check for messages from the backend bot."""
        try:
            message = self.comm_queue.get_nowait()
            new_state = message.get("state")
            if new_state:
                print(f"[GUI] State change: {new_state}")
                self.state = new_state
                self.angle = 0 
                
                # Reset display texts
                self.speaking_text = ""
                self.code_to_display = ""
                
                if self.state == "SPEAKING":
                    self.speaking_text = message.get("text", "")
                    self.speaking_pulse = 1.0
                elif self.state == "DISPLAY_CODE":
                    self.code_to_display = message.get("code", "")
                    
        except queue.Empty:
            pass

    def _update_animations(self):
        """Update animation values based on the current state."""
        self.angle += ORB_BREATHE_SPEED

        if self.state == "IDLE":
            self.orb_color = ORB_COLOR_IDLE
            self.orb_radius = ORB_RADIUS_MIN + (ORB_RADIUS_MAX - ORB_RADIUS_MIN) * (0.5 * (1 + math.sin(self.angle)))
        
        elif self.state == "LISTENING":
            self.orb_color = ORB_COLOR_LISTENING
            self.orb_radius = ORB_RADIUS_MAX
        
        elif self.state == "SPEAKING":
            self.orb_color = ORB_COLOR_SPEAKING
            if self.speaking_pulse > 0:
                self.speaking_pulse -= 0.02
            self.orb_radius = ORB_RADIUS_MIN + (ORB_RADIUS_MAX - ORB_RADIUS_MIN) * self.speaking_pulse
            
        elif self.state == "DISPLAY_CODE":
            self.orb_color = ORB_COLOR_CODING
            self.orb_radius = ORB_RADIUS_MIN

    def _draw_text_multiline(self, surface, text, x, y, font, color):
        """Helper to draw multi-line text."""
        lines = text.splitlines()
        for i, line in enumerate(lines):
            line_surface = font.render(line, True, color)
            surface.blit(line_surface, (x, y + i * font.get_linesize()))
            
    def _draw(self):
        """Draw all elements to the screen."""
        self.screen.fill(BLACK)

        # Draw code display area if showing code
        if self.state == "DISPLAY_CODE" and self.code_to_display:
            code_area_rect = pygame.Rect(50, 120, WIDTH - 100, HEIGHT - 180)
            pygame.draw.rect(self.screen, CODE_BG, code_area_rect)
            pygame.draw.rect(self.screen, ORB_COLOR_CODING, code_area_rect, 1) # Border
            self._draw_text_multiline(self.screen, self.code_to_display, code_area_rect.x + 15, code_area_rect.y + 15, self.code_font, WHITE)

        # Draw the orb (adjust position based on state)
        orb_y = HEIGHT // 2 if self.state != "DISPLAY_CODE" else 60
        pygame.draw.circle(self.screen, self.orb_color, (WIDTH // 2, orb_y), int(self.orb_radius))

        # Draw state text
        state_surface = self.font.render(self.state, True, WHITE)
        self.screen.blit(state_surface, (10, 10))

        # Draw speaking text (if not showing code)
        if self.speaking_text and self.state != "DISPLAY_CODE":
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
        
        self.comm_queue.put({"state": "SHUTDOWN"})
        pygame.quit()
        sys.exit()

if __name__ == '__main__':
    # Example of running the GUI standalone for testing
    q = queue.Queue()
    
    def test_backend(q):
        import time
        time.sleep(2)
        q.put({"state": "LISTENING"})
        time.sleep(2)
        q.put({"state": "SPEAKING", "text": "Generating code for a prime number function..."})
        time.sleep(3)
        code_snippet = "def is_prime(n):\n    if n <= 1:\n        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True"
        q.put({"state": "DISPLAY_CODE", "code": code_snippet})
        time.sleep(8)
        q.put({"state": "IDLE"})

    threading.Thread(target=test_backend, args=(q,), daemon=True).start()
    
    visualizer = Visualizer(q)
    visualizer.run()