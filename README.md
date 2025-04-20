# Smart Light Controller

A comprehensive application for controlling multiple brands of smart lights from a single interface.

## Features

- **Multi-brand Support**: Control Philips Hue and LIFX lights from one interface
- **Web & Desktop Interfaces**: Access via desktop application or web browser
- **Interactive Color Controls**: Choose colors using an intuitive color picker
- **Light Groups**: Create custom groups to control multiple lights together
- **Scheduling**: Set up automated schedules for your lights
- **Device Discovery**: Automatically find compatible lights on your network

## Requirements

### Desktop Application
- Python 3.8+
- PySide6
- Requests

### Web Interface
- Python 3.8+
- Flask
- Flask-SQLAlchemy
- PostgreSQL (optional, for database persistence)

## Installation

1. **Unzip the archive**
   ```
   unzip smart_light_controller.zip
   ```

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Run the application**
   
   *Desktop Interface:*
   ```
   python main.py
   ```

   *Web Interface:*
   ```
   python web_app.py
   ```

## Usage

### Desktop Interface

The desktop application provides a full-featured interface with tabs for:
- Devices: View and control individual lights
- Groups: Create and manage light groups
- Schedules: Set up automated light controls

### Web Interface

The web interface is accessible at http://localhost:5000 when running and offers:
- Dashboard overview of all devices
- Individual device control
- Color selection
- Group management
- Schedule creation

## Configuration

Configuration is stored in `~/.smart_light_controller/config.json` and includes:
- Saved devices
- Groups
- Schedules
- User preferences

## Troubleshooting

- **No lights discovered**: Ensure your lights are on the same network as the application
- **Philips Hue connection issues**: Make sure the bridge is accessible and the user is registered
- **Web interface not loading**: Check that port 5000 is not in use by another application

## License

MIT License# SmartlightApp
# MichaelEZE
