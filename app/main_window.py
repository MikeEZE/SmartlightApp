"""
Main application window for the Smart Light Controller
"""

import logging
import sys
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QMessageBox, QMenu, QToolBar,
    QStatusBar, QSplitter, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QTimer, QSize, Slot, Signal
from PySide6.QtGui import QIcon, QAction, QKeySequence

from .constants import APP_NAME, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
from .light_manager import LightManager
from .discovery_service import DiscoveryService
from .scheduler import SchedulerService
from .settings_dialog import SettingsDialog
from .ui.status_bar import StatusBar
from .ui.light_control_widget import LightControlWidget
from .ui.light_group_widget import LightGroupWidget
from .ui.schedule_widget import ScheduleWidget
from .ui.icons import get_icon


logger = logging.getLogger(APP_NAME)


class MainWindow(QMainWindow):
    """
    Main application window containing the UI and connecting all components
    """
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.light_manager = LightManager(config_manager)
        self.discovery_service = DiscoveryService(self.light_manager)
        self.scheduler_service = SchedulerService(self.light_manager, config_manager)
        
        # Initialize UI
        self.init_ui()
        
        # Set up timers for periodic updates
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update status every 5 seconds
        
        # Auto-discover devices if configured
        if self.config_manager.get_setting('discover_on_startup', True):
            QTimer.singleShot(500, self.discover_devices)
    
    def init_ui(self):
        """Initialize the user interface components"""
        # Set window properties
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(get_icon('app'))
        
        # Set window size from saved config
        window_settings = self.config_manager.get_window_settings()
        self.resize(
            window_settings.get('width', DEFAULT_WINDOW_WIDTH),
            window_settings.get('height', DEFAULT_WINDOW_HEIGHT)
        )
        
        # Set window position if saved
        if window_settings.get('position_x') and window_settings.get('position_y'):
            self.move(window_settings['position_x'], window_settings['position_y'])
        
        # Maximize if that was the last state
        if window_settings.get('maximized', False):
            self.showMaximized()
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create main splitter and areas
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # Left panel - devices and groups
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        
        # Right panel - control area
        self.right_panel = QScrollArea()
        self.right_panel.setWidgetResizable(True)
        self.right_panel.setFrameShape(QFrame.NoFrame)
        
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.right_panel)
        self.main_splitter.setSizes([300, 700])  # Default sizes for panels
        
        # Tab widget for main content
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.right_panel.setWidget(self.tab_widget)
        
        # Create tabs
        self.devices_tab = QWidget()
        self.groups_tab = QWidget()
        self.schedules_tab = QWidget()
        
        self.setup_devices_tab()
        self.setup_groups_tab()
        self.setup_schedules_tab()
        
        self.tab_widget.addTab(self.devices_tab, get_icon('lightbulb'), "Devices")
        self.tab_widget.addTab(self.groups_tab, get_icon('group'), "Groups")
        self.tab_widget.addTab(self.schedules_tab, get_icon('schedule'), "Schedules")
        
        # Status Bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)
        
        # Connect signals to slots
        self.connect_signals()
        
        # Load devices from configuration
        self.load_saved_devices()
    
    def create_menu_bar(self):
        """Create the application menu bar"""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        refresh_action = QAction(get_icon('refresh'), "&Refresh Devices", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self.refresh_devices)
        file_menu.addAction(refresh_action)
        
        discover_action = QAction(get_icon('discover'), "&Discover Devices", self)
        discover_action.setShortcut(QKeySequence("Ctrl+D"))
        discover_action.triggered.connect(self.discover_devices)
        file_menu.addAction(discover_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction(get_icon('settings'), "&Settings", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(get_icon('exit'), "E&xit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = self.menuBar().addMenu("&View")
        
        toggle_toolbar_action = QAction("Show &Toolbar", self)
        toggle_toolbar_action.setCheckable(True)
        toggle_toolbar_action.setChecked(True)
        toggle_toolbar_action.triggered.connect(
            lambda checked: self.toolbar.setVisible(checked)
        )
        view_menu.addAction(toggle_toolbar_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        
        about_action = QAction(get_icon('about'), "&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create the toolbar with quick actions"""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        
        # Add toolbar actions
        refresh_action = QAction(get_icon('refresh'), "Refresh", self)
        refresh_action.triggered.connect(self.refresh_devices)
        self.toolbar.addAction(refresh_action)
        
        discover_action = QAction(get_icon('discover'), "Discover", self)
        discover_action.triggered.connect(self.discover_devices)
        self.toolbar.addAction(discover_action)
        
        self.toolbar.addSeparator()
        
        all_on_action = QAction(get_icon('bulb_on'), "All On", self)
        all_on_action.triggered.connect(lambda: self.light_manager.set_all_lights(True))
        self.toolbar.addAction(all_on_action)
        
        all_off_action = QAction(get_icon('bulb_off'), "All Off", self)
        all_off_action.triggered.connect(lambda: self.light_manager.set_all_lights(False))
        self.toolbar.addAction(all_off_action)
        
        self.toolbar.addSeparator()
        
        settings_action = QAction(get_icon('settings'), "Settings", self)
        settings_action.triggered.connect(self.show_settings)
        self.toolbar.addAction(settings_action)
    
    def setup_devices_tab(self):
        """Set up the devices tab layout and content"""
        layout = QVBoxLayout(self.devices_tab)
        
        # Instructions label
        instructions = QLabel(
            "Control your smart lights individually. Select a light from the left panel to control it."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Device control widget (will be populated when a device is selected)
        self.device_control_widget = LightControlWidget(self.light_manager)
        layout.addWidget(self.device_control_widget)
        
        # Stretch to fill available space
        layout.addStretch(1)
    
    def setup_groups_tab(self):
        """Set up the groups tab layout and content"""
        layout = QVBoxLayout(self.groups_tab)
        
        # Instructions
        instructions = QLabel(
            "Create and manage groups of lights to control multiple lights simultaneously."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Group management controls
        group_controls = QHBoxLayout()
        
        create_group_btn = QPushButton(get_icon('add'), "Create Group")
        create_group_btn.clicked.connect(self.create_new_group)
        group_controls.addWidget(create_group_btn)
        
        edit_group_btn = QPushButton(get_icon('edit'), "Edit Group")
        edit_group_btn.clicked.connect(self.edit_selected_group)
        group_controls.addWidget(edit_group_btn)
        
        delete_group_btn = QPushButton(get_icon('delete'), "Delete Group")
        delete_group_btn.clicked.connect(self.delete_selected_group)
        group_controls.addWidget(delete_group_btn)
        
        group_controls.addStretch(1)
        layout.addLayout(group_controls)
        
        # Group control widget
        self.group_widget = LightGroupWidget(self.light_manager, self.config_manager)
        layout.addWidget(self.group_widget)
        
        # Stretch to fill available space
        layout.addStretch(1)
    
    def setup_schedules_tab(self):
        """Set up the schedules tab layout and content"""
        layout = QVBoxLayout(self.schedules_tab)
        
        # Instructions
        instructions = QLabel(
            "Create schedules to automate your lights based on time of day or specific events."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Schedule management controls
        schedule_controls = QHBoxLayout()
        
        create_schedule_btn = QPushButton(get_icon('add'), "Create Schedule")
        create_schedule_btn.clicked.connect(self.create_new_schedule)
        schedule_controls.addWidget(create_schedule_btn)
        
        edit_schedule_btn = QPushButton(get_icon('edit'), "Edit Schedule")
        edit_schedule_btn.clicked.connect(self.edit_selected_schedule)
        schedule_controls.addWidget(edit_schedule_btn)
        
        delete_schedule_btn = QPushButton(get_icon('delete'), "Delete Schedule")
        delete_schedule_btn.clicked.connect(self.delete_selected_schedule)
        schedule_controls.addWidget(delete_schedule_btn)
        
        schedule_controls.addStretch(1)
        layout.addLayout(schedule_controls)
        
        # Schedule widget
        self.schedule_widget = ScheduleWidget(
            self.scheduler_service, self.light_manager, self.config_manager
        )
        layout.addWidget(self.schedule_widget)
        
        # Stretch to fill available space
        layout.addStretch(1)
    
    def connect_signals(self):
        """Connect signals to slots for event handling"""
        # Connect light manager signals
        self.light_manager.devices_updated.connect(self.update_device_list)
        self.light_manager.light_state_changed.connect(self.handle_light_state_change)
        
        # Connect discovery service signals
        self.discovery_service.discovery_started.connect(
            lambda: self.status_bar.show_message("Discovering devices...")
        )
        self.discovery_service.discovery_finished.connect(
            lambda success: self.status_bar.show_message(
                "Device discovery completed" if success else "Device discovery failed"
            )
        )
        self.discovery_service.device_discovered.connect(
            lambda protocol, device: self.status_bar.show_message(
                f"Discovered {protocol} device: {device.get('name', 'Unknown')}"
            )
        )
    
    def load_saved_devices(self):
        """Load devices from saved configuration"""
        # Load Hue bridges
        for bridge in self.config_manager.get_devices('hue'):
            self.light_manager.add_hue_bridge(bridge)
        
        # Load LIFX lights
        for light in self.config_manager.get_devices('lifx'):
            self.light_manager.add_lifx_light(light)
    
    @Slot()
    def update_device_list(self):
        """Update the device list in the UI when devices change"""
        # This would update the device tree in the left panel
        # For now, just show a status message
        self.status_bar.show_message("Devices updated")
    
    @Slot(str, str, dict)
    def handle_light_state_change(self, protocol, light_id, state):
        """Handle light state changes to update UI"""
        # Update device control widget if the currently selected light changed
        self.device_control_widget.update_if_match(protocol, light_id)
        
        # Update group widget to reflect light state changes
        self.group_widget.update_light_states()
    
    @Slot()
    def discover_devices(self):
        """Start device discovery process"""
        self.discovery_service.discover_devices()
    
    @Slot()
    def refresh_devices(self):
        """Refresh the status of existing devices"""
        self.light_manager.refresh_all_devices()
        self.status_bar.show_message("Refreshing all devices...")
    
    @Slot()
    def create_new_group(self):
        """Create a new light group"""
        self.group_widget.create_new_group()
    
    @Slot()
    def edit_selected_group(self):
        """Edit the currently selected group"""
        self.group_widget.edit_selected_group()
    
    @Slot()
    def delete_selected_group(self):
        """Delete the currently selected group"""
        self.group_widget.delete_selected_group()
    
    @Slot()
    def create_new_schedule(self):
        """Create a new schedule"""
        self.schedule_widget.create_new_schedule()
    
    @Slot()
    def edit_selected_schedule(self):
        """Edit the currently selected schedule"""
        self.schedule_widget.edit_selected_schedule()
    
    @Slot()
    def delete_selected_schedule(self):
        """Delete the currently selected schedule"""
        self.schedule_widget.delete_selected_schedule()
    
    @Slot()
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.config_manager, self)
        dialog.exec()
        
        # Apply any settings changes that affect the UI
        # (would be implemented as needed)
    
    @Slot()
    def show_about(self):
        """Show about dialog with application information"""
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h2>{APP_NAME}</h2>"
            "<p>A Windows desktop application for controlling multiple brands of smart lights.</p>"
            "<p>Supports Philips Hue and LIFX smart lighting systems.</p>"
            "<p>© 2023 Smart Light Controller Project</p>"
        )
    
    @Slot()
    def update_status(self):
        """Periodic status update for devices"""
        connected_count = self.light_manager.get_connected_device_count()
        total_count = self.light_manager.get_total_device_count()
        
        if total_count > 0:
            self.status_bar.update_device_status(connected_count, total_count)
        else:
            self.status_bar.update_device_status(0, 0)
    
    def closeEvent(self, event):
        """Handle window close event to save settings"""
        # Save window state
        window_settings = {
            'maximized': self.isMaximized(),
            'width': self.width(),
            'height': self.height(),
            'position_x': self.x(),
            'position_y': self.y()
        }
        self.config_manager.update_window_settings(window_settings)
        
        # Save configuration
        self.config_manager.save_config()
        
        # Stop scheduler
        self.scheduler_service.stop()
        
        # Accept the close event
        event.accept()
