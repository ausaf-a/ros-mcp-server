from mcp.server.fastmcp import FastMCP
from typing import List, Any, Optional
from pathlib import Path
import json
from utils.websocket_manager import WebSocketManager
from msgs.geometry_msgs import Twist
from msgs.sensor_msgs import Image, JointState
from msgs.trajectory_msgs import JointTrajectory

LOCAL_IP = "localhost"
ROSBRIDGE_IP = "localhost"
ROSBRIDGE_PORT = 9090

mcp = FastMCP("ros-mcp-server")
ws_manager = WebSocketManager(ROSBRIDGE_IP, ROSBRIDGE_PORT, LOCAL_IP)

# Original turtle control
twist = Twist(ws_manager, topic="/turtle1/cmd_vel")

# Camera and sensor data
image = Image(ws_manager, topic="/camera/image_raw")
jointstate = JointState(ws_manager, topic="/joint_states")

# Robot arm control
robot_trajectory = JointTrajectory(ws_manager, topic="/joint_trajectory_controller/joint_trajectory")

# UR5e joint names (in order)
UR5E_JOINTS = [
    "shoulder_pan_joint",
    "shoulder_lift_joint", 
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint"
]

@mcp.tool()
def get_topics():
    """Get all available ROS topics"""
    topic_info = ws_manager.get_topics()
    ws_manager.close()

    if topic_info:
        topics, types = zip(*topic_info)
        return {
            "topics": list(topics),
            "types": list(types)
        }
    else:
        return "No topics found"

# ===== TURTLE CONTROL (Original) =====
@mcp.tool()
def pub_twist(linear: List[Any], angular: List[Any]):
    """Control turtle movement"""
    msg = twist.publish(linear, angular)
    ws_manager.close()
    
    if msg is not None:
        return "Twist message published successfully"
    else:
        return "No message published"

@mcp.tool()
def pub_twist_seq(linear: List[Any], angular: List[Any], duration: List[Any]):
    """Publish sequence of turtle movements"""
    twist.publish_sequence(linear, angular, duration)

# ===== ROBOT ARM CONTROL =====
@mcp.tool()
def move_robot_joints(positions: List[float], duration: float = 3.0):
    """
    Move the UR5e robot arm to specific joint positions
    
    Args:
        positions: List of 6 joint positions in radians [shoulder_pan, shoulder_lift, elbow, wrist_1, wrist_2, wrist_3]
        duration: Time in seconds to complete the movement (default: 3.0)
    
    Example:
        move_robot_joints([0.0, -1.57, 0.0, -1.57, 0.0, 0.0], 5.0)  # Move to a "ready" position
    """
    if len(positions) != 6:
        return f"Error: Expected 6 joint positions, got {len(positions)}"
    
    msg = robot_trajectory.publish(UR5E_JOINTS, positions, duration)
    ws_manager.close()
    
    if msg is not None:
        return f"Robot arm moving to positions: {positions} over {duration} seconds"
    else:
        return "Failed to send robot arm command"

@mcp.tool()
def move_robot_home():
    """Move the robot arm to a safe home position"""
    home_position = [0.0, -1.57, 0.0, -1.57, 0.0, 0.0]  # Safe home pose
    return move_robot_joints(home_position, 4.0)

@mcp.tool()
def move_robot_ready():
    """Move the robot arm to a ready/observation position"""
    ready_position = [0.0, -1.0, 0.5, -2.0, 0.0, 0.0]  # Good for observing workspace
    return move_robot_joints(ready_position, 4.0)

@mcp.tool()
def move_robot_vertical():
    """Move the robot arm to a vertical position (good for demos)"""
    vertical_position = [0.0, -1.57, -1.57, -1.57, 1.57, 0.0]  # Arm pointing up
    return move_robot_joints(vertical_position, 5.0)

@mcp.tool()
def get_robot_status():
    """Get current robot joint states and positions"""
    msg = jointstate.subscribe()
    ws_manager.close()
    
    if msg is not None:
        # Parse the joint state message to extract UR5e joints
        joint_data = {}
        if 'name' in msg and 'position' in msg:
            for i, name in enumerate(msg['name']):
                if name in UR5E_JOINTS and i < len(msg['position']):
                    joint_data[name] = {
                        'position': msg['position'][i],
                        'velocity': msg['velocity'][i] if i < len(msg['velocity']) else 0.0
                    }
        
        return {
            "robot_joints": joint_data,
            "timestamp": msg.get('header', {}).get('stamp', 'unknown'),
            "status": "Robot is operational"
        }
    else:
        return "Could not get robot status - check if robot is running"

# ===== CAMERA & SENSING =====
@mcp.tool()
def sub_image():
    """Capture image from robot camera"""
    msg = image.subscribe()
    ws_manager.close()
    
    if msg is not None:
        return "Image data received and downloaded successfully"
    else:
        return "No image data received"

# ===== LOW-LEVEL JOINT CONTROL (Original) =====
@mcp.tool()
def pub_jointstate(name: list[str], position: list[float], velocity: list[float], effort: list[float]):
    """Publish raw joint state data (for advanced users)"""
    msg = jointstate.publish(name, position, velocity, effort)
    ws_manager.close()
    if msg is not None:
        return "JointState message published successfully"
    else:
        return "No message published"

@mcp.tool()
def sub_jointstate():
    """Subscribe to raw joint state data"""
    msg = jointstate.subscribe()
    ws_manager.close()
    if msg is not None:
        return msg
    else:
        return "No JointState data received"

if __name__ == "__main__":
    mcp.run(transport="stdio")
