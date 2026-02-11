import random

class JarvisResponses:
    """Natural, varied responses for better UX."""
    
    RESPONSES = {
        'greeting': [
            "Good day, sir.",
            "Hello, sir. Ready to assist.",
            "Jarvis online and at your service.",
        ],
        'open_app_success': [
            "Opening {app} now, sir.",
            "Launching {app}.",
            "{app} starting up.",
        ],
        'search_success': [
            "Searching {platform} for {query}.",
            "Here's what I found for {query} on {platform}.",
            "Running search on {platform}.",
        ],
        'error': [
            "I encountered an issue, sir. {error}",
            "My apologies, something went wrong. {error}",
            "Error detected: {error}",
        ],
        'not_understood': [
            "I didn't quite catch that, sir.",
            "Could you repeat that?",
            "I'm not sure I understood.",
        ],
    }
    
    def get(self, key, **kwargs):
        """Get a random response template and format it."""
        templates = self.RESPONSES.get(key, ["Understood, sir."])
        template = random.choice(templates)
        return template.format(**kwargs)
