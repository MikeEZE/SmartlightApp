"""
Light control widget for managing individual lights
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QGroupBox, QComboBox, QFormLayout, QFrame, QCheckBox
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QColor

from ..constants import APP_NAME, ATTR_BRIGHTNESS, ATTR_COLOR_TEMP
from .color_picker import ColorPickerWidget
from .icons import get_icon


logger = logging.getLogger(APP_NAME)


class LightControlWidget(QWidget):
    """
    Widget for controlling a single light
    Shows controls for brightness, color, and on/off state
    """
    
    def __init__(self, light_manager, parent=None):
        """Initialize light control widget with light manager"""
        super().__init__(parent)
        self.light_manager = light_manager
        
        # Current light selection
        self.current_protocol = None
        self.current_light_id = None
        
        # Set up UI
        self.init_ui()
        
        # Start in disabled state (no light selected)
        self.set_controls_enabled(False)
    
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Light selection info
        self.info_layout = QHBoxLayout()
        
        self.light_name_label = QLabel("No light selected")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.light_name_label.setFont(font)
        self.info_layout.addWidget(self.light_name_label)
        
        self.light_details_label = QLabel("")
        self.info_layout.addWidget(self.light_details_label)
        
        self.info_layout.addStretch(1)
        
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(16, 16)
        self.status_indicator.setStyleSheet(
            "background-color: gray; border-radius: 8px;"
        )
        self.info_layout.addWidget(self.status_indicator)
        
        layout.addLayout(self.info_layout)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # On/Off control
        on_off_layout = QHBoxLayout()
        
        self.power_button = QPushButton("Power")
        self.power_button.setCheckable(True)
        self.power_button.setFixedWidth(100)
        self.power_button.clicked.connect(self.on_power_toggled)
        on_off_layout.addWidget(self.power_button)
        
        self.power_label = QLabel("OFF")
        on_off_layout.addWidget(self.power_label)
        
        on_off_layout.addStretch(1)
        
        layout.addLayout(on_off_layout)
        
        # Brightness control
        brightness_group = QGroupBox("Brightness")
        brightness_layout = QVBoxLayout(brightness_group)
        
        brightness_slider_layout = QHBoxLayout()
        brightness_slider_layout.addWidget(QLabel("0%"))
        
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(100)
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)
        brightness_slider_layout.addWidget(self.brightness_slider)
        
        self.brightness_label = QLabel("100%")
        self.brightness_label.setFixedWidth(50)
        brightness_slider_layout.addWidget(self.brightness_label)
        
        brightness_layout.addLayout(brightness_slider_layout)
        
        layout.addWidget(brightness_group)
        
        # Color temperature control
        temp_group = QGroupBox("Color Temperature")
        temp_layout = QVBoxLayout(temp_group)
        
        temp_slider_layout = QHBoxLayout()
        temp_slider_layout.addWidget(QLabel("Warm"))
        
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(2000, 6500)
        self.temp_slider.setValue(4000)
        self.temp_slider.valueChanged.connect(self.on_temp_changed)
        temp_slider_layout.addWidget(self.temp_slider)
        
        self.temp_label = QLabel("4000K")
        self.temp_label.setFixedWidth(50)
        temp_slider_layout.addWidget(self.temp_label)
        
        temp_layout.addLayout(temp_slider_layout)
        
        layout.addWidget(temp_group)
        
        # Color control
        color_group = QGroupBox("Color")
        color_layout = QVBoxLayout(color_group)
        
        # Color picker
        self.color_picker = ColorPickerWidget()
        self.color_picker.colorSelected.connect(self.on_color_selected)
        color_layout.addWidget(self.color_picker)
        
        layout.addWidget(color_group)
        
        # Preset controls
        preset_group = QGroupBox("Presets")
        preset_layout = QHBoxLayout(preset_group)
        
        # Preset buttons for different scenes/colors
        presets = [
            ("Warm White", (255, 166, 87)),
            ("Cool White", (255, 255, 255)),
            ("Daylight", (255, 255, 240)),
            ("Night Light", (255, 140, 20)),
            ("Reading", (255, 200, 120)),
            ("Relax", (255, 120, 50))
        ]
        
        for name, color in presets:
            button = QPushButton(name)
            button.setFixedHeight(40)
            r, g, b = color
            button.setStyleSheet(
                f"background-color: rgb({r}, {g}, {b}); color: black;"
            )
            button.clicked.connect(lambda checked, c=color: self.apply_preset_color(c))
            preset_layout.addWidget(button)
        
        layout.addWidget(preset_group)
        
        # Stretch to fill space
        layout.addStretch(1)
    
    def set_light(self, protocol, light_id):
        """
        Set the current light to control
        
        Args:
            protocol: Light protocol ('hue' or 'lifx')
            light_id: Light identifier
        """
        if not protocol or not light_id:
            # Clear light selection
            self.current_protocol = None
            self.current_light_id = None
            self.light_name_label.setText("No light selected")
            self.light_details_label.setText("")
            self.set_controls_enabled(False)
            return
        
        # Get light information
        light = self.light_manager.get_light(protocol, light_id)
        if not light:
            logger.error(f"Cannot find light {protocol}/{light_id}")
            return
        
        # Update light selection
        self.current_protocol = protocol
        self.current_light_id = light_id
        
        # Update UI with light information
        self.light_name_label.setText(light.get('name', 'Unknown Light'))
        
        # Set details text
        details = []
        if 'manufacturer' in light:
            details.append(light['manufacturer'])
        if 'model' in light:
            details.append(light['model'])
        self.light_details_label.setText(", ".join(details))
        
        # Update controls with current state
        self.update_controls_from_state(light)
        
        # Enable controls
        self.set_controls_enabled(True)
    
    def update_controls_from_state(self, light):
        """
        Update controls to reflect the current light state
        
        Args:
            light: Light information dictionary
        """
        state = light.get('state', {})
        
        # Update power state
        on = state.get('on', False)
        self.power_button.setChecked(on)
        self.power_label.setText("ON" if on else "OFF")
        
        # Update status indicator
        if not state.get('reachable', True):
            self.status_indicator.setStyleSheet(
                "background-color: gray; border-radius: 8px;"
            )
        elif on:
            self.status_indicator.setStyleSheet(
                "background-color: green; border-radius: 8px;"
            )
        else:
            self.status_indicator.setStyleSheet(
                "background-color: red; border-radius: 8px;"
            )
        
        # Update brightness (block signals to prevent feedback loop)
        brightness = state.get('brightness', 100)
        self.brightness_slider.blockSignals(True)
        self.brightness_slider.setValue(brightness)
        self.brightness_slider.blockSignals(False)
        self.brightness_label.setText(f"{brightness}%")
        
        # Update color temperature
        color_temp = state.get('color_temp', 4000)
        self.temp_slider.blockSignals(True)
        self.temp_slider.setValue(color_temp)
        self.temp_slider.blockSignals(False)
        self.temp_label.setText(f"{color_temp}K")
        
        # Update color picker
        if 'rgb_color' in state:
            r, g, b = state['rgb_color']
            self.color_picker.blockSignals(True)
            self.color_picker.set_color(QColor(r, g, b))
            self.color_picker.blockSignals(False)
    
    def set_controls_enabled(self, enabled):
        """
        Enable or disable all controls
        
        Args:
            enabled: True to enable, False to disable
        """
        self.power_button.setEnabled(enabled)
        self.brightness_slider.setEnabled(enabled)
        self.temp_slider.setEnabled(enabled)
        self.color_picker.setEnabled(enabled)
    
    def update_if_match(self, protocol, light_id):
        """
        Update controls if they match the current light
        
        Args:
            protocol: Light protocol
            light_id: Light identifier
        """
        if protocol == self.current_protocol and light_id == self.current_light_id:
            light = self.light_manager.get_light(protocol, light_id)
            if light:
                self.update_controls_from_state(light)
    
    @Slot(bool)
    def on_power_toggled(self, checked):
        """Handle power button toggle"""
        if not self.current_protocol or not self.current_light_id:
            return
        
        # Update label
        self.power_label.setText("ON" if checked else "OFF")
        
        # Send command to light
        state = {'on': checked}
        success = self.light_manager.set_light_state(
            self.current_protocol, self.current_light_id, state
        )
        
        if not success:
            logger.error(f"Failed to set power state for {self.current_protocol}/{self.current_light_id}")
    
    @Slot(int)
    def on_brightness_changed(self, value):
        """Handle brightness slider change"""
        if not self.current_protocol or not self.current_light_id:
            return
        
        # Update label
        self.brightness_label.setText(f"{value}%")
        
        # Send command to light (throttled in a real implementation)
        state = {ATTR_BRIGHTNESS: value}
        success = self.light_manager.set_light_state(
            self.current_protocol, self.current_light_id, state
        )
        
        if not success:
            logger.error(f"Failed to set brightness for {self.current_protocol}/{self.current_light_id}")
    
    @Slot(int)
    def on_temp_changed(self, value):
        """Handle color temperature slider change"""
        if not self.current_protocol or not self.current_light_id:
            return
        
        # Update label
        self.temp_label.setText(f"{value}K")
        
        # Send command to light (throttled in a real implementation)
        state = {ATTR_COLOR_TEMP: value}
        success = self.light_manager.set_light_state(
            self.current_protocol, self.current_light_id, state
        )
        
        if not success:
            logger.error(f"Failed to set color temperature for {self.current_protocol}/{self.current_light_id}")
    
    @Slot(QColor)
    def on_color_selected(self, color):
        """Handle color picker selection"""
        if not self.current_protocol or not self.current_light_id:
            return
        
        # Send command to light
        rgb_color = (color.red(), color.green(), color.blue())
        state = {'rgb_color': rgb_color}
        success = self.light_manager.set_light_state(
            self.current_protocol, self.current_light_id, state
        )
        
        if not success:
            logger.error(f"Failed to set color for {self.current_protocol}/{self.current_light_id}")
    
    def apply_preset_color(self, color):
        """Apply a preset color to the light"""
        if not self.current_protocol or not self.current_light_id:
            return
        
        r, g, b = color
        qcolor = QColor(r, g, b)
        
        # Update color picker to match
        self.color_picker.blockSignals(True)
        self.color_picker.set_color(qcolor)
        self.color_picker.blockSignals(False)
        
        # Send command to light
        state = {'rgb_color': color}
        success = self.light_manager.set_light_state(
            self.current_protocol, self.current_light_id, state
        )
        
        if not success:
            logger.error(f"Failed to apply preset color for {self.current_protocol}/{self.current_light_id}")
