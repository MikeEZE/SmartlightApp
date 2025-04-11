"""
Web interface for the Smart Light Controller
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import logging
import sys
from datetime import datetime
import threading

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Smart Light Controller Web")

app = Flask(__name__)

# Store for our lights, groups, and schedules
app_data = {
    'lights': {},
    'groups': {},
    'schedules': {}
}

# Configuration file path
CONFIG_DIR = os.path.expanduser("~/.smart_light_controller")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

def load_config():
    """Load configuration from disk"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                logger.info(f"Configuration loaded from {CONFIG_FILE}")
                return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    # Default configuration
    return {
        'devices': {
            'hue': [],
            'lifx': []
        },
        'groups': {},
        'schedules': {},
        'settings': {
            'discover_on_startup': True,
            'refresh_interval': 30,
            'theme': 'light'
        }
    }

def save_config(config):
    """Save configuration to disk"""
    # Ensure directory exists
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False

def discover_lights():
    """Simulate discovering lights"""
    # Simulate LIFX lights
    lifx_lights = [
        {
            'id': 'd073d5f1f9e2',
            'ip': '192.168.1.101',
            'mac': 'd0:73:d5:f1:f9:e2',
            'name': 'LIFX Living Room',
            'model': 'LIFX Color 1000',
            'manufacturer': 'LIFX',
            'firmware': '2.80',
            'protocol': 'lifx',
            'state': {
                'on': True,
                'brightness': 80,
                'color_temp': 3500,
                'hue': 120,
                'saturation': 50,
                'rgb_color': (128, 255, 128),
                'reachable': True
            }
        },
        {
            'id': 'd073d5f1f9e3',
            'ip': '192.168.1.102',
            'mac': 'd0:73:d5:f1:f9:e3',
            'name': 'LIFX Bedroom',
            'model': 'LIFX White 800',
            'manufacturer': 'LIFX',
            'firmware': '2.80',
            'protocol': 'lifx',
            'state': {
                'on': False,
                'brightness': 50,
                'color_temp': 2700,
                'reachable': True
            }
        }
    ]
    
    # Simulate Hue bridge and lights
    hue_bridge = {
        'id': '001788fffe23de89',
        'ip': '192.168.1.100',
        'name': 'Philips Hue Bridge',
        'model': 'BSB002',
        'manufacturer': 'Philips',
        'protocol': 'hue',
        'username': 'abcdefghijklmnopqrstuvwxyz',
        'lights': [
            {
                'id': '1',
                'name': 'Hue Kitchen',
                'model': 'LCT007',
                'type': 'Extended color light',
                'state': {
                    'on': True,
                    'brightness': 254,
                    'hue': 8418,
                    'saturation': 140,
                    'color_temp': 366,
                    'reachable': True
                }
            },
            {
                'id': '2',
                'name': 'Hue Dining Room',
                'model': 'LCT007',
                'type': 'Extended color light',
                'state': {
                    'on': False,
                    'brightness': 175,
                    'hue': 15331,
                    'saturation': 121,
                    'color_temp': 400,
                    'reachable': True
                }
            }
        ]
    }
    
    return {
        'lifx': lifx_lights,
        'hue': [hue_bridge]
    }

# Initialize data from config or discovery
config = load_config()

# Load any saved lights
if 'devices' in config and 'lifx' in config['devices'] and config['devices']['lifx']:
    for light in config['devices']['lifx']:
        app_data['lights'][light['id']] = light

if 'devices' in config and 'hue' in config['devices'] and config['devices']['hue']:
    for bridge in config['devices']['hue']:
        if 'lights' in bridge:
            for light in bridge['lights']:
                # Create a unique ID for Hue lights (bridge ID + light ID)
                unique_id = f"hue_{bridge['id']}_{light['id']}"
                light['unique_id'] = unique_id
                light['bridge_id'] = bridge['id']
                light['protocol'] = 'hue'
                app_data['lights'][unique_id] = light

# Make sure the config has the expected structure
if 'devices' not in config:
    config['devices'] = {'hue': [], 'lifx': []}
if 'lifx' not in config['devices']:
    config['devices']['lifx'] = []
if 'hue' not in config['devices']:
    config['devices']['hue'] = []
if 'groups' not in config:
    config['groups'] = {}
if 'schedules' not in config:
    config['schedules'] = {}
if 'settings' not in config:
    config['settings'] = {
        'discover_on_startup': True,
        'refresh_interval': 30,
        'theme': 'light'
    }

# If no lights loaded from config, discover them
if not app_data['lights'] and config['settings'].get('discover_on_startup', True):
    discovered = discover_lights()
    
    # Add LIFX lights
    for light in discovered['lifx']:
        app_data['lights'][light['id']] = light
        if light['id'] not in [l.get('id') for l in config['devices']['lifx']]:
            config['devices']['lifx'].append(light)
    
    # Add Hue bridges and lights
    for bridge in discovered['hue']:
        if 'lights' in bridge:
            for light in bridge['lights']:
                # Create a unique ID for Hue lights
                unique_id = f"hue_{bridge['id']}_{light['id']}"
                light['unique_id'] = unique_id
                light['bridge_id'] = bridge['id'] 
                light['protocol'] = 'hue'
                app_data['lights'][unique_id] = light
            
            # Add bridge to config if new
            if bridge['id'] not in [b.get('id') for b in config['devices']['hue']]:
                config['devices']['hue'].append(bridge)
    
    # Save updated config
    save_config(config)

# Load groups
app_data['groups'] = config.get('groups', {})

# Load schedules
app_data['schedules'] = config.get('schedules', {})

@app.route('/')
def home():
    """Home page"""
    return render_template('index.html', 
                           lights=app_data['lights'],
                           groups=app_data['groups'],
                           schedules=app_data['schedules'])

@app.route('/devices')
def devices():
    """Devices page"""
    return render_template('devices.html', lights=app_data['lights'])

@app.route('/groups')
def groups():
    """Groups page"""
    return render_template('groups.html', 
                           groups=app_data['groups'],
                           lights=app_data['lights'])

@app.route('/schedules')
def schedules():
    """Schedules page"""
    return render_template('schedules.html', 
                           schedules=app_data['schedules'],
                           lights=app_data['lights'],
                           groups=app_data['groups'])

@app.route('/api/lights', methods=['GET', 'POST'])
def get_lights():
    """API endpoint to get all lights or create a new virtual light"""
    if request.method == 'GET':
        return jsonify(app_data['lights'])
    
    # POST method for creating a new virtual light
    data = request.json
    if 'name' not in data:
        return jsonify({'error': 'Light name is required'}), 400
    
    # Generate a unique ID
    light_id = f"virtual_{len(app_data['lights']) + 1}_{int(datetime.now().timestamp())}"
    
    # Create default state if not provided
    if 'state' not in data:
        data['state'] = {
            'on': True,
            'brightness': 100,
            'color_temp': 3500,
            'reachable': True
        }
    
    # Set protocol to virtual if not specified
    if 'protocol' not in data:
        data['protocol'] = 'virtual'
    
    # Add metadata
    data['id'] = light_id
    data['user_created'] = True
    
    # Add the light to app data
    app_data['lights'][light_id] = data
    
    # If using 'virtual' protocol, add to a special section in config
    if 'virtual' not in config['devices']:
        config['devices']['virtual'] = []
    
    config['devices']['virtual'].append(data)
    save_config(config)
    
    return jsonify({
        'success': True, 
        'id': light_id,
        'message': f"Created new virtual light: {data['name']}"
    })

@app.route('/api/lights/<light_id>')
def get_light(light_id):
    """API endpoint to get a specific light"""
    if light_id in app_data['lights']:
        return jsonify(app_data['lights'][light_id])
    return jsonify({'error': 'Light not found'}), 404

@app.route('/api/lights/<light_id>/state', methods=['PUT'])
def set_light_state(light_id):
    """API endpoint to set a light's state"""
    if light_id in app_data['lights']:
        data = request.json
        # Update light state
        if 'on' in data:
            app_data['lights'][light_id]['state']['on'] = data['on']
        if 'brightness' in data:
            app_data['lights'][light_id]['state']['brightness'] = data['brightness']
        if 'color_temp' in data:
            app_data['lights'][light_id]['state']['color_temp'] = data['color_temp']
        if 'hue' in data:
            app_data['lights'][light_id]['state']['hue'] = data['hue']
        if 'saturation' in data:
            app_data['lights'][light_id]['state']['saturation'] = data['saturation']
        
        # Update config based on protocol
        protocol = app_data['lights'][light_id].get('protocol', '')
        
        if protocol == 'lifx':
            for i, light in enumerate(config['devices']['lifx']):
                if light['id'] == light_id:
                    config['devices']['lifx'][i]['state'] = app_data['lights'][light_id]['state']
                    break
        elif protocol == 'hue':
            # Extract bridge and light ID
            bridge_id = app_data['lights'][light_id]['bridge_id']
            actual_light_id = light_id.split('_')[-1]
            
            for i, bridge in enumerate(config['devices']['hue']):
                if bridge['id'] == bridge_id:
                    for j, light in enumerate(bridge['lights']):
                        if light['id'] == actual_light_id:
                            config['devices']['hue'][i]['lights'][j]['state'] = app_data['lights'][light_id]['state']
                            break
                    break
        elif protocol == 'virtual':
            # Handle virtual lights created by the user
            if 'virtual' in config['devices']:
                for i, light in enumerate(config['devices']['virtual']):
                    if light['id'] == light_id:
                        config['devices']['virtual'][i]['state'] = app_data['lights'][light_id]['state']
                        break
        
        # Log changes for debugging
        logger.info(f"Light state updated: {light_id} - Protocol: {protocol}")
        logger.info(f"New state: {app_data['lights'][light_id]['state']}")
        
        save_config(config)
        return jsonify({
            'success': True,
            'light_id': light_id,
            'state': app_data['lights'][light_id]['state']
        })
    return jsonify({'error': 'Light not found'}), 404

@app.route('/api/groups')
def get_groups():
    """API endpoint to get all groups"""
    return jsonify(app_data['groups'])

@app.route('/api/groups/<group_id>')
def get_group(group_id):
    """API endpoint to get a specific group"""
    if group_id in app_data['groups']:
        return jsonify(app_data['groups'][group_id])
    return jsonify({'error': 'Group not found'}), 404

@app.route('/api/groups', methods=['POST'])
def create_group():
    """API endpoint to create a new group"""
    data = request.json
    if 'name' not in data or 'lights' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Generate a new unique ID
    group_id = f"group_{len(app_data['groups']) + 1}_{int(datetime.now().timestamp())}"
    
    # Create group
    app_data['groups'][group_id] = {
        'id': group_id,
        'name': data['name'],
        'lights': data['lights']
    }
    
    # Update config
    config['groups'][group_id] = app_data['groups'][group_id]
    save_config(config)
    
    return jsonify({'id': group_id, 'success': True})

@app.route('/api/groups/<group_id>', methods=['PUT'])
def update_group(group_id):
    """API endpoint to update a group"""
    if group_id in app_data['groups']:
        data = request.json
        if 'name' in data:
            app_data['groups'][group_id]['name'] = data['name']
        if 'lights' in data:
            app_data['groups'][group_id]['lights'] = data['lights']
        
        # Update config
        config['groups'][group_id] = app_data['groups'][group_id]
        save_config(config)
        
        return jsonify({'success': True})
    return jsonify({'error': 'Group not found'}), 404

@app.route('/api/groups/<group_id>', methods=['DELETE'])
def delete_group(group_id):
    """API endpoint to delete a group"""
    if group_id in app_data['groups']:
        del app_data['groups'][group_id]
        
        # Update config
        if group_id in config['groups']:
            del config['groups'][group_id]
            save_config(config)
        
        return jsonify({'success': True})
    return jsonify({'error': 'Group not found'}), 404

@app.route('/api/groups/<group_id>/state', methods=['PUT'])
def set_group_state(group_id):
    """API endpoint to set state for all lights in a group"""
    if group_id in app_data['groups']:
        data = request.json
        group = app_data['groups'][group_id]
        
        # Update state for each light in the group
        for light_id in group['lights']:
            if light_id in app_data['lights']:
                # Update light state
                if 'on' in data:
                    app_data['lights'][light_id]['state']['on'] = data['on']
                if 'brightness' in data:
                    app_data['lights'][light_id]['state']['brightness'] = data['brightness']
                if 'color_temp' in data:
                    app_data['lights'][light_id]['state']['color_temp'] = data['color_temp']
                if 'hue' in data and 'hue' in app_data['lights'][light_id]['state']:
                    app_data['lights'][light_id]['state']['hue'] = data['hue']
                if 'saturation' in data and 'saturation' in app_data['lights'][light_id]['state']:
                    app_data['lights'][light_id]['state']['saturation'] = data['saturation']
        
        # Update config
        save_config(config)
        return jsonify({'success': True})
    return jsonify({'error': 'Group not found'}), 404

@app.route('/api/schedules')
def get_schedules():
    """API endpoint to get all schedules"""
    return jsonify(app_data['schedules'])

@app.route('/api/schedules/<schedule_id>')
def get_schedule(schedule_id):
    """API endpoint to get a specific schedule"""
    if schedule_id in app_data['schedules']:
        return jsonify(app_data['schedules'][schedule_id])
    return jsonify({'error': 'Schedule not found'}), 404

@app.route('/api/schedules', methods=['POST'])
def create_schedule():
    """API endpoint to create a new schedule"""
    data = request.json
    if 'name' not in data or 'time' not in data or 'actions' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Generate a new unique ID
    schedule_id = f"schedule_{len(app_data['schedules']) + 1}_{int(datetime.now().timestamp())}"
    
    # Create schedule
    app_data['schedules'][schedule_id] = {
        'id': schedule_id,
        'name': data['name'],
        'time': data['time'],
        'days': data.get('days', ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']),
        'enabled': data.get('enabled', True),
        'actions': data['actions']
    }
    
    # Update config
    config['schedules'][schedule_id] = app_data['schedules'][schedule_id]
    save_config(config)
    
    return jsonify({'id': schedule_id, 'success': True})

@app.route('/api/schedules/<schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """API endpoint to update a schedule"""
    if schedule_id in app_data['schedules']:
        data = request.json
        
        # Update schedule properties
        for key, value in data.items():
            app_data['schedules'][schedule_id][key] = value
        
        # Update config
        config['schedules'][schedule_id] = app_data['schedules'][schedule_id]
        save_config(config)
        
        return jsonify({'success': True})
    return jsonify({'error': 'Schedule not found'}), 404

@app.route('/api/schedules/<schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """API endpoint to delete a schedule"""
    if schedule_id in app_data['schedules']:
        del app_data['schedules'][schedule_id]
        
        # Update config
        if schedule_id in config['schedules']:
            del config['schedules'][schedule_id]
            save_config(config)
        
        return jsonify({'success': True})
    return jsonify({'error': 'Schedule not found'}), 404

@app.route('/api/discover', methods=['POST'])
def api_discover():
    """API endpoint to trigger light discovery"""
    discovered = discover_lights()
    
    # Add LIFX lights
    for light in discovered['lifx']:
        app_data['lights'][light['id']] = light
        if light['id'] not in [l.get('id') for l in config['devices']['lifx']]:
            config['devices']['lifx'].append(light)
    
    # Add Hue bridges and lights
    for bridge in discovered['hue']:
        if 'lights' in bridge:
            for light in bridge['lights']:
                # Create a unique ID for Hue lights
                unique_id = f"hue_{bridge['id']}_{light['id']}"
                light['unique_id'] = unique_id
                light['bridge_id'] = bridge['id']
                light['protocol'] = 'hue'
                app_data['lights'][unique_id] = light
            
            # Add bridge to config if new
            if bridge['id'] not in [b.get('id') for b in config['devices']['hue']]:
                config['devices']['hue'].append(bridge)
    
    # Save updated config
    save_config(config)
    
    return jsonify({
        'success': True,
        'lights_count': len(app_data['lights'])
    })

@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html', settings=config['settings'])

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    """API endpoint to update settings"""
    data = request.json
    
    # Update settings
    for key, value in data.items():
        config['settings'][key] = value
    
    # Save config
    save_config(config)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    # Create templates and static directories if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Create initial templates if they don't exist
    if not os.path.exists('templates/index.html'):
        app.logger.info("Creating initial templates...")
        # We'll create them separately using the editor
    
    app.run(host='0.0.0.0', port=5000, debug=True)