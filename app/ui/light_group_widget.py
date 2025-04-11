"""
Widget for managing light groups
"""

import logging
import uuid
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QDialog, QDialogButtonBox, 
    QFormLayout, QLineEdit, QGroupBox, QCheckBox, QMessageBox,
    QSlider, QComboBox
)
from PySide6.QtCore import Qt, Slot

from ..constants import APP_NAME
from .icons import get_icon


logger = logging.getLogger(APP_NAME)


class LightGroupWidget(QWidget):
    """
    Widget for creating, editing, and controlling light groups
    """
    
    def __init__(self, light_manager, config_manager, parent=None):
        """Initialize light group widget with managers"""
        super().__init__(parent)
        self.light_manager = light_manager
        self.config_manager = config_manager
        
        # Current group selection
        self.current_group_id = None
        
        # Set up UI
        self.init_ui()
        
        # Load groups
        self.load_groups()
    
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        layout = QHBoxLayout(self)
        
        # Left panel - group list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Group list
        group_label = QLabel("Light Groups:")
        left_layout.addWidget(group_label)
        
        self.group_list = QListWidget()
        self.group_list.setMinimumWidth(200)
        self.group_list.currentItemChanged.connect(self.on_group_selected)
        left_layout.addWidget(self.group_list)
        
        layout.addWidget(left_panel)
        
        # Right panel - group controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Group info
        self.group_name_label = QLabel("No group selected")
        font = self.group_name_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.group_name_label.setFont(font)
        right_layout.addWidget(self.group_name_label)
        
        self.group_info_label = QLabel("")
        right_layout.addWidget(self.group_info_label)
        
        # Group control panel
        control_group = QGroupBox("Group Control")
        control_layout = QVBoxLayout(control_group)
        
        # Power controls
        power_layout = QHBoxLayout()
        
        self.all_on_button = QPushButton(get_icon('bulb_on'), "All On")
        self.all_on_button.clicked.connect(self.turn_group_on)
        power_layout.addWidget(self.all_on_button)
        
        self.all_off_button = QPushButton(get_icon('bulb_off'), "All Off")
        self.all_off_button.clicked.connect(self.turn_group_off)
        power_layout.addWidget(self.all_off_button)
        
        power_layout.addStretch(1)
        control_layout.addLayout(power_layout)
        
        # Brightness control
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("Brightness:"))
        
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(100)
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)
        brightness_layout.addWidget(self.brightness_slider)
        
        self.brightness_label = QLabel("100%")
        self.brightness_label.setFixedWidth(50)
        brightness_layout.addWidget(self.brightness_label)
        
        control_layout.addLayout(brightness_layout)
        
        # Color temperature control
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperature:"))
        
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(2000, 6500)
        self.temp_slider.setValue(4000)
        self.temp_slider.valueChanged.connect(self.on_temp_changed)
        temp_layout.addWidget(self.temp_slider)
        
        self.temp_label = QLabel("4000K")
        self.temp_label.setFixedWidth(50)
        temp_layout.addWidget(self.temp_label)
        
        control_layout.addLayout(temp_layout)
        
        # Scene selection
        scene_layout = QHBoxLayout()
        scene_layout.addWidget(QLabel("Scene:"))
        
        self.scene_combo = QComboBox()
        self.scene_combo.addItems([
            "Normal", "Reading", "Relax", "Energize", 
            "Concentrate", "Nightlight", "Movie"
        ])
        self.scene_combo.currentTextChanged.connect(self.on_scene_changed)
        scene_layout.addWidget(self.scene_combo)
        
        control_layout.addLayout(scene_layout)
        
        right_layout.addWidget(control_group)
        
        # Group members list
        members_group = QGroupBox("Group Members")
        members_layout = QVBoxLayout(members_group)
        
        self.members_list = QListWidget()
        members_layout.addWidget(self.members_list)
        
        right_layout.addWidget(members_group)
        
        # Set initial state of controls
        self.set_controls_enabled(False)
        
        layout.addWidget(right_panel)
    
    def load_groups(self):
        """Load groups from configuration"""
        self.group_list.clear()
        
        groups = self.config_manager.get_groups()
        
        for group in groups:
            item = QListWidgetItem(group.get('name', 'Unnamed Group'))
            item.setData(Qt.UserRole, group['id'])
            self.group_list.addItem(item)
    
    def on_group_selected(self, current, previous):
        """Handle group selection change"""
        if not current:
            self.current_group_id = None
            self.group_name_label.setText("No group selected")
            self.group_info_label.setText("")
            self.set_controls_enabled(False)
            self.members_list.clear()
            return
        
        # Get group ID from item
        self.current_group_id = current.data(Qt.UserRole)
        
        # Find group in configuration
        groups = self.config_manager.get_groups()
        group = next((g for g in groups if g.get('id') == self.current_group_id), None)
        
        if not group:
            logger.error(f"Cannot find group {self.current_group_id}")
            return
        
        # Update UI with group information
        self.group_name_label.setText(group.get('name', 'Unnamed Group'))
        self.group_info_label.setText(f"{len(group.get('lights', []))} lights")
        
        # Populate members list
        self.members_list.clear()
        
        for light_info in group.get('lights', []):
            protocol, light_id = light_info
            
            light = self.light_manager.get_light(protocol, light_id)
            if light:
                item = QListWidgetItem(light.get('name', 'Unknown Light'))
                item.setData(Qt.UserRole, light_info)
                self.members_list.addItem(item)
        
        # Enable controls
        self.set_controls_enabled(True)
    
    def set_controls_enabled(self, enabled):
        """Enable or disable group control widgets"""
        self.all_on_button.setEnabled(enabled)
        self.all_off_button.setEnabled(enabled)
        self.brightness_slider.setEnabled(enabled)
        self.temp_slider.setEnabled(enabled)
        self.scene_combo.setEnabled(enabled)
    
    def update_light_states(self):
        """Update UI to reflect current light states"""
        if not self.current_group_id:
            return
        
        # TODO: Implement logic to show mixed states when lights in
        # the group have different settings
    
    def turn_group_on(self):
        """Turn on all lights in the selected group"""
        if not self.current_group_id:
            return
        
        self.light_manager.set_group_state(self.current_group_id, {'on': True})
    
    def turn_group_off(self):
        """Turn off all lights in the selected group"""
        if not self.current_group_id:
            return
        
        self.light_manager.set_group_state(self.current_group_id, {'on': False})
    
    def on_brightness_changed(self, value):
        """Handle brightness slider change"""
        if not self.current_group_id:
            return
        
        # Update label
        self.brightness_label.setText(f"{value}%")
        
        # Set brightness for the group
        self.light_manager.set_group_state(
            self.current_group_id, {'brightness': value}
        )
    
    def on_temp_changed(self, value):
        """Handle temperature slider change"""
        if not self.current_group_id:
            return
        
        # Update label
        self.temp_label.setText(f"{value}K")
        
        # Set color temperature for the group
        self.light_manager.set_group_state(
            self.current_group_id, {'color_temp': value}
        )
    
    def on_scene_changed(self, scene_name):
        """Handle scene selection change"""
        if not self.current_group_id:
            return
        
        # Define scenes
        scenes = {
            "Normal": {'on': True, 'brightness': 100, 'color_temp': 4000},
            "Reading": {'on': True, 'brightness': 100, 'color_temp': 4700},
            "Relax": {'on': True, 'brightness': 60, 'color_temp': 2700},
            "Energize": {'on': True, 'brightness': 100, 'color_temp': 6500},
            "Concentrate": {'on': True, 'brightness': 100, 'color_temp': 5000},
            "Nightlight": {'on': True, 'brightness': 10, 'color_temp': 2300},
            "Movie": {'on': True, 'brightness': 30, 'color_temp': 2700}
        }
        
        # Apply scene if defined
        if scene_name in scenes:
            self.light_manager.set_group_state(
                self.current_group_id, scenes[scene_name]
            )
    
    def create_new_group(self):
        """Create a new light group"""
        dialog = GroupEditDialog(self.light_manager, self)
        if dialog.exec():
            group_name = dialog.name_edit.text().strip()
            selected_lights = dialog.get_selected_lights()
            
            if not group_name:
                QMessageBox.warning(
                    self, "Invalid Group", "Group name cannot be empty"
                )
                return
            
            if not selected_lights:
                QMessageBox.warning(
                    self, "Invalid Group", "Please select at least one light"
                )
                return
            
            # Create the group
            group_id = self.light_manager.create_group(group_name, selected_lights)
            
            if group_id:
                # Reload the group list
                self.load_groups()
                
                # Select the new group
                for i in range(self.group_list.count()):
                    item = self.group_list.item(i)
                    if item.data(Qt.UserRole) == group_id:
                        self.group_list.setCurrentItem(item)
                        break
            else:
                QMessageBox.critical(
                    self, "Error", "Failed to create group"
                )
    
    def edit_selected_group(self):
        """Edit the currently selected group"""
        if not self.current_group_id:
            QMessageBox.information(
                self, "No Selection", "Please select a group to edit"
            )
            return
        
        # Find group in configuration
        groups = self.config_manager.get_groups()
        group = next((g for g in groups if g.get('id') == self.current_group_id), None)
        
        if not group:
            logger.error(f"Cannot find group {self.current_group_id}")
            return
        
        dialog = GroupEditDialog(self.light_manager, self, group)
        if dialog.exec():
            group_name = dialog.name_edit.text().strip()
            selected_lights = dialog.get_selected_lights()
            
            if not group_name:
                QMessageBox.warning(
                    self, "Invalid Group", "Group name cannot be empty"
                )
                return
            
            if not selected_lights:
                QMessageBox.warning(
                    self, "Invalid Group", "Please select at least one light"
                )
                return
            
            # Update the group
            success = self.light_manager.update_group(
                self.current_group_id, name=group_name, light_ids=selected_lights
            )
            
            if success:
                # Reload the group list
                self.load_groups()
                
                # Update UI to reflect changes
                self.group_name_label.setText(group_name)
                self.group_info_label.setText(f"{len(selected_lights)} lights")
                
                # Refresh members list
                self.members_list.clear()
                
                for light_info in selected_lights:
                    protocol, light_id = light_info
                    
                    light = self.light_manager.get_light(protocol, light_id)
                    if light:
                        item = QListWidgetItem(light.get('name', 'Unknown Light'))
                        item.setData(Qt.UserRole, light_info)
                        self.members_list.addItem(item)
            else:
                QMessageBox.critical(
                    self, "Error", "Failed to update group"
                )
    
    def delete_selected_group(self):
        """Delete the currently selected group"""
        if not self.current_group_id:
            QMessageBox.information(
                self, "No Selection", "Please select a group to delete"
            )
            return
        
        # Confirm deletion
        result = QMessageBox.question(
            self, "Confirm Deletion",
            "Are you sure you want to delete this group?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            success = self.light_manager.delete_group(self.current_group_id)
            
            if success:
                # Remove from list
                for i in range(self.group_list.count()):
                    item = self.group_list.item(i)
                    if item.data(Qt.UserRole) == self.current_group_id:
                        self.group_list.takeItem(i)
                        break
                
                # Clear selection
                self.current_group_id = None
                self.group_name_label.setText("No group selected")
                self.group_info_label.setText("")
                self.set_controls_enabled(False)
                self.members_list.clear()
            else:
                QMessageBox.critical(
                    self, "Error", "Failed to delete group"
                )


class GroupEditDialog(QDialog):
    """
    Dialog for creating or editing a light group
    """
    
    def __init__(self, light_manager, parent=None, group=None):
        """
        Initialize group edit dialog
        
        Args:
            light_manager: LightManager instance
            parent: Parent widget
            group: Optional group data for editing (None for new group)
        """
        super().__init__(parent)
        self.light_manager = light_manager
        self.group = group
        
        self.setWindowTitle("Edit Group" if group else "Create Group")
        self.resize(500, 400)
        
        self.init_ui()
        
        # If editing, fill in group data
        if group:
            self.name_edit.setText(group.get('name', ''))
            self.select_group_lights(group.get('lights', []))
    
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Group name
        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        form_layout.addRow("Group Name:", self.name_edit)
        layout.addLayout(form_layout)
        
        # Available lights
        lights_group = QGroupBox("Select Lights for Group")
        lights_layout = QVBoxLayout(lights_group)
        
        # Get all lights
        all_lights = self.light_manager.get_all_lights()
        
        # Create checkboxes for lights
        self.light_checks = {}
        
        for light_id, light in all_lights.items():
            protocol = light.get('protocol')
            name = light.get('name', 'Unknown Light')
            
            checkbox = QCheckBox(name)
            checkbox.setToolTip(f"{protocol}: {light_id}")
            checkbox.setProperty("light_info", (protocol, light_id))
            
            lights_layout.addWidget(checkbox)
            self.light_checks[(protocol, light_id)] = checkbox
        
        lights_layout.addStretch(1)
        
        # Add scroll area for lights if there are many
        layout.addWidget(lights_group)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def select_group_lights(self, lights):
        """
        Select lights that are in the group
        
        Args:
            lights: List of (protocol, light_id) tuples
        """
        for light_info in lights:
            if light_info in self.light_checks:
                self.light_checks[light_info].setChecked(True)
    
    def get_selected_lights(self):
        """
        Get selected lights
        
        Returns:
            list: List of (protocol, light_id) tuples
        """
        selected = []
        
        for light_info, checkbox in self.light_checks.items():
            if checkbox.isChecked():
                selected.append(light_info)
        
        return selected
