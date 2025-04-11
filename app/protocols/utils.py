"""
Utility functions for light protocol implementations
"""

import math
import colorsys


def rgb_to_xy(red, green, blue):
    """
    Convert RGB color to CIE xy chromaticity
    
    Args:
        red: Red component (0-255)
        green: Green component (0-255)
        blue: Blue component (0-255)
        
    Returns:
        tuple: (x, y) coordinates in CIE color space
    """
    # Normalize RGB values to 0-1
    r = red / 255.0
    g = green / 255.0
    b = blue / 255.0
    
    # Apply gamma correction
    r = _gamma_correct(r)
    g = _gamma_correct(g)
    b = _gamma_correct(b)
    
    # Convert to XYZ color space
    X = r * 0.649926 + g * 0.103455 + b * 0.197109
    Y = r * 0.234327 + g * 0.743075 + b * 0.022598
    Z = r * 0.000000 + g * 0.053077 + b * 1.035763
    
    # Calculate xy values
    sum_XYZ = X + Y + Z
    if sum_XYZ == 0:
        return (0.0, 0.0)
    
    x = X / sum_XYZ
    y = Y / sum_XYZ
    
    return (x, y)


def xy_to_rgb(x, y, brightness=1.0):
    """
    Convert CIE xy chromaticity to RGB color
    
    Args:
        x: x-coordinate in CIE color space
        y: y-coordinate in CIE color space
        brightness: Brightness value (0-1)
        
    Returns:
        tuple: (red, green, blue) values (0-255)
    """
    # Calculate XYZ values
    if y == 0:
        return (0, 0, 0)
    
    Y = brightness
    X = (Y / y) * x
    Z = (Y / y) * (1 - x - y)
    
    # Convert to RGB
    r = X * 1.656492 - Y * 0.354851 - Z * 0.255038
    g = -X * 0.707196 + Y * 1.655397 + Z * 0.036152
    b = X * 0.051713 - Y * 0.121364 + Z * 1.011530
    
    # Apply gamma correction and clamp values
    r = _reverse_gamma(r)
    g = _reverse_gamma(g)
    b = _reverse_gamma(b)
    
    # Convert to 0-255 range and clamp
    r = max(0, min(255, int(r * 255)))
    g = max(0, min(255, int(g * 255)))
    b = max(0, min(255, int(b * 255)))
    
    return (r, g, b)


def rgb_to_hsv(red, green, blue):
    """
    Convert RGB color to HSV color space
    
    Args:
        red: Red component (0-255)
        green: Green component (0-255)
        blue: Blue component (0-255)
        
    Returns:
        tuple: (hue, saturation, value) - hue in degrees, saturation and value are 0-1
    """
    # Normalize RGB values to 0-1
    r = red / 255.0
    g = green / 255.0
    b = blue / 255.0
    
    # Convert to HSV
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    # Convert hue to degrees
    h = h * 360
    
    return (h, s, v)


def hsv_to_rgb(hue, saturation, value):
    """
    Convert HSV color to RGB color space
    
    Args:
        hue: Hue in degrees (0-360)
        saturation: Saturation (0-1)
        value: Value (0-1)
        
    Returns:
        tuple: (red, green, blue) values (0-255)
    """
    # Normalize hue to 0-1
    h = hue / 360.0
    
    # Convert to RGB
    r, g, b = colorsys.hsv_to_rgb(h, saturation, value)
    
    # Convert to 0-255 range
    r = max(0, min(255, int(r * 255)))
    g = max(0, min(255, int(g * 255)))
    b = max(0, min(255, int(b * 255)))
    
    return (r, g, b)


def _gamma_correct(value):
    """Apply gamma correction to a color value"""
    if value <= 0.04045:
        return value / 12.92
    else:
        return ((value + 0.055) / 1.055) ** 2.4


def _reverse_gamma(value):
    """Reverse gamma correction for a color value"""
    if value <= 0.0031308:
        return value * 12.92
    else:
        return 1.055 * (value ** (1 / 2.4)) - 0.055


def kelvin_to_rgb(kelvin):
    """
    Convert color temperature in Kelvin to RGB
    Based on approximation from http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
    
    Args:
        kelvin: Color temperature in Kelvin (1000-40000)
        
    Returns:
        tuple: (red, green, blue) values (0-255)
    """
    # Clamp kelvin to valid range
    temperature = max(1000, min(40000, kelvin)) / 100
    
    # Calculate red
    if temperature <= 66:
        red = 255
    else:
        red = temperature - 60
        red = 329.698727446 * (red ** -0.1332047592)
        red = max(0, min(255, red))
    
    # Calculate green
    if temperature <= 66:
        green = temperature
        green = 99.4708025861 * math.log(green) - 161.1195681661
    else:
        green = temperature - 60
        green = 288.1221695283 * (green ** -0.0755148492)
    green = max(0, min(255, green))
    
    # Calculate blue
    if temperature >= 66:
        blue = 255
    elif temperature <= 19:
        blue = 0
    else:
        blue = temperature - 10
        blue = 138.5177312231 * math.log(blue) - 305.0447927307
        blue = max(0, min(255, blue))
    
    return (int(red), int(green), int(blue))


def rgb_to_kelvin(red, green, blue):
    """
    Estimate color temperature in Kelvin from RGB
    This is an approximation and not very accurate
    
    Args:
        red: Red component (0-255)
        green: Green component (0-255)
        blue: Blue component (0-255)
        
    Returns:
        int: Estimated color temperature in Kelvin
    """
    # Simple estimation based on RGB ratios
    # More accurate methods would use color science calculations
    
    # Normalize RGB values
    r = red / 255.0
    g = green / 255.0
    b = blue / 255.0
    
    # Calculate temperature based on RGB ratios
    if b == 0:
        return 2000  # Very warm
    
    # Calculate kelvin based on RGB ratio
    rgb_ratio = r / b
    
    if rgb_ratio > 2.5:
        return 2000  # Very warm
    elif rgb_ratio > 2.0:
        return 2500
    elif rgb_ratio > 1.5:
        return 3000
    elif rgb_ratio > 1.2:
        return 3500
    elif rgb_ratio > 1.0:
        return 4000
    elif rgb_ratio > 0.8:
        return 4500
    elif rgb_ratio > 0.6:
        return 5000
    elif rgb_ratio > 0.5:
        return 5500
    elif rgb_ratio > 0.4:
        return 6000
    else:
        return 6500  # Very cool
