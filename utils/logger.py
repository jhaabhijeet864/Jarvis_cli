import logging
from pathlib import Path

class JarvisLogger:
    """Centralized logging for debugging and monitoring."""
    
    def __init__(self, log_dir='logs'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create separate logs for different components
        self.setup_logger('main', 'main.log')
        self.setup_logger('stt', 'speech_recognition.log')
        self.setup_logger('commands', 'commands.log')
        self.setup_logger('llm', 'llm.log')
        self.setup_logger('errors', 'errors.log', level=logging.ERROR)
    
    def setup_logger(self, name, filename, level=logging.INFO):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # File handler
        log_file = self.log_dir / filename
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        
        # Console handler - only show warnings and above in console
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Avoid adding handlers multiple times
        if not logger.handlers:
            logger.addHandler(fh)
            logger.addHandler(ch)
        
        return logger

# Initialize the logger globally so it can be imported
JarvisLogger()
