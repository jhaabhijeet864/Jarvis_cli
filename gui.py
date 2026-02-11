"""
Jarvis Voice Assistant GUI
Creates a visualizer window with an animated orb that reflects the assistant's state.
"""
import pygame
import sys
import math
import threading
import queue
import logging

# --- Constants ---
# Colors are kept here as they are visual design choices, not really user settings.
BLACK = (10, 10, 20)
WHITE = (230, 230, 230)
CODE_BG = (20, 20, 30)
ORB_COLOR_IDLE = (0, 100, 255)       # Blue
ORB_COLOR_LISTENING = (100, 255, 100) # Green
ORB_COLOR_THINKING = (255, 255, 100)   # Yellow
ORB_COLOR_SPEAKING = (255, 100, 0)    # Orange
ORB_COLOR_CODING = (160, 32, 240)     # Purple

# Get loggers
main_logger = logging.getLogger('main')
error_logger = logging.getLogger('errors')

class Visualizer:
    """
    Manages the Pygame GUI window and all animations.
    """
    def __init__(self, comm_queue: queue.Queue, settings):
        main_logger.info("Initializing GUI Visualizer.")
        self.settings = settings
        pygame.init()

        # Load settings
        self.width = self.settings.get('gui.width', 900)
        self.height = self.settings.get('gui.height', 700)
        self.fps = self.settings.get('gui.fps', 60)

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Jarvis")
        self.clock = pygame.time.Clock()
        
        try:
            self.font = pygame.font.Font(None, 28) # Default font
            self.code_font = pygame.font.SysFont("Consolas", 18) # Code specific font
        except pygame.error as e:
            error_logger.critical(f"Pygame font error: {e}. Check if fonts are available.", exc_info=True)
            raise

        self.comm_queue = comm_queue
        
        # State
        self.state = "IDLE"  # IDLE, LISTENING, SPEAKING, DISPLAY_CODE
        self.speaking_text = ""
        self.code_to_display = ""
        self.code_lines = []

        # Animation variables from settings
        self.orb_radius_min = self.settings.get('gui.orb_radius_min', 30)
        self.orb_radius_max = self.settings.get('gui.orb_radius_max', 40)
        self.orb_breathe_speed = self.settings.get('gui.orb_breathe_speed', 0.02)
        
        self.angle = 0
        self.orb_radius = self.orb_radius_min
        self.current_orb_color = ORB_COLOR_IDLE
        self.speaking_pulse = 0
        self.current_glow_alpha = 0

        # Code display scrolling
        self.code_scroll_offset = 0
        self.code_display_rect = pygame.Rect(50, 120, self.width - 100, self.height - 180)
        self.line_height = self.code_font.get_linesize()
        self.visible_lines_count = self.code_display_rect.height // self.line_height
        self.max_code_scroll_offset = 0
        main_logger.info("GUI Visualizer initialized successfully.")

    def _check_queue(self):
        """Check for messages from the backend bot."""
        try:
            message = self.comm_queue.get_nowait()
            new_state = message.get("state")
            if new_state == "SHUTDOWN":
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return

            if new_state:
                main_logger.info(f"GUI received state change: {new_state}")
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
                    if self.code_to_display:
                        self.code_lines = self.code_to_display.splitlines()
                        self.max_code_scroll_offset = max(0, len(self.code_lines) - self.visible_lines_count)
                    
        except queue.Empty:
            pass

    def _update_animations(self):
        """Update animation values based on the current state."""
        self.angle += self.orb_breathe_speed

        target_color = ORB_COLOR_IDLE
        if self.state == "IDLE":
            target_color = ORB_COLOR_IDLE
            self.orb_radius = self.orb_radius_min + (self.orb_radius_max - self.orb_radius_min) * (0.5 * (1 + math.sin(self.angle)))
            self.current_glow_alpha = max(0, self.current_glow_alpha - 5)
        
        elif self.state == "LISTENING":
            target_color = ORB_COLOR_LISTENING
            self.orb_radius = self.orb_radius_max + 5 * (0.5 * (1 + math.sin(self.angle * 2)))
            self.current_glow_alpha = min(150, self.current_glow_alpha + 10)
        
        elif self.state == "THINKING":
            target_color = ORB_COLOR_THINKING
            self.orb_radius = self.orb_radius_min + (self.orb_radius_max - self.orb_radius_min) * (0.5 * (1 + math.sin(self.angle * 4)))
            self.current_glow_alpha = min(200, self.current_glow_alpha + 15)

        elif self.state == "SPEAKING":
            target_color = ORB_COLOR_SPEAKING
            if self.speaking_pulse > 0:
                self.speaking_pulse -= 0.02
            self.orb_radius = self.orb_radius_min + (self.orb_radius_max - self.orb_radius_min) * self.speaking_pulse * 1.5
            self.current_glow_alpha = min(100, self.current_glow_alpha + 5)
            
        elif self.state == "DISPLAY_CODE":
            target_color = ORB_COLOR_CODING
            self.orb_radius = self.orb_radius_min
            self.current_glow_alpha = max(0, self.current_glow_alpha - 5)

        # Smooth color transition (linear interpolation)
        self.current_orb_color = tuple(
            int(self.current_orb_color[i] * 0.9 + target_color[i] * 0.1) for i in range(3)
        )
            
    def _draw_text_multiline_scrollable(self, surface, lines, rect, font, color, scroll_offset):
        """Helper to draw multi-line text with scrolling."""
        y_offset = rect.y + 10
        start_line_index = int(scroll_offset)
        end_line_index = min(int(scroll_offset) + self.visible_lines_count, len(lines))
        
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
            pygame.draw.rect(self.screen, self.current_orb_color, self.code_display_rect, 2)

            if len(self.code_lines) > self.visible_lines_count:
                scrollbar_track_rect = pygame.Rect(self.code_display_rect.right - 15, self.code_display_rect.y, 10, self.code_display_rect.height)
                pygame.draw.rect(self.screen, (50, 50, 50), scrollbar_track_rect, 0, 5)

                scrollbar_height_ratio = self.visible_lines_count / len(self.code_lines)
                actual_scrollbar_height = max(20, int(scrollbar_height_ratio * self.code_display_rect.height))
                
                scrollbar_y_ratio = self.code_scroll_offset / self.max_code_scroll_offset
                scrollbar_y = self.code_display_rect.y + (self.code_display_rect.height - actual_scrollbar_height) * scrollbar_y_ratio

                scrollbar_thumb_rect = pygame.Rect(self.code_display_rect.right - 15, scrollbar_y, 10, actual_scrollbar_height)
                pygame.draw.rect(self.screen, self.current_orb_color, scrollbar_thumb_rect, 0, 5)

            self._draw_text_multiline_scrollable(self.screen, self.code_lines, self.code_display_rect, self.code_font, WHITE, self.code_scroll_offset)

        orb_y = self.height // 2 if self.state != "DISPLAY_CODE" else 60
        pygame.draw.circle(self.screen, self.current_orb_color, (self.width // 2, orb_y), int(self.orb_radius))
        
        if self.current_glow_alpha > 0:
            glow_surface = pygame.Surface((self.orb_radius * 2 + 20, self.orb_radius * 2 + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*self.current_orb_color, self.current_glow_alpha), (self.orb_radius + 10, self.orb_radius + 10), int(self.orb_radius * 0.9 + 5))
            glow_rect = glow_surface.get_rect(center=(self.width // 2, orb_y))
            self.screen.blit(glow_surface, glow_rect)

        state_surface = self.font.render(f"State: {self.state}", True, WHITE)
        self.screen.blit(state_surface, (10, 10))

        if self.speaking_text and self.state not in ["DISPLAY_CODE"]:
            text_surface = self.font.render(self.speaking_text, True, WHITE)
            text_rect = text_surface.get_rect(center=(self.width // 2, self.height - 40))
            self.screen.blit(text_surface, text_rect)
        elif self.state == "DISPLAY_CODE":
            instruction_surface = self.font.render("Use mouse wheel to scroll code.", True, WHITE)
            instruction_rect = instruction_surface.get_rect(center=(self.width // 2, 90))
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
                    if self.max_code_scroll_offset > 0:
                        if event.button == 4: # Scroll up
                            self.code_scroll_offset = max(0, self.code_scroll_offset - 1)
                        elif event.button == 5: # Scroll down
                            self.code_scroll_offset = min(self.max_code_scroll_offset, self.code_scroll_offset + 1)
            
            self._check_queue()
            self._update_animations()
            self._draw()
            
            self.clock.tick(self.fps)
        
        main_logger.info("GUI is shutting down.")
        # Don't send shutdown message here, main loop handles it.
        pygame.quit()
        # Don't call sys.exit() here, let the main thread exit gracefully.

