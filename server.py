#!/usr/bin/env python3
"""
ROS MCP Server - Complete Implementation

A Model Context Protocol (MCP) server for ROS2 robotics simulation with Ignition Gazebo.
Provides robot spawning, control, scene management, and enhanced robot discovery.
"""

import sys
import os
from pathlib import Path
from typing import List, Any, Dict, Optional
import json
import math
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# MCP imports
from mcp.server.fastmcp import FastMCP

# ROS message imports
from terracotta.communication.msgs.geometry_msgs.twist import Twist
from terracotta.communication.msgs.sensor_msgs.jointstate import JointState
from terracotta.communication.msgs.sensor_msgs.image import Image
from terracotta.communication.msgs.trajectory_msgs.joint_trajectory import JointTrajectory

# Utility imports
from terracotta.communication import WebSocketManager
from terracotta.scene import SceneManager, PickPlaceManager
from terracotta.launch import LaunchManager

# Robot management imports
from terracotta.robots import EnhancedRobotManager
ENHANCED_ROBOT_MANAGER_AVAILABLE = True

# Gazebo integration (mock for now - replace with actual gazebo interface)
class IgnitionGazebo:
    """Mock Ignition Gazebo interface - replace with actual implementation"""
    
    def get_objects(self) -> Dict[str, Any]:
        """Get objects in the scene"""
        # Mock implementation - replace with actual Gazebo object detection
        return {
            "red_box": {
                "position": [0.5, 0.0, 0.05],
                "type": "box",
                "color": "red"
            },
            "blue_cylinder": {
                "position": [0.0, 0.5, 0.1],
                "type": "cylinder", 
                "color": "blue"
            },
            "green_sphere": {
                "position": [-0.5, 0.0, 0.1],
                "type": "sphere",
                "color": "green"
            }
        }

# ===== INITIALIZATION =====
# Initialize MCP server
mcp = FastMCP("ROS MCP Server")

# Initialize managers
ws_manager = WebSocketManager("127.0.0.1", 9090, "127.0.0.1")
scene_manager = SceneManager(ws_manager)
pick_place_manager = PickPlaceManager()
launch_manager = LaunchManager()
ign_gazebo = IgnitionGazebo()

# Initialize enhanced robot manager
enhanced_robot_manager = EnhancedRobotManager("empty")
print("[Server] Enhanced robot manager initialized successfully")

# Initialize ROS message publishers/subscribers
twist = Twist(ws_manager, "/cmd_vel")
jointstate = JointState(ws_manager, "/joint_states")
image = Image(ws_manager, "/camera/image_raw")
robot_trajectory = JointTrajectory(ws_manager, "/joint_trajectory_controller/joint_trajectory")

# Robot configuration
UR5E_JOINTS = [
    "shoulder_pan_joint",
    "shoulder_lift_joint", 
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint"
]

# ===== LAUNCH MANAGEMENT TOOLS =====

@mcp.tool()
def start_simulation(world_name: str = "empty") -> str:
    """Start the complete simulation stack (Gazebo + ROS bridge)"""
    try:
        return launch_manager.start_simulation(world_name)
    except Exception as e:
        return f"Error starting simulation: {e}"

@mcp.tool()
def stop_simulation() -> str:
    """Stop the complete simulation stack"""
    try:
        return launch_manager.stop_simulation()
    except Exception as e:
        return f"Error stopping simulation: {e}"

@mcp.tool()
def get_simulation_status() -> Dict[str, Any]:
    """Get status of simulation components"""
    try:
        return launch_manager.get_status()
    except Exception as e:
        return {"error": f"Failed to get status: {e}"}

@mcp.tool()
def restart_simulation(world_name: str = "empty") -> str:
    """Restart the simulation stack"""
    try:
        stop_result = launch_manager.stop_simulation()
        time.sleep(2)  # Brief pause
        start_result = launch_manager.start_simulation(world_name)
        return f"Restart: {stop_result}. {start_result}"
    except Exception as e:
        return f"Error restarting simulation: {e}"

# ===== ENHANCED ROBOT MANAGEMENT TOOLS =====

@mcp.tool()
def search_robots_in_dataset(name_pattern: str = None, robot_type: str = None, 
                           manufacturer: str = None, source: str = None, 
                           include_dataset: bool = True) -> Dict[str, Any]:
    """Search for robots in the URDF dataset with various filters"""
    # Enhanced robot manager is always available
    
    try:
        robots = enhanced_robot_manager.search_robots(
            name_pattern=name_pattern,
            robot_type=robot_type,
            manufacturer=manufacturer,
            source=source,
            include_dataset=include_dataset
        )
        
        # Convert to JSON-serializable format
        result = {}
        for key, robot_info in robots.items():
            result[key] = {
                "name": robot_info.name,
                "variant": robot_info.variant,
                "type": robot_info.robot_type,
                "manufacturer": robot_info.manufacturer,
                "source": robot_info.source,
                "description": robot_info.description,
                "specifications": robot_info.specifications
            }
        
        return {
            "total_found": len(result),
            "robots": result
        }
    except Exception as e:
        return {"error": f"Search failed: {e}"}

@mcp.tool()
def spawn_robot_by_name(robot_name: str, source: str = None, instance_name: str = None,
                       position: List[float] = None, orientation: List[float] = None,
                       gripper_name: str = None) -> str:
    """Spawn a robot by name from the dataset"""
    # Enhanced robot manager is always available
    
    try:
        # Search for robots matching the name
        matching_robots = enhanced_robot_manager.search_robots(
            name_pattern=robot_name,
            source=source,
            include_dataset=True
        )
        
        if not matching_robots:
            return f"Robot '{robot_name}' not found in dataset"
        
        # Pick the first match or exact match
        robot_key = list(matching_robots.keys())[0]
        
        return enhanced_robot_manager.spawn_robot(
            robot_key=robot_key,
            instance_name=instance_name,
            position=position or [0, 0, 0],
            orientation=orientation,
            gripper_name=gripper_name
        )
    except Exception as e:
        return f"Error spawning robot: {e}"

@mcp.tool()
def get_spawned_robots() -> Dict[str, Any]:
    """Get list of currently spawned robots"""
    try:
        return enhanced_robot_manager.get_spawned_robots()
    except Exception as e:
        return {"error": f"Failed to get spawned robots: {e}"}

@mcp.tool()
def move_robot_by_name(instance_name: str, position: List[float], 
                      orientation: List[float] = None) -> str:
    """Move a spawned robot to a new position"""
    if not ENHANCED_ROBOT_MANAGER_AVAILABLE:
        return "Enhanced robot manager not available"
    
    if enhanced_robot_manager is None:
        return "Enhanced robot manager not initialized"
    
    try:
        return enhanced_robot_manager.move_robot(instance_name, position, orientation)
    except Exception as e:
        return f"Error moving robot: {e}"

@mcp.tool()
def remove_robot(instance_name: str) -> str:
    """Remove a robot from the scene"""
    if not ENHANCED_ROBOT_MANAGER_AVAILABLE:
        return "Enhanced robot manager not available"
    
    if enhanced_robot_manager is None:
        return "Enhanced robot manager not initialized"
    
    try:
        return enhanced_robot_manager.remove_robot(instance_name)
    except Exception as e:
        return f"Error removing robot: {e}"

@mcp.tool()
def get_dataset_statistics() -> Dict[str, Any]:
    """Get statistics about the robot dataset"""
    if not ENHANCED_ROBOT_MANAGER_AVAILABLE:
        return {"error": "Enhanced robot manager not available"}
    
    if enhanced_robot_manager is None:
        return {"error": "Enhanced robot manager not initialized"}
    
    try:
        return enhanced_robot_manager.get_robot_statistics()
    except Exception as e:
        return {"error": f"Failed to get statistics: {e}"}

@mcp.tool()
def find_collaborative_robots() -> Dict[str, Any]:
    """Find collaborative robots suitable for human interaction"""
    if not ENHANCED_ROBOT_MANAGER_AVAILABLE:
        return {"error": "Enhanced robot manager not available"}
    
    if enhanced_robot_manager is None:
        return {"error": "Enhanced robot manager not initialized"}
    
    try:
        # Search for collaborative robots
        cobot_manufacturers = ["Universal Robots", "Franka Emika", "KUKA", "ABB"]
        cobot_names = ["UR3", "UR5", "UR10", "Panda", "YuMi", "iiwa", "Gen3"]
        
        all_robots = enhanced_robot_manager.get_available_robots(include_dataset=True)
        cobots = {}
        
        for key, robot_info in all_robots.items():
            if (robot_info.manufacturer in cobot_manufacturers or
                any(name in robot_info.name for name in cobot_names)):
                if robot_info.robot_type in ["robotic arm", "dual arm robot"]:
                    cobots[key] = {
                        "name": robot_info.name,
                        "manufacturer": robot_info.manufacturer,
                        "type": robot_info.robot_type,
                        "source": robot_info.source,
                        "specifications": robot_info.specifications
                    }
        
        return {
            "collaborative_robots": cobots,
            "total_found": len(cobots)
        }
    except Exception as e:
        return {"error": f"Search failed: {e}"}

# ===== WORKSPACE SCANNING =====

@mcp.tool()
def scan_workspace(robot_name: str = "main_robot") -> Dict[str, Any]:
    """Scan workspace to identify reachable objects"""
    try:
        objects = ign_gazebo.get_objects()
        
        # Get robot position if robot manager is available
        robot_position = [0.0, 0.0, 0.0]  # Default
        robot_reach = 0.85  # UR5e max reach in meters
        
        if ENHANCED_ROBOT_MANAGER_AVAILABLE and enhanced_robot_manager:
            robots = enhanced_robot_manager.get_spawned_robots()
            if robot_name in robots:
                robot_position = robots[robot_name]["position"]
                robot_config = robots[robot_name]["robot_info"]
                robot_reach = robot_config.get("specifications", {}).get("reach", 0.85)
        
        reachable = {}
        unreachable = {}
        
        for obj_name, obj_info in objects.items():
            obj_pos = obj_info["position"]
            # Calculate distance from robot base
            distance = ((obj_pos[0] - robot_position[0])**2 + 
                       (obj_pos[1] - robot_position[1])**2)**0.5
            
            if distance <= robot_reach:
                reachable[obj_name] = {
                    "position": obj_pos,
                    "distance": distance,
                    "type": obj_info["type"]
                }
            else:
                unreachable[obj_name] = {
                    "position": obj_pos,
                    "distance": distance,
                    "reason": f"Too far ({distance:.2f}m > {robot_reach}m)"
                }
        
        return {
            "reachable": reachable,
            "unreachable": unreachable,
            "robot_position": robot_position,
            "robot_reach": robot_reach,
            "total_objects": len(objects)
        }
    except Exception as e:
        return {"error": f"Workspace scan failed: {e}"}

@mcp.tool()
def find_objects_by_color(color: str) -> Dict[str, Any]:
    """Find all objects of a specific color"""
    try:
        objects = ign_gazebo.get_objects()
        matching_objects = []
        
        for obj_name, obj_info in objects.items():
            # Color matching based on stored color info
            if obj_info.get("color", "").lower() == color.lower():
                matching_objects.append({
                    "name": obj_name,
                    "position": obj_info["position"],
                    "type": obj_info["type"]
                })
        
        return {"color": color, "objects": matching_objects}
    except Exception as e:
        return {"error": f"Color search failed: {e}"}

@mcp.tool()
def get_closest_object(position: List[float], color_filter: str = None) -> Dict[str, Any]:
    """Find closest object to a position, optionally filtered by color"""
    try:
        objects = ign_gazebo.get_objects()
        min_distance = float('inf')
        closest_object = None
        
        for obj_name, obj_info in objects.items():
            # Apply color filter if specified
            if color_filter and obj_info.get("color", "").lower() != color_filter.lower():
                continue
                
            obj_pos = obj_info["position"]
            distance = sum((a - b)**2 for a, b in zip(position[:3], obj_pos[:3]))**0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_object = obj_name
        
        return {"closest_object": closest_object, "distance": min_distance}
    except Exception as e:
        return {"error": f"Closest object search failed: {e}"}

# ===== ROBOT CONTROL =====

@mcp.tool()
def move_robot_to_position(robot_name: str = None, position: List[float] = None, 
                          orientation: List[float] = [0.0, 0.0, 0.0, 1.0]) -> str:
    """
    Move robot end-effector to a Cartesian position using simple IK
    
    Args:
        robot_name: Name of robot instance (optional, uses first available)
        position: [x, y, z] target position in meters relative to robot base
        orientation: [x, y, z, w] target orientation quaternion (optional)
    """
    if position is None:
        return "Error: position parameter is required"
    
    try:
        # Simple IK approximation for UR5e
        x, y, z = position[0], position[1], position[2]
        
        # Basic geometric IK (simplified)
        # Joint 1 (base rotation)
        theta1 = math.atan2(y, x)
        
        # Simplified approach for other joints
        r = math.sqrt(x*x + y*y)
        theta2 = -1.57 + math.atan2(z - 0.1625, r) * 0.5
        theta3 = math.atan2(z - 0.1625, r) * 0.3
        theta4 = -theta2 - theta3
        theta5 = 1.57 if abs(math.sin(theta1)) > 0.1 else 0.0
        theta6 = 0.0
        
        joint_positions = [theta1, theta2, theta3, theta4, theta5, theta6]
        
        # Execute movement
        msg = robot_trajectory.publish(UR5E_JOINTS, joint_positions, 4.0)
        ws_manager.close()
        
        if msg is not None:
            return f"Robot moving to Cartesian position: {position} with joint angles: {[round(j, 3) for j in joint_positions]}"
        else:
            return f"Robot movement command sent to position {position}"
    except Exception as e:
        return f"Error moving robot to position: {e}"

@mcp.tool()
def compute_inverse_kinematics(position: List[float], orientation: List[float] = [0.0, 0.0, 0.0, 1.0]) -> Dict[str, Any]:
    """
    Compute inverse kinematics for a target pose without moving the robot
    """
    try:
        # Use the same simple IK as above
        x, y, z = position[0], position[1], position[2]
        
        theta1 = math.atan2(y, x)
        r = math.sqrt(x*x + y*y)
        theta2 = -1.57 + math.atan2(z - 0.1625, r) * 0.5
        theta3 = math.atan2(z - 0.1625, r) * 0.3
        theta4 = -theta2 - theta3
        theta5 = 1.57 if abs(math.sin(theta1)) > 0.1 else 0.0
        theta6 = 0.0
        
        joint_positions = [theta1, theta2, theta3, theta4, theta5, theta6]
        
        return {
            "success": True,
            "joint_positions": joint_positions,
            "target_position": position,
            "target_orientation": orientation
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"IK computation failed: {e}"
        }

@mcp.tool()
def get_joint_states() -> Dict[str, Any]:
    """Get current joint states from the robot"""
    try:
        msg = jointstate.subscribe()
        ws_manager.close()
        if msg is not None:
            return {"success": True, "joint_states": msg}
        else:
            return {"success": False, "error": "No joint state data received"}
    except Exception as e:
        return {"success": False, "error": f"Failed to get joint states: {e}"}

@mcp.tool()
def get_gripper_status() -> Dict[str, Any]:
    """Get current gripper status (simulated)"""
    return {
        "open": True,  # Simulated
        "holding_object": None,  # Simulated
        "can_pick": True,
        "can_place": False
    }

# ===== ROS COMMUNICATION TOOLS =====

@mcp.tool()
def get_topics() -> List[str]:
    """Get list of available ROS topics"""
    try:
        topics = ws_manager.get_topics()
        return [f"{topic[0]} ({topic[1]})" for topic in topics]
    except Exception as e:
        return [f"Error getting topics: {e}"]

@mcp.tool()
def pub_twist(linear: List[float], angular: List[float]) -> str:
    """Control robot movement with twist commands"""
    try:
        msg = twist.publish(linear, angular)
        ws_manager.close()
        
        if msg is not None:
            return "Twist message published successfully"
        else:
            return "Twist message sent (no confirmation)"
    except Exception as e:
        return f"Error publishing twist: {e}"

@mcp.tool()
def pub_twist_seq(linear: List[List[float]], angular: List[List[float]], duration: List[float]) -> str:
    """Publish sequence of robot movements"""
    try:
        twist.publish_sequence(linear, angular, duration)
        return f"Published sequence of {len(linear)} movements"
    except Exception as e:
        return f"Error publishing twist sequence: {e}"

@mcp.tool()
def sub_image() -> str:
    """Capture image from robot camera"""
    try:
        msg = image.subscribe()
        ws_manager.close()
        
        if msg is not None:
            return "Image data received and downloaded successfully"
        else:
            return "No image data received"
    except Exception as e:
        return f"Error capturing image: {e}"

@mcp.tool()
def pub_jointstate(name: List[str], position: List[float], velocity: List[float], effort: List[float]) -> str:
    """Publish raw joint state data (for advanced users)"""
    try:
        msg = jointstate.publish(name, position, velocity, effort)
        ws_manager.close()
        if msg is not None:
            return "JointState message published successfully"
        else:
            return "JointState message sent (no confirmation)"
    except Exception as e:
        return f"Error publishing joint state: {e}"

@mcp.tool()
def sub_jointstate() -> str:
    """Subscribe to raw joint state data"""
    try:
        msg = jointstate.subscribe()
        ws_manager.close()
        if msg is not None:
            return str(msg)
        else:
            return "No JointState data received"
    except Exception as e:
        return f"Error subscribing to joint state: {e}"

# ===== SYSTEM STATUS =====

@mcp.tool()
def get_system_status() -> Dict[str, Any]:
    """Get status of all system components"""
    status = {
        "mcp_server": "running",
        "websocket_manager": "available" if ws_manager else "unavailable",
        "enhanced_robot_manager": "available" if ENHANCED_ROBOT_MANAGER_AVAILABLE else "unavailable",
        "scene_manager": "available" if scene_manager else "unavailable",
        "pick_place_manager": "available" if pick_place_manager else "unavailable",
        "ignition_gazebo": "mocked",  # Replace with actual status check
        "ros_bridge": "unknown"  # Replace with actual status check
    }
    
    if ENHANCED_ROBOT_MANAGER_AVAILABLE and enhanced_robot_manager:
        try:
            robot_stats = enhanced_robot_manager.get_robot_statistics()
            status["robot_dataset"] = robot_stats
        except:
            status["robot_dataset"] = "error"
    
    return status

# ===== MAIN ENTRY POINT =====

def main():
    """Main entry point for the MCP server"""
    print("🤖 ROS MCP Server starting...")
    print(f"   Enhanced Robot Manager: {'✅' if ENHANCED_ROBOT_MANAGER_AVAILABLE else '❌'}")
    print(f"   Scene Manager: {'✅' if scene_manager else '❌'}")
    print(f"   Pick-Place Manager: {'✅' if pick_place_manager else '❌'}")
    print(f"   WebSocket Manager: {'✅' if ws_manager else '❌'}")
    
    if ENHANCED_ROBOT_MANAGER_AVAILABLE and enhanced_robot_manager:
        try:
            stats = enhanced_robot_manager.get_robot_statistics()
            print(f"   Robot Dataset: {stats['total_robots']} robots loaded")
        except:
            print("   Robot Dataset: Error loading statistics")
    
    print("🚀 Server ready - use with MCP client")

if __name__ == "__main__":
    main()
    mcp.run(transport="stdio")
