"""
Color picker widget for selecting light colors
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel,
    QGridLayout, QPushButton
)
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QLinearGradient, QGradient

from ..constants import APP_NAME


logger = logging.getLogger(APP_NAME)


class ColorPickerWidget(QWidget):
    """
    Custom widget for selecting colors
    Provides a color wheel and RGB sliders
    """
    
    # Signal emitted when color is selected
    colorSelected = Signal(QColor)
    
    def __init__(self, parent=None):
        """Initialize color picker widget"""
        super().__init__(parent)
        
        # Current color
        self.current_color = QColor(255, 255, 255)  # Start with white
        
        # Set up UI
        self.init_ui()
        
        # Set minimum size
        self.setMinimumSize(200, 200)
    
    def init_ui(self):
        """Initialize the user interface components"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Color display
        self.color_display = ColorDisplay(self.current_color)
        layout.addWidget(self.color_display)
        
        # RGB sliders
        sliders_layout = QGridLayout()
        
        # Red slider
        sliders_layout.addWidget(QLabel("R:"), 0, 0)
        
        self.red_slider = QSlider(Qt.Horizontal)
        self.red_slider.setRange(0, 255)
        self.red_slider.setValue(self.current_color.red())
        self.red_slider.valueChanged.connect(self.on_slider_changed)
        sliders_layout.addWidget(self.red_slider, 0, 1)
        
        self.red_label = QLabel(str(self.current_color.red()))
        self.red_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.red_label.setFixedWidth(40)
        sliders_layout.addWidget(self.red_label, 0, 2)
        
        # Green slider
        sliders_layout.addWidget(QLabel("G:"), 1, 0)
        
        self.green_slider = QSlider(Qt.Horizontal)
        self.green_slider.setRange(0, 255)
        self.green_slider.setValue(self.current_color.green())
        self.green_slider.valueChanged.connect(self.on_slider_changed)
        sliders_layout.addWidget(self.green_slider, 1, 1)
        
        self.green_label = QLabel(str(self.current_color.green()))
        self.green_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.green_label.setFixedWidth(40)
        sliders_layout.addWidget(self.green_label, 1, 2)
        
        # Blue slider
        sliders_layout.addWidget(QLabel("B:"), 2, 0)
        
        self.blue_slider = QSlider(Qt.Horizontal)
        self.blue_slider.setRange(0, 255)
        self.blue_slider.setValue(self.current_color.blue())
        self.blue_slider.valueChanged.connect(self.on_slider_changed)
        sliders_layout.addWidget(self.blue_slider, 2, 1)
        
        self.blue_label = QLabel(str(self.current_color.blue()))
        self.blue_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.blue_label.setFixedWidth(40)
        sliders_layout.addWidget(self.blue_label, 2, 2)
        
        layout.addLayout(sliders_layout)
        
        # Common colors grid
        colors_layout = QGridLayout()
        common_colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 165, 0),  # Orange
            (128, 0, 128),  # Purple
            (255, 192, 203),# Pink
            (165, 42, 42),  # Brown
            (255, 255, 255),# White
            (0, 0, 0)       # Black
        ]
        
        row, col = 0, 0
        for r, g, b in common_colors:
            color_button = QPushButton()
            color_button.setFixedSize(24, 24)
            color_button.setStyleSheet(
                f"background-color: rgb({r}, {g}, {b}); border: 1px solid #888888;"
            )
            color_button.clicked.connect(
                lambda checked, color=(r, g, b): self.set_color_from_rgb(color)
            )
            colors_layout.addWidget(color_button, row, col)
            
            col += 1
            if col > 3:  # 4 columns
                col = 0
                row += 1
        
        layout.addLayout(colors_layout)
    
    def on_slider_changed(self):
        """Handle RGB slider changes"""
        # Update color from slider values
        self.current_color.setRgb(
            self.red_slider.value(),
            self.green_slider.value(),
            self.blue_slider.value()
        )
        
        # Update labels
        self.red_label.setText(str(self.current_color.red()))
        self.green_label.setText(str(self.current_color.green()))
        self.blue_label.setText(str(self.current_color.blue()))
        
        # Update color display
        self.color_display.set_color(self.current_color)
        
        # Emit signal
        self.colorSelected.emit(self.current_color)
    
    def set_color(self, color):
        """
        Set current color
        
        Args:
            color: QColor object
        """
        self.current_color = color
        
        # Update sliders (block signals to prevent feedback loop)
        self.red_slider.blockSignals(True)
        self.red_slider.setValue(color.red())
        self.red_slider.blockSignals(False)
        
        self.green_slider.blockSignals(True)
        self.green_slider.setValue(color.green())
        self.green_slider.blockSignals(False)
        
        self.blue_slider.blockSignals(True)
        self.blue_slider.setValue(color.blue())
        self.blue_slider.blockSignals(False)
        
        # Update labels
        self.red_label.setText(str(color.red()))
        self.green_label.setText(str(color.green()))
        self.blue_label.setText(str(color.blue()))
        
        # Update color display
        self.color_display.set_color(color)
    
    def set_color_from_rgb(self, rgb):
        """
        Set color from RGB tuple
        
        Args:
            rgb: Tuple of (red, green, blue) values (0-255)
        """
        r, g, b = rgb
        self.set_color(QColor(r, g, b))
        
        # Emit signal
        self.colorSelected.emit(self.current_color)


class ColorDisplay(QWidget):
    """
    Widget to display the currently selected color
    """
    
    def __init__(self, color, parent=None):
        """Initialize color display with initial color"""
        super().__init__(parent)
        self.color = color
        
        # Set minimum size
        self.setMinimumHeight(50)
    
    def set_color(self, color):
        """Set current display color and update"""
        self.color = color
        self.update()
    
    def paintEvent(self, event):
        """Paint the color display"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw color rectangle with border
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setPen(QPen(Qt.gray, 1))
        painter.setBrush(QBrush(self.color))
        painter.drawRect(rect)
