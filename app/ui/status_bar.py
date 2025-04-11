"""
Status bar for the Smart Light Controller application
"""

import logging
from PySide6.QtWidgets import QStatusBar, QLabel, QWidget, QHBoxLayout, QProgressBar
from PySide6.QtCore import Qt, QTimer

from ..constants import APP_NAME


logger = logging.getLogger(APP_NAME)


class StatusBar(QStatusBar):
    """
    Custom status bar with device status indicators
    """
    
    def __init__(self, parent=None):
        """Initialize status bar"""
        super().__init__(parent)
        
        # Create widgets
        self.init_ui()
        
        # Message timeout
        self.message_timer = QTimer(self)
        self.message_timer.timeout.connect(self.clear_message)
        self.message_timer.setSingleShot(True)
    
    def init_ui(self):
        """Initialize the user interface components"""
        # Left side: status message
        self.message_label = QLabel("")
        self.addWidget(self.message_label, 1)
        
        # Right side: status indicators
        self.device_status = DeviceStatusWidget()
        self.addPermanentWidget(self.device_status)
    
    def show_message(self, message, timeout=5000):
        """
        Show a status message with timeout
        
        Args:
            message: Message text
            timeout: Timeout in milliseconds (0 for no timeout)
        """
        self.message_label.setText(message)
        
        # Reset timer if already running
        if self.message_timer.isActive():
            self.message_timer.stop()
        
        # Start timer if timeout specified
        if timeout > 0:
            self.message_timer.start(timeout)
    
    def clear_message(self):
        """Clear the status message"""
        self.message_label.clear()
    
    def update_device_status(self, connected_count, total_count):
        """
        Update device status indicators
        
        Args:
            connected_count: Number of connected devices
            total_count: Total number of devices
        """
        self.device_status.update_status(connected_count, total_count)


class DeviceStatusWidget(QWidget):
    """
    Widget displaying device connection status
    """
    
    def __init__(self, parent=None):
        """Initialize device status widget"""
        super().__init__(parent)
        
        # Track counts
        self.connected_count = 0
        self.total_count = 0
        
        # Set up UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Device count label
        self.count_label = QLabel("Devices: 0/0")
        layout.addWidget(self.count_label)
        
        # Connection indicator
        self.connection_indicator = QProgressBar()
        self.connection_indicator.setFixedWidth(60)
        self.connection_indicator.setFixedHeight(12)
        self.connection_indicator.setRange(0, 100)
        self.connection_indicator.setValue(0)
        self.connection_indicator.setTextVisible(False)
        layout.addWidget(self.connection_indicator)
    
    def update_status(self, connected_count, total_count):
        """
        Update device status display
        
        Args:
            connected_count: Number of connected devices
            total_count: Total number of devices
        """
        self.connected_count = connected_count
        self.total_count = total_count
        
        # Update label
        self.count_label.setText(f"Devices: {connected_count}/{total_count}")
        
        # Update indicator
        if total_count > 0:
            percentage = int((connected_count / total_count) * 100)
            self.connection_indicator.setValue(percentage)
            
            # Set color based on connection status
            if percentage >= 80:
                # Green for good connection
                self.connection_indicator.setStyleSheet(
                    "QProgressBar { background-color: #444; border: 1px solid #666; border-radius: 3px; }"
                    "QProgressBar::chunk { background-color: #22aa22; border-radius: 2px; }"
                )
            elif percentage >= 50:
                # Yellow for partial connection
                self.connection_indicator.setStyleSheet(
                    "QProgressBar { background-color: #444; border: 1px solid #666; border-radius: 3px; }"
                    "QProgressBar::chunk { background-color: #aaaa22; border-radius: 2px; }"
                )
            else:
                # Red for poor connection
                self.connection_indicator.setStyleSheet(
                    "QProgressBar { background-color: #444; border: 1px solid #666; border-radius: 3px; }"
                    "QProgressBar::chunk { background-color: #aa2222; border-radius: 2px; }"
                )
        else:
            self.connection_indicator.setValue(0)
            self.connection_indicator.setStyleSheet(
                "QProgressBar { background-color: #444; border: 1px solid #666; border-radius: 3px; }"
                "QProgressBar::chunk { background-color: #444; border-radius: 2px; }"
            )
