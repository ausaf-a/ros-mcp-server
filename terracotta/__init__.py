"""
Terracotta - ROS MCP Server Core Package

A comprehensive robotics simulation and control package for ROS2 and Ignition Gazebo.
"""

__version__ = "0.1.0"

# Import main components for easy access
from .robots.manager import EnhancedRobotManager
from .communication.websocket_manager import WebSocketManager
from .scene.manager import SceneManager
from .scene.pick_place import PickPlaceManager
from .launch.manager import LaunchManager

__all__ = [
    "EnhancedRobotManager",
    "WebSocketManager", 
    "SceneManager",
    "PickPlaceManager",
    "LaunchManager"
]
