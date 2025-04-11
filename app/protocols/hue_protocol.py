"""
Philips Hue protocol implementation
"""

import logging
import json
import time
import requests
from requests.exceptions import RequestException, Timeout

from ..constants import (
    APP_NAME, ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, ATTR_HUE, 
    ATTR_SATURATION, ATTR_RGB_COLOR, HUE_BRIDGE_DISCOVERY_URL,
    NETWORK_TIMEOUT, HUE_RANGE, SATURATION_RANGE, BRIGHTNESS_RANGE
)
from .protocol_base import ProtocolBase
from .utils import rgb_to_xy, xy_to_rgb


logger = logging.getLogger(APP_NAME)


class HueProtocol(ProtocolBase):
    """
    Protocol implementation for Philips Hue lighting system
    Handles communication with Hue bridges and light bulbs
    """
    
    def discover_bridges(self, timeout=NETWORK_TIMEOUT):
        """
        Discover Hue bridges on the network
        
        Args:
            timeout: Discovery timeout in seconds
            
        Returns:
            list: List of discovered bridge dictionaries
        """
        bridges = []
        
        try:
            # Method 1: Use Philips discovery service
            try:
                logger.info("Discovering Hue bridges via Philips discovery service")
                response = requests.get(
                    HUE_BRIDGE_DISCOVERY_URL,
                    timeout=timeout
                )
                if response.status_code == 200:
                    for bridge in response.json():
                        if 'internalipaddress' in bridge:
                            bridges.append({
                                'id': bridge.get('id', ''),
                                'ip': bridge['internalipaddress'],
                                'name': 'Philips Hue Bridge'
                            })
            except (RequestException, ValueError) as e:
                logger.warning(f"Error using Philips discovery service: {str(e)}")
            
            # Method 2: Try mDNS/UPnP discovery if no bridges found
            if not bridges:
                # In a real implementation, we would use additional discovery methods here
                # Such as mDNS/Bonjour or UPnP
                logger.info("No bridges found via Philips discovery, would try mDNS/UPnP here")
            
            # For each bridge, try to get more information
            for bridge in bridges:
                try:
                    if 'ip' in bridge:
                        # Get bridge info from the API
                        response = requests.get(
                            f"http://{bridge['ip']}/api/config",
                            timeout=timeout
                        )
                        if response.status_code == 200:
                            bridge_info = response.json()
                            # Update bridge information
                            if 'name' in bridge_info:
                                bridge['name'] = bridge_info['name']
                            if 'bridgeid' in bridge_info and 'id' not in bridge:
                                bridge['id'] = bridge_info['bridgeid']
                            if 'modelid' in bridge_info:
                                bridge['model'] = bridge_info['modelid']
                            if 'swversion' in bridge_info:
                                bridge['firmware'] = bridge_info['swversion']
                            bridge['manufacturer'] = 'Philips Hue'
                except RequestException as e:
                    logger.warning(f"Error getting info for bridge at {bridge.get('ip')}: {str(e)}")
            
            logger.info(f"Discovered {len(bridges)} Hue bridge(s)")
            return bridges
            
        except Exception as e:
            self.handle_error("bridge discovery", e)
            return []
    
    def discover_devices(self, timeout=NETWORK_TIMEOUT):
        """
        Discover Hue devices (bridges) on the network
        
        Args:
            timeout: Discovery timeout in seconds
            
        Returns:
            list: List of discovered device dictionaries
        """
        return self.discover_bridges(timeout)
    
    def connect(self, bridge_info):
        """
        Connect to a Hue bridge
        
        Args:
            bridge_info: Bridge information dictionary
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        if 'ip' not in bridge_info:
            logger.error("Cannot connect to Hue bridge: No IP address provided")
            return False
        
        ip = bridge_info['ip']
        
        try:
            # Check if we already have a username
            if 'username' in bridge_info:
                # Try to use existing username
                response = requests.get(
                    f"http://{ip}/api/{bridge_info['username']}",
                    timeout=NETWORK_TIMEOUT
                )
                if response.status_code == 200:
                    data = response.json()
                    if not isinstance(data, list) or 'error' not in data[0]:
                        logger.info(f"Connected to Hue bridge at {ip} with existing credentials")
                        return True
            
            # Need to create a new user
            # Note: In a real application, this would require user interaction
            # to press the link button on the bridge
            logger.info(f"Need to create new user for Hue bridge at {ip}")
            logger.info("NOTE: User would need to press the link button on the physical bridge")
            
            # This would normally wait for user confirmation that the button was pressed
            # For demo purposes, we'll just try to create a user
            
            response = requests.post(
                f"http://{ip}/api",
                json={"devicetype": "smart_light_controller#windows"},
                timeout=NETWORK_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and 'success' in data[0]:
                    username = data[0]['success']['username']
                    logger.info(f"Created new user for Hue bridge: {username}")
                    bridge_info['username'] = username
                    return True
                elif isinstance(data, list) and 'error' in data[0]:
                    error = data[0]['error']
                    if error['type'] == 101:  # Link button not pressed
                        logger.error("Link button not pressed on Hue bridge")
                    else:
                        logger.error(f"Hue bridge error: {error['description']}")
            
            return False
            
        except Exception as e:
            self.handle_error("bridge connection", e)
            return False
    
    def get_lights(self, bridge_ip, username):
        """
        Get list of lights from a Hue bridge
        
        Args:
            bridge_ip: IP address of the bridge
            username: Bridge username/API key
            
        Returns:
            dict: Dictionary of lights (ID -> light info)
        """
        try:
            response = requests.get(
                f"http://{bridge_ip}/api/{username}/lights",
                timeout=NETWORK_TIMEOUT
            )
            
            if response.status_code == 200:
                lights_data = response.json()
                
                # Process lights data
                lights = {}
                for light_id, light_data in lights_data.items():
                    # Convert to standardized format
                    normalized = {
                        'id': light_id,
                        'name': light_data.get('name', f'Light {light_id}'),
                        'type': light_data.get('type', 'Unknown'),
                        'model': light_data.get('modelid', 'Unknown'),
                        'manufacturer': light_data.get('manufacturername', 'Philips Hue'),
                        'protocol': 'hue'
                    }
                    
                    # Add state information
                    state = light_data.get('state', {})
                    normalized_state = self.normalize_state(state)
                    normalized['state'] = normalized_state
                    
                    lights[light_id] = normalized
                
                logger.info(f"Retrieved {len(lights)} lights from Hue bridge at {bridge_ip}")
                return lights
            
            logger.error(f"Failed to get lights from Hue bridge: {response.status_code}")
            return {}
            
        except Exception as e:
            self.handle_error("getting lights", e)
            return {}
    
    def get_light_state(self, bridge_ip, username, light_id):
        """
        Get the current state of a Hue light
        
        Args:
            bridge_ip: IP address of the bridge
            username: Bridge username/API key
            light_id: Light identifier
            
        Returns:
            dict: Light state dictionary
        """
        try:
            response = requests.get(
                f"http://{bridge_ip}/api/{username}/lights/{light_id}",
                timeout=NETWORK_TIMEOUT
            )
            
            if response.status_code == 200:
                light_data = response.json()
                if 'state' in light_data:
                    return self.normalize_state(light_data['state'])
            
            logger.error(f"Failed to get light state: {response.status_code}")
            return {}
            
        except Exception as e:
            self.handle_error("getting light state", e)
            return {}
    
    def set_light_state(self, bridge_ip, username, light_id, state):
        """
        Set the state of a Hue light
        
        Args:
            bridge_ip: IP address of the bridge
            username: Bridge username/API key
            light_id: Light identifier
            state: State dictionary with values to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert state to Hue API format
            hue_state = self._convert_to_hue_state(state)
            
            response = requests.put(
                f"http://{bridge_ip}/api/{username}/lights/{light_id}/state",
                json=hue_state,
                timeout=NETWORK_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                # Check if there were any errors
                for item in result:
                    if 'error' in item:
                        logger.error(f"Hue API error: {item['error']['description']}")
                        return False
                
                return True
            
            logger.error(f"Failed to set light state: {response.status_code}")
            return False
            
        except Exception as e:
            self.handle_error("setting light state", e)
            return False
    
    def normalize_state(self, state):
        """
        Normalize Hue state values to standard format
        
        Args:
            state: Hue API state dictionary
            
        Returns:
            dict: Normalized state dictionary
        """
        normalized = {}
        
        # Convert on/off state
        if 'on' in state:
            normalized['on'] = bool(state['on'])
        
        # Convert reachable state
        if 'reachable' in state:
            normalized['reachable'] = bool(state['reachable'])
        
        # Convert brightness (0-254 to 0-100%)
        if 'bri' in state:
            bri = state['bri']
            normalized['brightness'] = int((bri / BRIGHTNESS_RANGE[1]) * 100)
        
        # Convert color temperature (mirek to kelvin)
        if 'ct' in state:
            # Hue uses mirek (mired), which is 1,000,000/kelvin
            mirek = state['ct']
            if mirek > 0:
                normalized['color_temp'] = int(1000000 / mirek)
        
        # Convert color (xy to rgb)
        if 'xy' in state:
            xy = state['xy']
            if len(xy) == 2:
                rgb = xy_to_rgb(xy[0], xy[1])
                normalized['rgb_color'] = rgb
        
        # Convert hue and saturation
        if 'hue' in state and 'sat' in state:
            hue = state['hue']
            sat = state['sat']
            normalized['hue'] = int((hue / HUE_RANGE[1]) * 360)
            normalized['saturation'] = int((sat / SATURATION_RANGE[1]) * 100)
        
        return normalized
    
    def _convert_to_hue_state(self, state):
        """
        Convert generic state values to Hue API format
        
        Args:
            state: Generic state dictionary
            
        Returns:
            dict: Hue API state dictionary
        """
        hue_state = {}
        
        # Convert on/off state
        if 'on' in state:
            hue_state['on'] = bool(state['on'])
        
        # Convert brightness (0-100% to 0-254)
        if ATTR_BRIGHTNESS in state:
            bri = state[ATTR_BRIGHTNESS]
            hue_state['bri'] = int((bri / 100) * BRIGHTNESS_RANGE[1])
        
        # Convert color temperature (kelvin to mirek)
        if ATTR_COLOR_TEMP in state:
            kelvin = state[ATTR_COLOR_TEMP]
            if kelvin > 0:
                hue_state['ct'] = int(1000000 / kelvin)
        
        # Convert RGB color to xy
        if ATTR_RGB_COLOR in state:
            rgb = state[ATTR_RGB_COLOR]
            if len(rgb) == 3:
                xy = rgb_to_xy(rgb[0], rgb[1], rgb[2])
                hue_state['xy'] = xy
        
        # Convert hue and saturation
        if ATTR_HUE in state and ATTR_SATURATION in state:
            hue = state[ATTR_HUE]
            sat = state[ATTR_SATURATION]
            hue_state['hue'] = int((hue / 360) * HUE_RANGE[1])
            hue_state['sat'] = int((sat / 100) * SATURATION_RANGE[1])
        
        return hue_state
