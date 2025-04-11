"""
Light Manager for handling all light devices across different protocols
"""

import logging
import uuid
import threading
from PySide6.QtCore import QObject, Signal

from .constants import APP_NAME, PROTOCOL_HUE, PROTOCOL_LIFX
from .protocols.hue_protocol import HueProtocol
from .protocols.lifx_protocol import LifxProtocol


logger = logging.getLogger(APP_NAME)


class LightManager(QObject):
    """
    Manages all smart light devices across different protocols
    Provides a unified interface for controlling lights
    """
    
    # Signals
    devices_updated = Signal()  # Emitted when the device list changes
    light_state_changed = Signal(str, str, dict)  # Protocol, light ID, new state
    
    def __init__(self, config_manager):
        """Initialize the light manager with configuration manager"""
        super().__init__()
        self.config_manager = config_manager
        
        # Initialize protocol handlers
        self.hue = HueProtocol()
        self.lifx = LifxProtocol()
        
        # Device tracking
        self.hue_bridges = {}  # Bridge ID -> bridge info
        self.hue_lights = {}   # Light ID -> light info
        self.lifx_lights = {}  # Light ID -> light info
        
        # Lock for thread safety
        self.lock = threading.RLock()
    
    def add_hue_bridge(self, bridge_info):
        """
        Add or update a Hue bridge
        
        Args:
            bridge_info: Dictionary with bridge information
            
        Returns:
            bool: True if bridge was added/updated, False otherwise
        """
        with self.lock:
            if 'id' not in bridge_info:
                logger.error("Cannot add Hue bridge without ID")
                return False
            
            bridge_id = bridge_info['id']
            
            # Check if bridge already exists
            if bridge_id in self.hue_bridges:
                logger.info(f"Updating existing Hue bridge: {bridge_id}")
                self.hue_bridges[bridge_id].update(bridge_info)
            else:
                logger.info(f"Adding new Hue bridge: {bridge_id}")
                self.hue_bridges[bridge_id] = bridge_info
            
            # Save to configuration
            self.config_manager.add_device(PROTOCOL_HUE, bridge_info)
            
            # Try to connect to bridge and get lights
            try:
                # Connect to bridge if IP address and username are available
                if 'ip' in bridge_info and 'username' in bridge_info:
                    lights = self.hue.get_lights(bridge_info['ip'], bridge_info['username'])
                    
                    # Add lights to the manager
                    for light_id, light_data in lights.items():
                        # Add bridge reference to light data
                        light_data['bridge_id'] = bridge_id
                        
                        # Add unique ID combining bridge and light IDs
                        unique_id = f"{bridge_id}_{light_id}"
                        light_data['id'] = unique_id
                        
                        # Add protocol identifier
                        light_data['protocol'] = PROTOCOL_HUE
                        
                        # Store light
                        self.hue_lights[unique_id] = light_data
                        
                        # Emit signal for state change
                        self.light_state_changed.emit(PROTOCOL_HUE, unique_id, light_data)
                    
                    logger.info(f"Added {len(lights)} lights from Hue bridge {bridge_id}")
                
                self.devices_updated.emit()
                return True
                
            except Exception as e:
                logger.error(f"Error connecting to Hue bridge {bridge_id}: {str(e)}")
                return False
    
    def add_lifx_light(self, light_info):
        """
        Add or update a LIFX light
        
        Args:
            light_info: Dictionary with light information
            
        Returns:
            bool: True if light was added/updated, False otherwise
        """
        with self.lock:
            if 'id' not in light_info:
                logger.error("Cannot add LIFX light without ID")
                return False
            
            light_id = light_info['id']
            
            # Add protocol identifier if not present
            if 'protocol' not in light_info:
                light_info['protocol'] = PROTOCOL_LIFX
            
            # Check if light already exists
            if light_id in self.lifx_lights:
                logger.info(f"Updating existing LIFX light: {light_id}")
                self.lifx_lights[light_id].update(light_info)
            else:
                logger.info(f"Adding new LIFX light: {light_id}")
                self.lifx_lights[light_id] = light_info
            
            # Try to connect to the light and update its state
            try:
                # Get current state if MAC address or IP is available
                if 'mac' in light_info or 'ip' in light_info:
                    state = self.lifx.get_light_state(light_info)
                    if state:
                        self.lifx_lights[light_id].update(state)
                
                # Save to configuration
                self.config_manager.add_device(PROTOCOL_LIFX, self.lifx_lights[light_id])
                
                # Emit signals
                self.light_state_changed.emit(PROTOCOL_LIFX, light_id, self.lifx_lights[light_id])
                self.devices_updated.emit()
                
                return True
                
            except Exception as e:
                logger.error(f"Error connecting to LIFX light {light_id}: {str(e)}")
                return False
    
    def get_all_lights(self):
        """
        Get a dictionary of all lights across all protocols
        
        Returns:
            dict: Light ID -> light info
        """
        with self.lock:
            # Combine lights from all protocols
            all_lights = {}
            all_lights.update(self.hue_lights)
            all_lights.update(self.lifx_lights)
            return all_lights
    
    def get_light(self, protocol, light_id):
        """
        Get information for a specific light
        
        Args:
            protocol: Light protocol ('hue' or 'lifx')
            light_id: Light identifier
            
        Returns:
            dict: Light information or None if not found
        """
        with self.lock:
            if protocol == PROTOCOL_HUE:
                return self.hue_lights.get(light_id)
            elif protocol == PROTOCOL_LIFX:
                return self.lifx_lights.get(light_id)
            return None
    
    def set_light_state(self, protocol, light_id, state):
        """
        Set state for a specific light
        
        Args:
            protocol: Light protocol ('hue' or 'lifx')
            light_id: Light identifier
            state: Dictionary with state values to set
            
        Returns:
            bool: True if state was set successfully, False otherwise
        """
        with self.lock:
            try:
                if protocol == PROTOCOL_HUE:
                    # Get light and bridge info
                    light = self.hue_lights.get(light_id)
                    if not light or 'bridge_id' not in light:
                        logger.error(f"Cannot find Hue light or bridge for {light_id}")
                        return False
                    
                    bridge_id = light['bridge_id']
                    bridge = self.hue_bridges.get(bridge_id)
                    if not bridge or 'ip' not in bridge or 'username' not in bridge:
                        logger.error(f"Cannot find Hue bridge info for {bridge_id}")
                        return False
                    
                    # Extract the actual light ID on the bridge
                    actual_light_id = light_id.split('_')[1]
                    
                    # Set state via Hue protocol
                    success = self.hue.set_light_state(
                        bridge['ip'], 
                        bridge['username'],
                        actual_light_id,
                        state
                    )
                    
                    if success:
                        # Update local state
                        self.hue_lights[light_id].update(self.hue.normalize_state(state))
                        
                        # Emit signal
                        self.light_state_changed.emit(protocol, light_id, self.hue_lights[light_id])
                    
                    return success
                    
                elif protocol == PROTOCOL_LIFX:
                    # Get light info
                    light = self.lifx_lights.get(light_id)
                    if not light:
                        logger.error(f"Cannot find LIFX light {light_id}")
                        return False
                    
                    # Set state via LIFX protocol
                    success = self.lifx.set_light_state(light, state)
                    
                    if success:
                        # Update local state with normalized values
                        self.lifx_lights[light_id].update(self.lifx.normalize_state(state))
                        
                        # Emit signal
                        self.light_state_changed.emit(protocol, light_id, self.lifx_lights[light_id])
                    
                    return success
                
                else:
                    logger.error(f"Unsupported protocol: {protocol}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error setting state for {protocol} light {light_id}: {str(e)}")
                return False
    
    def refresh_light(self, protocol, light_id):
        """
        Refresh state for a specific light
        
        Args:
            protocol: Light protocol ('hue' or 'lifx')
            light_id: Light identifier
            
        Returns:
            bool: True if state was refreshed successfully, False otherwise
        """
        with self.lock:
            try:
                if protocol == PROTOCOL_HUE:
                    # Get light and bridge info
                    light = self.hue_lights.get(light_id)
                    if not light or 'bridge_id' not in light:
                        logger.error(f"Cannot find Hue light or bridge for {light_id}")
                        return False
                    
                    bridge_id = light['bridge_id']
                    bridge = self.hue_bridges.get(bridge_id)
                    if not bridge or 'ip' not in bridge or 'username' not in bridge:
                        logger.error(f"Cannot find Hue bridge info for {bridge_id}")
                        return False
                    
                    # Extract the actual light ID on the bridge
                    actual_light_id = light_id.split('_')[1]
                    
                    # Get updated state
                    state = self.hue.get_light_state(
                        bridge['ip'],
                        bridge['username'],
                        actual_light_id
                    )
                    
                    if state:
                        # Update local state
                        self.hue_lights[light_id].update(state)
                        
                        # Emit signal
                        self.light_state_changed.emit(protocol, light_id, self.hue_lights[light_id])
                        return True
                    
                    return False
                    
                elif protocol == PROTOCOL_LIFX:
                    # Get light info
                    light = self.lifx_lights.get(light_id)
                    if not light:
                        logger.error(f"Cannot find LIFX light {light_id}")
                        return False
                    
                    # Get updated state
                    state = self.lifx.get_light_state(light)
                    
                    if state:
                        # Update local state
                        self.lifx_lights[light_id].update(state)
                        
                        # Emit signal
                        self.light_state_changed.emit(protocol, light_id, self.lifx_lights[light_id])
                        return True
                    
                    return False
                
                else:
                    logger.error(f"Unsupported protocol: {protocol}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error refreshing state for {protocol} light {light_id}: {str(e)}")
                return False
    
    def refresh_all_devices(self):
        """
        Refresh state for all lights
        
        Returns:
            bool: True if all devices were refreshed successfully, False otherwise
        """
        with self.lock:
            success = True
            
            # Refresh Hue lights
            for light_id in self.hue_lights:
                if not self.refresh_light(PROTOCOL_HUE, light_id):
                    success = False
            
            # Refresh LIFX lights
            for light_id in self.lifx_lights:
                if not self.refresh_light(PROTOCOL_LIFX, light_id):
                    success = False
            
            return success
    
    def set_all_lights(self, on):
        """
        Turn all lights on or off
        
        Args:
            on: True to turn on, False to turn off
            
        Returns:
            bool: True if successful, False otherwise
        """
        with self.lock:
            success = True
            state = {'on': on}
            
            # Set state for Hue lights
            for light_id in self.hue_lights:
                if not self.set_light_state(PROTOCOL_HUE, light_id, state):
                    success = False
            
            # Set state for LIFX lights
            for light_id in self.lifx_lights:
                if not self.set_light_state(PROTOCOL_LIFX, light_id, state):
                    success = False
            
            return success
    
    def create_group(self, name, light_ids):
        """
        Create a new light group
        
        Args:
            name: Group name
            light_ids: List of (protocol, light_id) tuples
            
        Returns:
            str: Group ID if successful, None otherwise
        """
        # Generate a new group ID
        group_id = str(uuid.uuid4())
        
        # Create group info
        group_info = {
            'id': group_id,
            'name': name,
            'lights': light_ids
        }
        
        # Save to configuration
        if self.config_manager.add_group(group_info):
            self.devices_updated.emit()
            return group_id
        
        return None
    
    def update_group(self, group_id, name=None, light_ids=None):
        """
        Update an existing light group
        
        Args:
            group_id: Group ID
            name: New group name (optional)
            light_ids: New list of light IDs (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get existing group
        groups = self.config_manager.get_groups()
        group = next((g for g in groups if g['id'] == group_id), None)
        
        if not group:
            logger.error(f"Cannot find group {group_id}")
            return False
        
        # Update group info
        if name is not None:
            group['name'] = name
        
        if light_ids is not None:
            group['lights'] = light_ids
        
        # Save to configuration
        if self.config_manager.add_group(group):
            self.devices_updated.emit()
            return True
        
        return False
    
    def delete_group(self, group_id):
        """
        Delete a light group
        
        Args:
            group_id: Group ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.config_manager.remove_group(group_id):
            self.devices_updated.emit()
            return True
        
        return False
    
    def set_group_state(self, group_id, state):
        """
        Set state for all lights in a group
        
        Args:
            group_id: Group ID
            state: Dictionary with state values to set
            
        Returns:
            bool: True if successful for all lights, False otherwise
        """
        # Get group
        groups = self.config_manager.get_groups()
        group = next((g for g in groups if g['id'] == group_id), None)
        
        if not group or 'lights' not in group:
            logger.error(f"Cannot find group {group_id} or group has no lights")
            return False
        
        # Set state for each light in the group
        success = True
        
        for light_info in group['lights']:
            protocol, light_id = light_info
            if not self.set_light_state(protocol, light_id, state):
                success = False
        
        return success
    
    def get_connected_device_count(self):
        """
        Get the number of connected devices
        
        Returns:
            int: Number of connected devices
        """
        count = 0
        
        # Count Hue lights
        for light in self.hue_lights.values():
            if light.get('state', {}).get('reachable', False):
                count += 1
        
        # Count LIFX lights
        for light in self.lifx_lights.values():
            if light.get('state', {}).get('reachable', False):
                count += 1
        
        return count
    
    def get_total_device_count(self):
        """
        Get the total number of devices
        
        Returns:
            int: Total number of devices
        """
        return len(self.hue_lights) + len(self.lifx_lights)
