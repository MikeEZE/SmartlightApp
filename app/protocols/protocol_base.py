"""
Base protocol class for smart light communication
"""

import logging
from abc import ABC, abstractmethod

from ..constants import APP_NAME


logger = logging.getLogger(APP_NAME)


class ProtocolBase(ABC):
    """
    Abstract base class for all smart light protocols
    Defines the interface that all protocol implementations must follow
    """
    
    @abstractmethod
    def discover_devices(self, timeout=5):
        """
        Discover devices on the network
        
        Args:
            timeout: Discovery timeout in seconds
            
        Returns:
            list: List of discovered device dictionaries
        """
        pass
    
    @abstractmethod
    def connect(self, device_info):
        """
        Connect to a device
        
        Args:
            device_info: Device information dictionary
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_lights(self, *args, **kwargs):
        """
        Get list of lights from a device (e.g., a bridge)
        
        Args:
            Implementation-specific arguments
            
        Returns:
            dict: Dictionary of lights
        """
        pass
    
    @abstractmethod
    def get_light_state(self, *args, **kwargs):
        """
        Get the current state of a light
        
        Args:
            Implementation-specific arguments
            
        Returns:
            dict: Light state dictionary
        """
        pass
    
    @abstractmethod
    def set_light_state(self, *args, **kwargs):
        """
        Set the state of a light
        
        Args:
            Implementation-specific arguments
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def normalize_state(self, state):
        """
        Normalize state values to standard format
        
        Args:
            state: Protocol-specific state dictionary
            
        Returns:
            dict: Normalized state dictionary
        """
        pass
    
    def handle_error(self, action, error):
        """
        Handle and log protocol errors
        
        Args:
            action: Description of the action that failed
            error: Exception object or error message
        """
        error_msg = str(error)
        logger.error(f"Protocol error during {action}: {error_msg}")
        return error_msg
