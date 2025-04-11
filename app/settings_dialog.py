"""
Settings dialog for the Smart Light Controller application
"""

import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QComboBox, QGroupBox, QFormLayout, QTabWidget,
    QSpinBox, QDialogButtonBox
)
from PySide6.QtCore import Qt

from .constants import APP_NAME
from .ui.icons import get_icon


logger = logging.getLogger(APP_NAME)


class SettingsDialog(QDialog):
    """
    Dialog for managing application settings
    """
    
    def __init__(self, config_manager, parent=None):
        """Initialize settings dialog with config manager"""
        super().__init__(parent)
        self.config_manager = config_manager
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface components"""
        self.setWindowTitle("Settings")
        self.setWindowIcon(get_icon('settings'))
        self.resize(500, 400)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # General settings tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Create sections
        self.create_discovery_section(general_layout)
        self.create_ui_section(general_layout)
        general_layout.addStretch(1)
        
        # Advanced settings tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        self.create_network_section(advanced_layout)
        self.create_logging_section(advanced_layout)
        advanced_layout.addStretch(1)
        
        # Add tabs
        tab_widget.addTab(general_tab, "General")
        tab_widget.addTab(advanced_tab, "Advanced")
        
        layout.addWidget(tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def create_discovery_section(self, parent_layout):
        """Create device discovery settings section"""
        group_box = QGroupBox("Device Discovery")
        layout = QVBoxLayout()
        
        # Auto-discover devices
        self.auto_discover_check = QCheckBox("Auto-discover devices")
        self.auto_discover_check.setToolTip("Automatically search for devices when needed")
        layout.addWidget(self.auto_discover_check)
        
        # Discover on startup
        self.discover_startup_check = QCheckBox("Discover devices on startup")
        self.discover_startup_check.setToolTip("Search for new devices when the application starts")
        layout.addWidget(self.discover_startup_check)
        
        group_box.setLayout(layout)
        parent_layout.addWidget(group_box)
    
    def create_ui_section(self, parent_layout):
        """Create UI settings section"""
        group_box = QGroupBox("User Interface")
        layout = QVBoxLayout()
        
        # Dark mode
        self.dark_mode_check = QCheckBox("Dark mode")
        self.dark_mode_check.setToolTip("Use dark color theme for the application")
        layout.addWidget(self.dark_mode_check)
        
        # Notification level
        notification_layout = QHBoxLayout()
        notification_layout.addWidget(QLabel("Notification level:"))
        
        self.notification_combo = QComboBox()
        self.notification_combo.addItems(["Minimal", "Normal", "Verbose"])
        self.notification_combo.setToolTip("Control how many notifications are shown")
        notification_layout.addWidget(self.notification_combo)
        notification_layout.addStretch(1)
        
        layout.addLayout(notification_layout)
        
        # Check for updates
        self.check_updates_check = QCheckBox("Check for updates on startup")
        self.check_updates_check.setToolTip("Check for new application versions when starting")
        layout.addWidget(self.check_updates_check)
        
        group_box.setLayout(layout)
        parent_layout.addWidget(group_box)
    
    def create_network_section(self, parent_layout):
        """Create network settings section"""
        group_box = QGroupBox("Network")
        form_layout = QFormLayout()
        
        # Discovery timeout
        self.discovery_timeout_spin = QSpinBox()
        self.discovery_timeout_spin.setRange(1, 60)
        self.discovery_timeout_spin.setSuffix(" seconds")
        self.discovery_timeout_spin.setToolTip("How long to wait for devices to respond")
        form_layout.addRow("Discovery timeout:", self.discovery_timeout_spin)
        
        # Network retry attempts
        self.network_retry_spin = QSpinBox()
        self.network_retry_spin.setRange(0, 10)
        self.network_retry_spin.setToolTip("Number of times to retry failed network operations")
        form_layout.addRow("Network retry attempts:", self.network_retry_spin)
        
        group_box.setLayout(form_layout)
        parent_layout.addWidget(group_box)
    
    def create_logging_section(self, parent_layout):
        """Create logging settings section"""
        group_box = QGroupBox("Logging")
        form_layout = QFormLayout()
        
        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["Error", "Warning", "Info", "Debug"])
        self.log_level_combo.setToolTip("Control the detail level of application logs")
        form_layout.addRow("Log level:", self.log_level_combo)
        
        group_box.setLayout(form_layout)
        parent_layout.addWidget(group_box)
    
    def load_settings(self):
        """Load current settings into the UI"""
        settings = self.config_manager.config['settings']
        
        # Discovery settings
        self.auto_discover_check.setChecked(settings.get('auto_discover', True))
        self.discover_startup_check.setChecked(settings.get('discover_on_startup', True))
        
        # UI settings
        self.dark_mode_check.setChecked(settings.get('dark_mode', False))
        
        notification_level = settings.get('notification_level', 'normal')
        if notification_level == 'minimal':
            self.notification_combo.setCurrentIndex(0)
        elif notification_level == 'normal':
            self.notification_combo.setCurrentIndex(1)
        elif notification_level == 'verbose':
            self.notification_combo.setCurrentIndex(2)
        
        self.check_updates_check.setChecked(settings.get('startup_check_updates', True))
        
        # Network settings
        self.discovery_timeout_spin.setValue(settings.get('discovery_timeout', 5))
        self.network_retry_spin.setValue(settings.get('network_retry_count', 3))
        
        # Logging settings
        log_level = settings.get('log_level', 'info')
        if log_level == 'error':
            self.log_level_combo.setCurrentIndex(0)
        elif log_level == 'warning':
            self.log_level_combo.setCurrentIndex(1)
        elif log_level == 'info':
            self.log_level_combo.setCurrentIndex(2)
        elif log_level == 'debug':
            self.log_level_combo.setCurrentIndex(3)
    
    def accept(self):
        """Save settings and close dialog"""
        self.save_settings()
        super().accept()
    
    def save_settings(self):
        """Save settings from UI to configuration"""
        # Discovery settings
        self.config_manager.set_setting('auto_discover', self.auto_discover_check.isChecked())
        self.config_manager.set_setting('discover_on_startup', self.discover_startup_check.isChecked())
        
        # UI settings
        self.config_manager.set_setting('dark_mode', self.dark_mode_check.isChecked())
        
        notification_index = self.notification_combo.currentIndex()
        if notification_index == 0:
            self.config_manager.set_setting('notification_level', 'minimal')
        elif notification_index == 1:
            self.config_manager.set_setting('notification_level', 'normal')
        elif notification_index == 2:
            self.config_manager.set_setting('notification_level', 'verbose')
        
        self.config_manager.set_setting('startup_check_updates', self.check_updates_check.isChecked())
        
        # Network settings
        self.config_manager.set_setting('discovery_timeout', self.discovery_timeout_spin.value())
        self.config_manager.set_setting('network_retry_count', self.network_retry_spin.value())
        
        # Logging settings
        log_index = self.log_level_combo.currentIndex()
        if log_index == 0:
            self.config_manager.set_setting('log_level', 'error')
        elif log_index == 1:
            self.config_manager.set_setting('log_level', 'warning')
        elif log_index == 2:
            self.config_manager.set_setting('log_level', 'info')
        elif log_index == 3:
            self.config_manager.set_setting('log_level', 'debug')
        
        # Save to disk
        self.config_manager.save_config()
        logger.info("Settings saved")
