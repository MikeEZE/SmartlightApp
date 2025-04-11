#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Smart Light Controller - Main Entry Point
A Windows desktop application for controlling multiple brands of smart lights.
"""

import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.main_window import MainWindow
from app.config_manager import ConfigManager
from app.constants import APP_NAME, LOG_FORMAT, LOG_LEVEL


def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(APP_NAME)


def main():
    """Main application entry point"""
    # Set up logging
    logger = setup_logging()
    logger.info(f"Starting {APP_NAME}")
    
    # Set environment variables for Qt
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")  # Use Fusion style for consistent look across platforms
    
    # Load application configuration
    config_manager = ConfigManager()
    config_manager.load_config()
    
    # Create and show main window
    main_window = MainWindow(config_manager)
    main_window.show()
    
    # Start the application event loop
    exit_code = app.exec()
    
    # Save configuration on exit
    config_manager.save_config()
    logger.info(f"Shutting down {APP_NAME}")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
