"""
Widget for managing light schedules
"""

import logging
from datetime import datetime, time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QDialog, QDialogButtonBox, 
    QFormLayout, QLineEdit, QGroupBox, QCheckBox, QMessageBox,
    QTimeEdit, QComboBox, QTabWidget, QScrollArea, QFrame, 
    QTreeWidget, QTreeWidgetItem, QDateEdit
)
from PySide6.QtCore import Qt, Slot, QTime, QDate

from ..constants import APP_NAME
from .icons import get_icon


logger = logging.getLogger(APP_NAME)


class ScheduleWidget(QWidget):
    """
    Widget for creating, editing, and managing light schedules
    """
    
    def __init__(self, scheduler_service, light_manager, config_manager, parent=None):
        """Initialize schedule widget with required services"""
        super().__init__(parent)
        self.scheduler_service = scheduler_service
        self.light_manager = light_manager
        self.config_manager = config_manager
        
        # Set up UI
        self.init_ui()
        
        # Connect signals
        self.scheduler_service.schedule_triggered.connect(self.on_schedule_triggered)
        self.scheduler_service.schedule_updated.connect(self.load_schedules)
        
        # Load schedules
        self.load_schedules()
    
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        layout = QHBoxLayout(self)
        
        # Left panel - schedules list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        list_label = QLabel("Schedules:")
        left_layout.addWidget(list_label)
        
        self.schedule_list = QListWidget()
        self.schedule_list.setMinimumWidth(200)
        self.schedule_list.currentItemChanged.connect(self.on_schedule_selected)
        left_layout.addWidget(self.schedule_list)
        
        layout.addWidget(left_panel)
        
        # Right panel - schedule details
        right_panel = QScrollArea()
        right_panel.setWidgetResizable(True)
        right_panel.setFrameShape(QFrame.NoFrame)
        
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Schedule info
        self.schedule_name_label = QLabel("No schedule selected")
        font = self.schedule_name_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.schedule_name_label.setFont(font)
        details_layout.addWidget(self.schedule_name_label)
        
        self.schedule_info_label = QLabel("")
        details_layout.addWidget(self.schedule_info_label)
        
        # Status and control
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Status: Inactive")
        status_layout.addWidget(self.status_label)
        
        self.enable_button = QPushButton("Enable")
        self.enable_button.setCheckable(True)
        self.enable_button.clicked.connect(self.on_enable_toggle)
        status_layout.addWidget(self.enable_button)
        
        self.run_now_button = QPushButton("Run Now")
        self.run_now_button.clicked.connect(self.on_run_now)
        status_layout.addWidget(self.run_now_button)
        
        status_layout.addStretch(1)
        details_layout.addLayout(status_layout)
        
        # Schedule details
        details_group = QGroupBox("Schedule Details")
        details_inner_layout = QFormLayout(details_group)
        
        self.time_label = QLabel("")
        details_inner_layout.addRow("Time:", self.time_label)
        
        self.days_label = QLabel("")
        details_inner_layout.addRow("Days:", self.days_label)
        
        self.date_label = QLabel("")
        details_inner_layout.addRow("Date:", self.date_label)
        
        self.last_run_label = QLabel("Never")
        details_inner_layout.addRow("Last Run:", self.last_run_label)
        
        self.next_run_label = QLabel("")
        details_inner_layout.addRow("Next Run:", self.next_run_label)
        
        details_layout.addWidget(details_group)
        
        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.actions_tree = QTreeWidget()
        self.actions_tree.setHeaderLabels(["Type", "Target", "Action"])
        self.actions_tree.setRootIsDecorated(False)
        self.actions_tree.setAlternatingRowColors(True)
        actions_layout.addWidget(self.actions_tree)
        
        details_layout.addWidget(actions_group)
        
        # Set the widget for the scroll area
        right_panel.setWidget(details_widget)
        
        # Add to the main layout
        layout.addWidget(right_panel)
        
        # Set initial state of controls
        self.set_controls_enabled(False)
    
    def load_schedules(self):
        """Load schedules from the scheduler service"""
        # Remember the current selection
        current_id = None
        if self.schedule_list.currentItem():
            current_id = self.schedule_list.currentItem().data(Qt.UserRole)
        
        # Clear the list
        self.schedule_list.clear()
        
        # Get schedules
        schedules = self.scheduler_service.get_schedules()
        
        # Add each schedule to the list
        for schedule_id, schedule in schedules.items():
            name = schedule.get('name', 'Unnamed Schedule')
            time_str = schedule.get('time', '')
            
            item = QListWidgetItem(f"{name} ({time_str})")
            item.setData(Qt.UserRole, schedule_id)
            
            # Set icon based on enabled state
            if schedule.get('enabled', True):
                item.setIcon(get_icon('schedule'))
            else:
                item.setIcon(get_icon('warning'))
            
            self.schedule_list.addItem(item)
        
        # Restore selection if possible
        if current_id:
            for i in range(self.schedule_list.count()):
                item = self.schedule_list.item(i)
                if item.data(Qt.UserRole) == current_id:
                    self.schedule_list.setCurrentItem(item)
                    break
    
    def on_schedule_selected(self, current, previous):
        """Handle schedule selection change"""
        if not current:
            self.schedule_name_label.setText("No schedule selected")
            self.schedule_info_label.setText("")
            self.set_controls_enabled(False)
            return
        
        # Get schedule ID from item
        schedule_id = current.data(Qt.UserRole)
        
        # Get schedule from service
        schedule = self.scheduler_service.get_schedule(schedule_id)
        
        if not schedule:
            logger.error(f"Cannot find schedule {schedule_id}")
            return
        
        # Update UI with schedule information
        self.update_schedule_display(schedule)
        
        # Enable controls
        self.set_controls_enabled(True)
    
    def update_schedule_display(self, schedule):
        """Update the UI with schedule details"""
        name = schedule.get('name', 'Unnamed Schedule')
        self.schedule_name_label.setText(name)
        
        # Set info text
        info_text = "Runs "
        if 'days' in schedule:
            days = schedule['days']
            if isinstance(days, list):
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_text = ', '.join([day_names[d] for d in days])
                info_text += f"every {day_text} "
            elif days == 'weekdays':
                info_text += "on weekdays "
            elif days == 'weekend':
                info_text += "on weekends "
            elif days == 'all':
                info_text += "every day "
        elif 'date' in schedule:
            date_obj = datetime.fromisoformat(schedule['date'])
            info_text += f"on {date_obj.strftime('%B %d, %Y')} "
        
        if 'time' in schedule:
            info_text += f"at {schedule['time']}"
        
        self.schedule_info_label.setText(info_text)
        
        # Set status
        enabled = schedule.get('enabled', True)
        self.status_label.setText(f"Status: {'Active' if enabled else 'Inactive'}")
        self.enable_button.setChecked(enabled)
        self.enable_button.setText("Disable" if enabled else "Enable")
        
        # Set schedule details
        self.time_label.setText(schedule.get('time', ''))
        
        # Set days
        if 'days' in schedule:
            days = schedule['days']
            if isinstance(days, list):
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                self.days_label.setText(', '.join([day_names[d] for d in days]))
            else:
                self.days_label.setText(days.capitalize())
        else:
            self.days_label.setText("N/A")
        
        # Set date
        if 'date' in schedule:
            date_obj = datetime.fromisoformat(schedule['date'])
            self.date_label.setText(date_obj.strftime('%Y-%m-%d'))
        else:
            self.date_label.setText("N/A")
        
        # Set last run
        last_run = schedule.get('last_run')
        if last_run:
            last_datetime = datetime.fromisoformat(last_run)
            self.last_run_label.setText(last_datetime.strftime('%Y-%m-%d %H:%M'))
        else:
            self.last_run_label.setText("Never")
        
        # Set next run (would need to calculate this)
        self.next_run_label.setText("Calculating...")
        
        # Fill actions tree
        self.actions_tree.clear()
        
        for action in schedule.get('actions', []):
            action_type = action.get('type', '')
            target_type = action.get('target_type', '')
            
            # Format the target string
            target_str = "Unknown"
            if target_type == 'light':
                protocol, light_id = action.get('target_id', '').split('/')
                light = self.light_manager.get_light(protocol, light_id)
                if light:
                    target_str = light.get('name', 'Unknown Light')
            elif target_type == 'group':
                group_id = action.get('target_id', '')
                groups = self.config_manager.get_groups()
                group = next((g for g in groups if g.get('id') == group_id), None)
                if group:
                    target_str = group.get('name', 'Unknown Group')
            elif target_type == 'all':
                target_str = "All Lights"
            
            # Format the action string
            action_str = "Unknown"
            state = action.get('state', {})
            if 'on' in state:
                action_str = f"Turn {'On' if state['on'] else 'Off'}"
                
                # Add brightness if turning on
                if state['on'] and 'brightness' in state:
                    action_str += f", Brightness: {state['brightness']}%"
                
                # Add color temp if specified
                if state['on'] and 'color_temp' in state:
                    action_str += f", Temp: {state['color_temp']}K"
            
            # Create the item
            item = QTreeWidgetItem([action_type.capitalize(), target_str, action_str])
            self.actions_tree.addTopLevelItem(item)
        
        # Auto resize columns
        for i in range(3):
            self.actions_tree.resizeColumnToContents(i)
    
    def set_controls_enabled(self, enabled):
        """Enable or disable schedule control widgets"""
        self.enable_button.setEnabled(enabled)
        self.run_now_button.setEnabled(enabled)
    
    def on_enable_toggle(self, checked):
        """Handle schedule enable/disable"""
        if not self.schedule_list.currentItem():
            return
        
        schedule_id = self.schedule_list.currentItem().data(Qt.UserRole)
        
        # Update enable state
        self.scheduler_service.enable_schedule(schedule_id, checked)
        
        # Update button text
        self.enable_button.setText("Disable" if checked else "Enable")
        
        # Update status label
        self.status_label.setText(f"Status: {'Active' if checked else 'Inactive'}")
        
        # Reload schedules to update icons
        self.load_schedules()
    
    def on_run_now(self):
        """Run the selected schedule immediately"""
        if not self.schedule_list.currentItem():
            return
        
        schedule_id = self.schedule_list.currentItem().data(Qt.UserRole)
        
        # Trigger the schedule
        self.scheduler_service._trigger_schedule(schedule_id)
    
    def on_schedule_triggered(self, schedule_id):
        """Handle schedule trigger event"""
        # Update the display if this is the currently selected schedule
        if (self.schedule_list.currentItem() and 
                self.schedule_list.currentItem().data(Qt.UserRole) == schedule_id):
            schedule = self.scheduler_service.get_schedule(schedule_id)
            if schedule:
                self.update_schedule_display(schedule)
    
    def create_new_schedule(self):
        """Create a new schedule"""
        dialog = ScheduleEditDialog(self.light_manager, self.config_manager, self)
        if dialog.exec():
            # Get schedule data from dialog
            name = dialog.name_edit.text().strip()
            time_str = dialog.time_edit.time().toString("HH:mm")
            enabled = dialog.enabled_check.isChecked()
            
            # Get day/date information
            days = None
            date = None
            
            if dialog.repeat_combo.currentText() == "Specific Date":
                date_obj = dialog.date_edit.date()
                date_time = datetime(
                    date_obj.year(), date_obj.month(), date_obj.day()
                )
                date = date_time.isoformat()
            else:
                repeat_type = dialog.repeat_combo.currentText()
                if repeat_type == "Every Day":
                    days = "all"
                elif repeat_type == "Weekdays":
                    days = "weekdays"
                elif repeat_type == "Weekend":
                    days = "weekend"
                elif repeat_type == "Custom":
                    days = []
                    day_checks = [
                        dialog.mon_check, dialog.tue_check, dialog.wed_check,
                        dialog.thu_check, dialog.fri_check, dialog.sat_check,
                        dialog.sun_check
                    ]
                    for i, check in enumerate(day_checks):
                        if check.isChecked():
                            days.append(i)
            
            # Get actions
            actions = dialog.get_actions()
            
            # Create schedule
            schedule_id = self.scheduler_service.create_schedule(
                name, time_str, actions, days, date, enabled
            )
            
            if schedule_id:
                # Schedule created successfully
                self.load_schedules()
                
                # Select the new schedule
                for i in range(self.schedule_list.count()):
                    item = self.schedule_list.item(i)
                    if item.data(Qt.UserRole) == schedule_id:
                        self.schedule_list.setCurrentItem(item)
                        break
            else:
                QMessageBox.critical(
                    self, "Error", "Failed to create schedule"
                )
    
    def edit_selected_schedule(self):
        """Edit the currently selected schedule"""
        if not self.schedule_list.currentItem():
            QMessageBox.information(
                self, "No Selection", "Please select a schedule to edit"
            )
            return
        
        schedule_id = self.schedule_list.currentItem().data(Qt.UserRole)
        schedule = self.scheduler_service.get_schedule(schedule_id)
        
        if not schedule:
            logger.error(f"Cannot find schedule {schedule_id}")
            return
        
        dialog = ScheduleEditDialog(
            self.light_manager, self.config_manager, self, schedule
        )
        
        if dialog.exec():
            # Get schedule data from dialog
            name = dialog.name_edit.text().strip()
            time_str = dialog.time_edit.time().toString("HH:mm")
            enabled = dialog.enabled_check.isChecked()
            
            # Get day/date information
            days = None
            date = None
            
            if dialog.repeat_combo.currentText() == "Specific Date":
                date_obj = dialog.date_edit.date()
                date_time = datetime(
                    date_obj.year(), date_obj.month(), date_obj.day()
                )
                date = date_time.isoformat()
            else:
                repeat_type = dialog.repeat_combo.currentText()
                if repeat_type == "Every Day":
                    days = "all"
                elif repeat_type == "Weekdays":
                    days = "weekdays"
                elif repeat_type == "Weekend":
                    days = "weekend"
                elif repeat_type == "Custom":
                    days = []
                    day_checks = [
                        dialog.mon_check, dialog.tue_check, dialog.wed_check,
                        dialog.thu_check, dialog.fri_check, dialog.sat_check,
                        dialog.sun_check
                    ]
                    for i, check in enumerate(day_checks):
                        if check.isChecked():
                            days.append(i)
            
            # Get actions
            actions = dialog.get_actions()
            
            # Update schedule
            updates = {
                'name': name,
                'time': time_str,
                'actions': actions,
                'enabled': enabled
            }
            
            if days is not None:
                updates['days'] = days
                # Remove date if it was set before
                updates['date'] = None
            elif date is not None:
                updates['date'] = date
                # Remove days if it was set before
                updates['days'] = None
            
            success = self.scheduler_service.update_schedule(schedule_id, **updates)
            
            if success:
                # Schedule updated successfully
                self.load_schedules()
                
                # Update display
                schedule = self.scheduler_service.get_schedule(schedule_id)
                if schedule:
                    self.update_schedule_display(schedule)
            else:
                QMessageBox.critical(
                    self, "Error", "Failed to update schedule"
                )
    
    def delete_selected_schedule(self):
        """Delete the currently selected schedule"""
        if not self.schedule_list.currentItem():
            QMessageBox.information(
                self, "No Selection", "Please select a schedule to delete"
            )
            return
        
        schedule_id = self.schedule_list.currentItem().data(Qt.UserRole)
        
        # Confirm deletion
        result = QMessageBox.question(
            self, "Confirm Deletion",
            "Are you sure you want to delete this schedule?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            success = self.scheduler_service.delete_schedule(schedule_id)
            
            if success:
                # Remove from list
                self.schedule_list.takeItem(self.schedule_list.currentRow())
                
                # Clear selection
                self.schedule_name_label.setText("No schedule selected")
                self.schedule_info_label.setText("")
                self.set_controls_enabled(False)
                self.actions_tree.clear()
            else:
                QMessageBox.critical(
                    self, "Error", "Failed to delete schedule"
                )


class ScheduleEditDialog(QDialog):
    """
    Dialog for creating or editing a schedule
    """
    
    def __init__(self, light_manager, config_manager, parent=None, schedule=None):
        """
        Initialize schedule edit dialog
        
        Args:
            light_manager: LightManager instance
            config_manager: ConfigManager instance
            parent: Parent widget
            schedule: Optional schedule data for editing (None for new schedule)
        """
        super().__init__(parent)
        self.light_manager = light_manager
        self.config_manager = config_manager
        self.schedule = schedule
        
        self.setWindowTitle("Edit Schedule" if schedule else "Create Schedule")
        self.resize(600, 500)
        
        self.init_ui()
        
        # If editing, fill in schedule data
        if schedule:
            self.populate_from_schedule(schedule)
    
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Basic information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        basic_layout.addRow("Name:", self.name_edit)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())
        basic_layout.addRow("Time:", self.time_edit)
        
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(True)
        basic_layout.addRow("", self.enabled_check)
        
        layout.addWidget(basic_group)
        
        # Repeat settings
        repeat_group = QGroupBox("Repeat Settings")
        repeat_layout = QVBoxLayout(repeat_group)
        
        repeat_form = QFormLayout()
        self.repeat_combo = QComboBox()
        self.repeat_combo.addItems([
            "Every Day", "Weekdays", "Weekend", "Custom", "Specific Date"
        ])
        self.repeat_combo.currentTextChanged.connect(self.on_repeat_changed)
        repeat_form.addRow("Repeat:", self.repeat_combo)
        repeat_layout.addLayout(repeat_form)
        
        # Custom days selection
        self.custom_days_widget = QWidget()
        days_layout = QHBoxLayout(self.custom_days_widget)
        days_layout.setContentsMargins(0, 0, 0, 0)
        
        self.mon_check = QCheckBox("Mon")
        days_layout.addWidget(self.mon_check)
        
        self.tue_check = QCheckBox("Tue")
        days_layout.addWidget(self.tue_check)
        
        self.wed_check = QCheckBox("Wed")
        days_layout.addWidget(self.wed_check)
        
        self.thu_check = QCheckBox("Thu")
        days_layout.addWidget(self.thu_check)
        
        self.fri_check = QCheckBox("Fri")
        days_layout.addWidget(self.fri_check)
        
        self.sat_check = QCheckBox("Sat")
        days_layout.addWidget(self.sat_check)
        
        self.sun_check = QCheckBox("Sun")
        days_layout.addWidget(self.sun_check)
        
        repeat_layout.addWidget(self.custom_days_widget)
        self.custom_days_widget.hide()  # Initially hidden
        
        # Specific date selection
        self.date_widget = QWidget()
        date_layout = QHBoxLayout(self.date_widget)
        date_layout.setContentsMargins(0, 0, 0, 0)
        
        date_layout.addWidget(QLabel("Date:"))
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_edit)
        
        date_layout.addStretch(1)
        
        repeat_layout.addWidget(self.date_widget)
        self.date_widget.hide()  # Initially hidden
        
        layout.addWidget(repeat_group)
        
        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        # Tab widget for different action types
        action_tabs = QTabWidget()
        
        # Light control tab
        light_tab = QWidget()
        light_layout = QFormLayout(light_tab)
        
        self.target_combo = QComboBox()
        self.target_combo.addItem("All Lights", ("all", ""))
        
        # Add groups
        groups = self.config_manager.get_groups()
        for group in groups:
            self.target_combo.addItem(
                f"Group: {group.get('name', 'Unnamed')}",
                ("group", group.get('id', ''))
            )
        
        # Add individual lights
        lights = self.light_manager.get_all_lights()
        for light_id, light in lights.items():
            protocol = light.get('protocol')
            name = light.get('name', 'Unknown Light')
            self.target_combo.addItem(
                f"Light: {name}",
                ("light", f"{protocol}/{light_id}")
            )
        
        light_layout.addRow("Target:", self.target_combo)
        
        self.light_state_combo = QComboBox()
        self.light_state_combo.addItems(["Turn On", "Turn Off"])
        self.light_state_combo.currentTextChanged.connect(self.on_light_state_changed)
        light_layout.addRow("Action:", self.light_state_combo)
        
        # Settings for turn on action
        self.light_settings_widget = QWidget()
        light_settings_layout = QFormLayout(self.light_settings_widget)
        light_settings_layout.setContentsMargins(0, 0, 0, 0)
        
        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(100)
        
        self.brightness_label = QLabel("100%")
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(self.brightness_slider)
        brightness_layout.addWidget(self.brightness_label)
        
        self.brightness_slider.valueChanged.connect(
            lambda value: self.brightness_label.setText(f"{value}%")
        )
        
        light_settings_layout.addRow("Brightness:", brightness_layout)
        
        self.color_temp_slider = QSlider(Qt.Horizontal)
        self.color_temp_slider.setRange(2000, 6500)
        self.color_temp_slider.setValue(4000)
        
        self.color_temp_label = QLabel("4000K")
        color_temp_layout = QHBoxLayout()
        color_temp_layout.addWidget(self.color_temp_slider)
        color_temp_layout.addWidget(self.color_temp_label)
        
        self.color_temp_slider.valueChanged.connect(
            lambda value: self.color_temp_label.setText(f"{value}K")
        )
        
        light_settings_layout.addRow("Color Temp:", color_temp_layout)
        
        light_layout.addRow("", self.light_settings_widget)
        
        action_tabs.addTab(light_tab, "Light Control")
        
        # Could add more action tabs here (scenes, effects, etc.)
        
        actions_layout.addWidget(action_tabs)
        
        layout.addWidget(actions_group)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Initial state updates
        self.on_light_state_changed(self.light_state_combo.currentText())
    
    def on_repeat_changed(self, repeat_type):
        """Handle repeat type change"""
        self.custom_days_widget.setVisible(repeat_type == "Custom")
        self.date_widget.setVisible(repeat_type == "Specific Date")
    
    def on_light_state_changed(self, state):
        """Handle light state change"""
        self.light_settings_widget.setVisible(state == "Turn On")
    
    def populate_from_schedule(self, schedule):
        """
        Fill in dialog fields from schedule data
        
        Args:
            schedule: Schedule data dictionary
        """
        # Basic info
        self.name_edit.setText(schedule.get('name', ''))
        
        if 'time' in schedule:
            time_parts = schedule['time'].split(':')
            if len(time_parts) == 2:
                hours, minutes = map(int, time_parts)
                self.time_edit.setTime(QTime(hours, minutes))
        
        self.enabled_check.setChecked(schedule.get('enabled', True))
        
        # Repeat settings
        if 'date' in schedule:
            self.repeat_combo.setCurrentText("Specific Date")
            date_obj = datetime.fromisoformat(schedule['date'])
            self.date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
        elif 'days' in schedule:
            days = schedule['days']
            if isinstance(days, list):
                self.repeat_combo.setCurrentText("Custom")
                day_checks = [
                    self.mon_check, self.tue_check, self.wed_check,
                    self.thu_check, self.fri_check, self.sat_check,
                    self.sun_check
                ]
                for i, check in enumerate(day_checks):
                    check.setChecked(i in days)
            else:
                if days == 'all':
                    self.repeat_combo.setCurrentText("Every Day")
                elif days == 'weekdays':
                    self.repeat_combo.setCurrentText("Weekdays")
                elif days == 'weekend':
                    self.repeat_combo.setCurrentText("Weekend")
        
        # Actions (just handle the first action for now)
        actions = schedule.get('actions', [])
        if actions:
            action = actions[0]
            target_type = action.get('target_type')
            target_id = action.get('target_id', '')
            
            # Set target
            for i in range(self.target_combo.count()):
                item_type, item_id = self.target_combo.itemData(i)
                if item_type == target_type and item_id == target_id:
                    self.target_combo.setCurrentIndex(i)
                    break
            
            # Set action
            state = action.get('state', {})
            if 'on' in state:
                self.light_state_combo.setCurrentText("Turn On" if state['on'] else "Turn Off")
                
                if state['on']:
                    # Set brightness
                    if 'brightness' in state:
                        self.brightness_slider.setValue(state['brightness'])
                    
                    # Set color temperature
                    if 'color_temp' in state:
                        self.color_temp_slider.setValue(state['color_temp'])
    
    def get_actions(self):
        """
        Get actions from dialog fields
        
        Returns:
            list: List of action dictionaries
        """
        actions = []
        
        # Get target
        target_index = self.target_combo.currentIndex()
        target_type, target_id = self.target_combo.itemData(target_index)
        
        # Get state
        state = {}
        if self.light_state_combo.currentText() == "Turn On":
            state['on'] = True
            state['brightness'] = self.brightness_slider.value()
            state['color_temp'] = self.color_temp_slider.value()
        else:
            state['on'] = False
        
        # Create action
        action = {
            'type': 'set_state',
            'target_type': target_type,
            'target_id': target_id,
            'state': state
        }
        
        actions.append(action)
        
        return actions
