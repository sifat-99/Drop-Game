import math

def lerp(start, end, t):
    """Linear interpolation"""
    return start + (end - start) * t

def ease_out_cubic(t):
    """Easing function for smooth animations"""
    return 1 - pow(1 - t, 3)
