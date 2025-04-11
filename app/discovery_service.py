"""
Discovery service for finding smart light devices on the network
"""

import logging
import threading
import time
from PySide6.QtCore import QObject, Signal

from .constants import APP_NAME, DISCOVERY_TIMEOUT
from .protocols.hue_protocol import HueProtocol
from .protocols.lifx_protocol import LifxProtocol


logger = logging.getLogger(APP_NAME)


class DiscoveryService(QObject):
    """
    Service for discovering smart light devices on the network
    Handles discovery for all supported protocols
    """
    
    # Signals
    discovery_started = Signal()
    discovery_finished = Signal(bool)  # Success flag
    device_discovered = Signal(str, dict)  # Protocol, device info
    
    def __init__(self, light_manager):
        """Initialize discovery service with light manager reference"""
        super().__init__()
        self.light_manager = light_manager
        self.discovery_active = False
        self.discovery_thread = None
        
        # Initialize protocol handlers
        self.hue = HueProtocol()
        self.lifx = LifxProtocol()
    
    def discover_devices(self):
        """Start device discovery in a background thread"""
        if self.discovery_active:
            logger.warning("Discovery already in progress")
            return False
        
        self.discovery_thread = threading.Thread(
            target=self._run_discovery,
            daemon=True
        )
        self.discovery_thread.start()
        return True
    
    def _run_discovery(self):
        """Run device discovery for all protocols (in background thread)"""
        self.discovery_active = True
        self.discovery_started.emit()
        
        logger.info("Starting device discovery")
        success = False
        
        try:
            # Discover Philips Hue bridges
            hue_success = self._discover_hue_devices()
            
            # Discover LIFX devices
            lifx_success = self._discover_lifx_devices()
            
            # Overall success if at least one protocol succeeded
            success = hue_success or lifx_success
            
        except Exception as e:
            logger.error(f"Error during device discovery: {str(e)}")
            success = False
        
        self.discovery_active = False
        self.discovery_finished.emit(success)
        logger.info(f"Device discovery completed: {'success' if success else 'failed'}")
    
    def _discover_hue_devices(self):
        """Discover Philips Hue bridges and lights"""
        logger.info("Discovering Hue bridges...")
        
        try:
            # Step 1: Find Hue bridges on the network
            bridges = self.hue.discover_bridges()
            
            if not bridges:
                logger.info("No Hue bridges found")
                return False
            
            logger.info(f"Found {len(bridges)} Hue bridge(s)")
            
            # Step 2: For each bridge, try to connect and get lights
            for bridge in bridges:
                # Add the bridge to the light manager
                bridge_added = self.light_manager.add_hue_bridge(bridge)
                
                if bridge_added:
                    # Emit signal for discovered bridge
                    self.device_discovered.emit('hue', bridge)
            
            return True
            
        except Exception as e:
            logger.error(f"Hue discovery error: {str(e)}")
            return False
    
    def _discover_lifx_devices(self):
        """Discover LIFX devices on the network"""
        logger.info("Discovering LIFX lights...")
        
        try:
            # Find LIFX lights on the network
            lights = self.lifx.discover_lights(timeout=DISCOVERY_TIMEOUT)
            
            if not lights:
                logger.info("No LIFX lights found")
                return False
            
            logger.info(f"Found {len(lights)} LIFX light(s)")
            
            # Add each light to the light manager
            for light in lights:
                light_added = self.light_manager.add_lifx_light(light)
                
                if light_added:
                    # Emit signal for discovered light
                    self.device_discovered.emit('lifx', light)
            
            return True
            
        except Exception as e:
            logger.error(f"LIFX discovery error: {str(e)}")
            return False
