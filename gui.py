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
WIDTH, HEIGHT = 900, 700  # Increased size for code display
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
ORB_PULSE_SPEED = 0.1 # This was for speaking animation, now combined with orb_radius

class Visualizer:
    """
    Manages the Pygame GUI window and all animations.
    """
    def __init__(self, comm_queue: queue.Queue):
        pygame.init()
        # Increased size for code display and overall aesthetic
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Jarvis")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28) # Default font
        self.code_font = pygame.font.SysFont("Consolas", 18) # Code specific font

        self.comm_queue = comm_queue
        
        # State
        self.state = "IDLE"  # IDLE, LISTENING, SPEAKING, DISPLAY_CODE
        self.speaking_text = ""
        self.code_to_display = ""
        self.code_lines = []

        # Animation variables
        self.angle = 0
        self.orb_radius = ORB_RADIUS_MIN
        self.current_orb_color = ORB_COLOR_IDLE # For smooth transitions
        self.speaking_pulse = 0
        self.current_glow_alpha = 0 # For orb glow effect

        # Code display scrolling
        self.code_scroll_offset = 0
        self.code_display_rect = pygame.Rect(50, 120, WIDTH - 100, HEIGHT - 180)
        self.line_height = self.code_font.get_linesize()
        self.visible_lines_count = self.code_display_rect.height // self.line_height
        self.max_code_scroll_offset = 0

    def _check_queue(self):
        """Check for messages from the backend bot."""
        try:
            message = self.comm_queue.get_nowait()
            new_state = message.get("state")
            if new_state:
                print(f"[GUI] State change: {new_state}")
                self.state = new_state
                self.angle = 0 # Reset animation angle on state change
                
                # Reset display texts
                self.speaking_text = ""
                self.code_to_display = ""
                self.code_lines = []
                self.code_scroll_offset = 0 # Reset scroll
                
                if self.state == "SPEAKING":
                    self.speaking_text = message.get("text", "")
                    self.speaking_pulse = 1.0
                elif self.state == "DISPLAY_CODE":
                    self.code_to_display = message.get("code", "")
                    self.code_lines = self.code_to_display.splitlines()
                    self.max_code_scroll_offset = max(0, len(self.code_lines) - self.visible_lines_count)
                    
        except queue.Empty:
            pass

    def _update_animations(self):
        """Update animation values based on the current state."""
        self.angle += ORB_BREATHE_SPEED

        target_color = ORB_COLOR_IDLE
        if self.state == "IDLE":
            target_color = ORB_COLOR_IDLE
            self.orb_radius = ORB_RADIUS_MIN + (ORB_RADIUS_MAX - ORB_RADIUS_MIN) * (0.5 * (1 + math.sin(self.angle)))
            self.current_glow_alpha = max(0, self.current_glow_alpha - 5)
        
        elif self.state == "LISTENING":
            target_color = ORB_COLOR_LISTENING
            self.orb_radius = ORB_RADIUS_MAX + 5 * (0.5 * (1 + math.sin(self.angle * 2))) # More pronounced pulse
            self.current_glow_alpha = min(150, self.current_glow_alpha + 10) # Brighter glow
        
        elif self.state == "SPEAKING":
            target_color = ORB_COLOR_SPEAKING
            if self.speaking_pulse > 0:
                self.speaking_pulse -= 0.02
            self.orb_radius = ORB_RADIUS_MIN + (ORB_RADIUS_MAX - ORB_RADIUS_MIN) * self.speaking_pulse * 1.5 # Stronger pulse
            self.current_glow_alpha = min(100, self.current_glow_alpha + 5)
            
        elif self.state == "DISPLAY_CODE":
            target_color = ORB_COLOR_CODING
            self.orb_radius = ORB_RADIUS_MIN # Static size
            self.current_glow_alpha = max(0, self.current_glow_alpha - 5)

        # Smooth color transition (linear interpolation)
        self.current_orb_color = tuple(
            int(self.current_orb_color[i] * 0.9 + target_color[i] * 0.1) for i in range(3)
        )
            
    def _draw_text_multiline_scrollable(self, surface, lines, rect, font, color, scroll_offset):
        """Helper to draw multi-line text with scrolling."""
        y_offset = rect.y + 10
        # Calculate start and end indices for visible lines
        start_line_index = scroll_offset
        end_line_index = min(scroll_offset + self.visible_lines_count, len(lines))
        
        for i in range(start_line_index, end_line_index):
            line_surface = font.render(lines[i], True, color)
            surface.blit(line_surface, (rect.x + 10, y_offset))
            y_offset += font.get_linesize()

    def _draw(self):
        """Draw all elements to the screen."""
        self.screen.fill(BLACK)

        # Draw code display area if showing code
        if self.state == "DISPLAY_CODE" and self.code_to_display:
            pygame.draw.rect(self.screen, CODE_BG, self.code_display_rect)
            pygame.draw.rect(self.screen, self.current_orb_color, self.code_display_rect, 2) # Thicker, animated border

            # Draw scrollbar
            if self.max_code_scroll_offset > 0:
                scrollbar_track_rect = pygame.Rect(self.code_display_rect.right - 15, self.code_display_rect.y, 10, self.code_display_rect.height)
                pygame.draw.rect(self.screen, (50, 50, 50), scrollbar_track_rect, 0, 5) # Darker track

                scrollbar_height_ratio = self.visible_lines_count / len(self.code_lines)
                actual_scrollbar_height = max(20, int(scrollbar_height_ratio * self.code_display_rect.height)) # Min height
                
                scrollbar_y_ratio = self.code_scroll_offset / self.max_code_scroll_offset
                scrollbar_y = self.code_display_rect.y + (self.code_display_rect.height - actual_scrollbar_height) * scrollbar_y_ratio

                scrollbar_thumb_rect = pygame.Rect(self.code_display_rect.right - 15, scrollbar_y, 10, actual_scrollbar_height)
                pygame.draw.rect(self.screen, self.current_orb_color, scrollbar_thumb_rect, 0, 5) # Draw scrollbar thumb

            self._draw_text_multiline_scrollable(self.screen, self.code_lines, self.code_display_rect, self.code_font, WHITE, self.code_scroll_offset)

        # Draw the orb (adjust position based on state)
        orb_y = HEIGHT // 2 if self.state != "DISPLAY_CODE" else 60
        pygame.draw.circle(self.screen, self.current_orb_color, (WIDTH // 2, orb_y), int(self.orb_radius))
        
        # Draw orb glow
        if self.current_glow_alpha > 0:
            glow_surface = pygame.Surface((self.orb_radius * 2 + 20, self.orb_radius * 2 + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*self.current_orb_color, self.current_glow_alpha), (self.orb_radius + 10, self.orb_radius + 10), int(self.orb_radius * 0.9 + 5))
            glow_rect = glow_surface.get_rect(center=(WIDTH // 2, orb_y))
            self.screen.blit(glow_surface, glow_rect)


        # Draw state text
        state_surface = self.font.render(f"State: {self.state}", True, WHITE)
        self.screen.blit(state_surface, (10, 10))

        # Draw speaking text (if not showing code)
        if self.speaking_text and self.state not in ["DISPLAY_CODE"]:
            text_surface = self.font.render(self.speaking_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT - 40))
            self.screen.blit(text_surface, text_rect)
        elif self.state == "DISPLAY_CODE":
            # Display current command or instruction above code
            instruction_surface = self.font.render("Use mouse wheel to scroll code.", True, WHITE)
            instruction_rect = instruction_surface.get_rect(center=(WIDTH // 2, 90))
            self.screen.blit(instruction_surface, instruction_rect)


        pygame.display.flip()

    def run(self):
        """The main loop of the GUI."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and self.state == "DISPLAY_CODE":
                    if event.button == 4: # Scroll up
                        self.code_scroll_offset = max(0, self.code_scroll_offset - 1)
                    elif event.button == 5: # Scroll down
                        self.code_scroll_offset = min(self.max_code_scroll_offset, self.code_scroll_offset + 1)
            
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
        code_snippet = """def is_prime(n):
    '''Checks if a number is prime.'''
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

# Example usage:
print(is_prime(7))   # Output: True
print(is_prime(10))  # Output: False
print(is_prime(1))   # Output: False
print(is_prime(2))   # Output: True
"""
        q.put({"state": "DISPLAY_CODE", "code": code_snippet})
        time.sleep(8)
        q.put({"state": "IDLE"})

    threading.Thread(target=test_backend, args=(q,), daemon=True).start() 
    
    visualizer = Visualizer(q)
    visualizer.run()
