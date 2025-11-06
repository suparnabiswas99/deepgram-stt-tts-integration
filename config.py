"""
Centralized configuration for Deepgram TTS & STT Demo
Handles environment variable loading and API key management
"""

import os
from dotenv import load_dotenv


class Config:
    """Centralized configuration class for Deepgram API"""
    
    def __init__(self):
        """Initialize configuration by loading environment variables"""
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key from environment
        self.api_key = os.getenv('DEEPGRAM_API_KEY')
        
        # Validate API key
        if not self.api_key:
            raise ValueError(
                "Deepgram API key is required. Set DEEPGRAM_API_KEY environment variable."
            )
    
    def get_api_key(self) -> str:
        """
        Get the Deepgram API key
        
        Returns:
            str: The API key
            
        Raises:
            ValueError: If API key is not set
        """
        if not self.api_key:
            raise ValueError(
                "Deepgram API key is required. Set DEEPGRAM_API_KEY environment variable."
            )
        return self.api_key
    
    def validate_setup(self) -> bool:
        """
        Validate that the configuration is properly set up
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        try:
            self.get_api_key()
            return True
        except ValueError:
            return False


# Global config instance
config = Config()


def get_api_key() -> str:
    """
    Convenience function to get the API key from the global config
    
    Returns:
        str: The Deepgram API key
    """
    return config.get_api_key()


def validate_config() -> bool:
    """
    Convenience function to validate the configuration
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    return config.validate_setup()
