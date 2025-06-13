import json
import time
from typing import List, Any

class JointTrajectory:
    def __init__(self, ws_manager, topic: str):
        self.ws_manager = ws_manager
        self.topic = topic
        self.msg_type = "trajectory_msgs/JointTrajectory"  # Match ROS 2 format exactly
    
    def publish(self, joint_names: List[str], positions: List[float], duration_sec: float = 3.0):
        """
        Publish a joint trajectory command
        
        Args:
            joint_names: List of joint names (e.g., ['shoulder_pan_joint', 'shoulder_lift_joint', ...])
            positions: List of target positions for each joint (in radians)
            duration_sec: Time to reach the target positions
        """
        
        print(f"[JointTrajectory] Publishing trajectory to {self.topic}")
        print(f"[JointTrajectory] Joints: {joint_names}")
        print(f"[JointTrajectory] Positions: {positions}")
        print(f"[JointTrajectory] Duration: {duration_sec}s")
        
        # Create trajectory point - match the working ROS format exactly
        trajectory_point = {
            "positions": positions,
            "velocities": [],
            "accelerations": [],
            "effort": [],
            "time_from_start": {
                "sec": int(duration_sec),
                "nanosec": 0  # Keep it simple like the working example
            }
        }
        
        # Create the full message - match ROS 2 format
        message = {
            "header": {
                "stamp": {
                    "sec": 0,
                    "nanosec": 0
                },
                "frame_id": ""
            },
            "joint_names": joint_names,
            "points": [trajectory_point]
        }
        
        # Create the rosbridge message with correct type
        rosbridge_msg = {
            "op": "publish",
            "topic": self.topic,
            "type": self.msg_type,
            "msg": message
        }
        
        try:
            # Connect if not connected
            if not self.ws_manager.connected:
                print("[JointTrajectory] Connecting to WebSocket...")
                self.ws_manager.connect()
            
            # Send the message
            print("[JointTrajectory] Sending trajectory command...")
            print(f"[JointTrajectory] Full message: {json.dumps(rosbridge_msg, indent=2)}")
            self.ws_manager.send(rosbridge_msg)
            print("[JointTrajectory] Trajectory command sent successfully!")
            return message
            
        except Exception as e:
            print(f"Error publishing JointTrajectory: {e}")
            return None
