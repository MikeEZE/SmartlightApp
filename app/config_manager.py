"""
Configuration management for the Smart Light Controller application
"""

import json
import logging
import os
from pathlib import Path

from .constants import CONFIG_FILE, APP_NAME

logger = logging.getLogger(APP_NAME)


class ConfigManager:
    """
    Manages application configuration, including saved lights, groups, and user preferences.
    Handles loading and saving configuration to disk.
    """
    
    def __init__(self):
        """Initialize configuration manager with default settings"""
        self.config = {
            'version': 1,
            'first_run': True,
            'devices': {
                'hue_bridges': [],
                'lifx_lights': []
            },
            'groups': [],
            'schedules': [],
            'settings': {
                'auto_discover': True,
                'discover_on_startup': True,
                'dark_mode': False,
                'startup_check_updates': True,
                'notification_level': 'normal'  # 'minimal', 'normal', 'verbose'
            },
            'window': {
                'width': 900,
                'height': 600,
                'maximized': False,
                'position_x': 100,
                'position_y': 100
            },
            'last_protocol': 'hue'  # Last protocol tab selected
        }
        self.config_file = CONFIG_FILE
    
    def load_config(self):
        """Load configuration from disk, creating default if none exists"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Update config with loaded values, maintaining defaults for missing keys
                    self._update_config_recursive(self.config, loaded_config)
                logger.info(f"Configuration loaded from {self.config_file}")
                return True
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading configuration: {e}")
                # Backup corrupted config
                if os.path.exists(self.config_file):
                    backup_path = str(self.config_file) + ".bak"
                    try:
                        os.rename(self.config_file, backup_path)
                        logger.info(f"Backed up corrupted config to {backup_path}")
                    except OSError as e:
                        logger.error(f"Could not backup corrupted config: {e}")
                return False
        else:
            logger.info("No configuration file found, using defaults")
            return self.save_config()  # Create a new config file with defaults
    
    def save_config(self):
        """Save current configuration to disk"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except (IOError, OSError) as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get_setting(self, key, default=None):
        """
        Get a setting value from the configuration
        
        Args:
            key: The setting key to retrieve
            default: Default value to return if key not found
            
        Returns:
            The setting value or default if not found
        """
        return self.config['settings'].get(key, default)
    
    def set_setting(self, key, value):
        """
        Update a setting in the configuration
        
        Args:
            key: The setting key to update
            value: The new value
            
        Returns:
            True if setting was updated, False otherwise
        """
        if key in self.config['settings'] or value is not None:
            self.config['settings'][key] = value
            return True
        return False
    
    def get_window_settings(self):
        """Get the saved window configuration"""
        return self.config['window']
    
    def update_window_settings(self, settings):
        """Update window configuration with new values"""
        self.config['window'].update(settings)
    
    def get_devices(self, protocol=None):
        """
        Get saved device information
        
        Args:
            protocol: Optional protocol filter, if None returns all devices
            
        Returns:
            Dictionary of devices by protocol or list of a specific protocol
        """
        if protocol == 'hue':
            return self.config['devices']['hue_bridges']
        elif protocol == 'lifx':
            return self.config['devices']['lifx_lights']
        else:
            return self.config['devices']
    
    def add_device(self, protocol, device_info):
        """
        Add or update a device in the configuration
        
        Args:
            protocol: Device protocol ('hue' or 'lifx')
            device_info: Dictionary of device information
            
        Returns:
            True if device was added/updated, False otherwise
        """
        if protocol == 'hue':
            # For Hue, check if bridge already exists by ID
            if 'id' in device_info:
                for i, bridge in enumerate(self.config['devices']['hue_bridges']):
                    if bridge.get('id') == device_info['id']:
                        # Update existing bridge
                        self.config['devices']['hue_bridges'][i].update(device_info)
                        return True
                # Add new bridge
                self.config['devices']['hue_bridges'].append(device_info)
                return True
        elif protocol == 'lifx':
            # For LIFX, check if light already exists by ID
            if 'id' in device_info:
                for i, light in enumerate(self.config['devices']['lifx_lights']):
                    if light.get('id') == device_info['id']:
                        # Update existing light
                        self.config['devices']['lifx_lights'][i].update(device_info)
                        return True
                # Add new light
                self.config['devices']['lifx_lights'].append(device_info)
                return True
        return False
    
    def remove_device(self, protocol, device_id):
        """
        Remove a device from the configuration
        
        Args:
            protocol: Device protocol ('hue' or 'lifx')
            device_id: ID of the device to remove
            
        Returns:
            True if device was removed, False otherwise
        """
        if protocol == 'hue':
            for i, bridge in enumerate(self.config['devices']['hue_bridges']):
                if bridge.get('id') == device_id:
                    self.config['devices']['hue_bridges'].pop(i)
                    return True
        elif protocol == 'lifx':
            for i, light in enumerate(self.config['devices']['lifx_lights']):
                if light.get('id') == device_id:
                    self.config['devices']['lifx_lights'].pop(i)
                    return True
        return False
    
    def get_groups(self):
        """Get configured light groups"""
        return self.config['groups']
    
    def add_group(self, group_info):
        """Add or update a light group"""
        if 'id' in group_info:
            for i, group in enumerate(self.config['groups']):
                if group.get('id') == group_info['id']:
                    self.config['groups'][i].update(group_info)
                    return True
            self.config['groups'].append(group_info)
            return True
        return False
    
    def remove_group(self, group_id):
        """Remove a light group"""
        for i, group in enumerate(self.config['groups']):
            if group.get('id') == group_id:
                self.config['groups'].pop(i)
                return True
        return False
    
    def get_schedules(self):
        """Get configured schedules"""
        return self.config['schedules']
    
    def add_schedule(self, schedule_info):
        """Add or update a schedule"""
        if 'id' in schedule_info:
            for i, schedule in enumerate(self.config['schedules']):
                if schedule.get('id') == schedule_info['id']:
                    self.config['schedules'][i].update(schedule_info)
                    return True
            self.config['schedules'].append(schedule_info)
            return True
        return False
    
    def remove_schedule(self, schedule_id):
        """Remove a schedule"""
        for i, schedule in enumerate(self.config['schedules']):
            if schedule.get('id') == schedule_id:
                self.config['schedules'].pop(i)
                return True
        return False
    
    def get_last_protocol(self):
        """Get the last selected protocol tab"""
        return self.config.get('last_protocol', 'hue')
    
    def set_last_protocol(self, protocol):
        """Set the last selected protocol tab"""
        if protocol in ['hue', 'lifx']:
            self.config['last_protocol'] = protocol
            return True
        return False
    
    def _update_config_recursive(self, target, source):
        """
        Recursively update configuration while maintaining structure and defaults
        
        Args:
            target: Target dictionary to update (our default config)
            source: Source dictionary with values to apply
        """
        for key, value in source.items():
            if key in target:
                if isinstance(value, dict) and isinstance(target[key], dict):
                    # Recursively update nested dictionaries
                    self._update_config_recursive(target[key], value)
                else:
                    # Update simple values
                    target[key] = value
