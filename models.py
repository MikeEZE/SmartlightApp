"""
Database models for the Smart Light Controller application
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class LightState(db.Model):
    """Model to store light state information"""
    id = db.Column(db.Integer, primary_key=True)
    on = db.Column(db.Boolean, default=False)
    brightness = db.Column(db.Integer, default=100)
    color_temp = db.Column(db.Integer, default=3500)
    hue = db.Column(db.Integer, default=0)
    saturation = db.Column(db.Integer, default=0)
    rgb_color = db.Column(db.String(50), default="(255, 255, 255)")
    reachable = db.Column(db.Boolean, default=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    light_id = db.Column(db.Integer, db.ForeignKey('light.id'), nullable=False)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'on': self.on,
            'brightness': self.brightness,
            'color_temp': self.color_temp,
            'hue': self.hue,
            'saturation': self.saturation,
            'rgb_color': self.rgb_color,
            'reachable': self.reachable,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary data"""
        state = cls()
        if 'on' in data:
            state.on = data['on']
        if 'brightness' in data:
            state.brightness = data['brightness']
        if 'color_temp' in data:
            state.color_temp = data['color_temp']
        if 'hue' in data:
            state.hue = data['hue']
        if 'saturation' in data:
            state.saturation = data['saturation']
        if 'rgb_color' in data:
            state.rgb_color = str(data['rgb_color'])
        if 'reachable' in data:
            state.reachable = data['reachable']
        
        return state

class Light(db.Model):
    """Model to store light information"""
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    protocol = db.Column(db.String(20), nullable=False)  # 'hue', 'lifx', 'virtual'
    model = db.Column(db.String(50))
    manufacturer = db.Column(db.String(50))
    firmware = db.Column(db.String(30))
    ip_address = db.Column(db.String(15))
    mac_address = db.Column(db.String(17))
    bridge_id = db.Column(db.String(50))
    is_user_created = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    state = db.relationship('LightState', backref='light', uselist=False, lazy=True, 
                          cascade="all, delete-orphan")
    
    # Many-to-many relationship with groups
    groups = db.relationship('Group', secondary='light_group_association',
                           backref=db.backref('lights', lazy='dynamic'))
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.unique_id,
            'name': self.name,
            'protocol': self.protocol,
            'model': self.model,
            'manufacturer': self.manufacturer,
            'firmware': self.firmware,
            'ip': self.ip_address,
            'mac': self.mac_address,
            'bridge_id': self.bridge_id,
            'state': self.state.to_dict() if self.state else {},
            'is_user_created': self.is_user_created,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create from dictionary data"""
        light = cls(
            unique_id=data.get('id') or data.get('unique_id'),
            name=data.get('name', 'Unnamed Light'),
            protocol=data.get('protocol', 'virtual'),
            model=data.get('model'),
            manufacturer=data.get('manufacturer'),
            firmware=data.get('firmware'),
            ip_address=data.get('ip'),
            mac_address=data.get('mac'),
            bridge_id=data.get('bridge_id'),
            is_user_created=data.get('user_created', False)
        )
        
        if 'state' in data:
            light.state = LightState.from_dict(data['state'])
        
        return light

# Association table for many-to-many relationship between lights and groups
light_group_association = db.Table('light_group_association',
    db.Column('light_id', db.Integer, db.ForeignKey('light.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)

class Group(db.Model):
    """Model to store light group information"""
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.unique_id,
            'name': self.name,
            'lights': [light.unique_id for light in self.lights],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Schedule(db.Model):
    """Model to store schedule information"""
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(8), nullable=False)  # Format: "HH:MM:SS"
    days = db.Column(db.String(200), nullable=False, default="monday,tuesday,wednesday,thursday,friday,saturday,sunday")
    enabled = db.Column(db.Boolean, default=True)
    actions = db.Column(db.Text, nullable=False)  # JSON-encoded string of actions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_days_list(self):
        """Get days as a list"""
        return self.days.split(',')
    
    def set_days_list(self, days_list):
        """Set days from a list"""
        self.days = ','.join(days_list)
    
    def get_actions(self):
        """Get actions as Python objects"""
        return json.loads(self.actions)
    
    def set_actions(self, actions_list):
        """Set actions from Python objects"""
        self.actions = json.dumps(actions_list)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.unique_id,
            'name': self.name,
            'time': self.time,
            'days': self.get_days_list(),
            'enabled': self.enabled,
            'actions': self.get_actions(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Setting(db.Model):
    """Model to store application settings"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), default='string')  # string, int, bool, json
    
    def get_value(self):
        """Get the typed value"""
        if self.value_type == 'int':
            return int(self.value)
        elif self.value_type == 'bool':
            return self.value.lower() == 'true'
        elif self.value_type == 'json':
            return json.loads(self.value)
        return self.value
    
    def set_value(self, value):
        """Set the value with correct type"""
        if isinstance(value, bool):
            self.value_type = 'bool'
            self.value = str(value).lower()
        elif isinstance(value, int):
            self.value_type = 'int'
            self.value = str(value)
        elif isinstance(value, (dict, list)):
            self.value_type = 'json'
            self.value = json.dumps(value)
        else:
            self.value_type = 'string'
            self.value = str(value)
    
    @classmethod
    def get_settings_dict(cls):
        """Get all settings as a dictionary"""
        settings = {}
        for setting in cls.query.all():
            settings[setting.key] = setting.get_value()
        return settings