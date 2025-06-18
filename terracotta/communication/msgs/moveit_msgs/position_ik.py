import json
import math
from typing import List, Tuple, Optional


class PositionIK:
    """Inverse kinematics solver for UR5e via rosbridge websocket"""
    
    def __init__(self, ws_manager, service_name="/compute_ik"):
        self.ws_manager = ws_manager
        self.service_name = service_name

    def compute_ik(self, position: List[float], orientation: List[float] = [0.0, 0.0, 0.0, 1.0],
                   group_name: str = "ur_manipulator") -> Optional[List[float]]:
        """
        Compute inverse kinematics for target pose
        
        Args:
            position: [x, y, z] target position in meters
            orientation: [x, y, z, w] target orientation quaternion  
            group_name: MoveIt planning group name
            
        Returns:
            List of joint angles in radians, or None if IK failed
        """
        
        message = {
            "op": "call_service",
            "service": self.service_name,
            "args": {
                "ik_request": {
                    "group_name": group_name,
                    "pose_stamped": {
                        "header": {
                            "frame_id": "base_link"
                        },
                        "pose": {
                            "position": {
                                "x": position[0],
                                "y": position[1],
                                "z": position[2]
                            },
                            "orientation": {
                                "x": orientation[0],
                                "y": orientation[1],
                                "z": orientation[2],
                                "w": orientation[3]
                            }
                        }
                    },
                    "avoid_collisions": True,
                    "timeout": {
                        "secs": 5,
                        "nsecs": 0
                    }
                }
            },
            "id": f"compute_ik_{hash(str(position)) % 10000}"
        }
        
        try:
            self.ws_manager.send(message)
            response = self.ws_manager.receive_service_response(timeout=10.0)
            
            if response:
                data = json.loads(response)
                values = data.get("values", {})
                
                if values.get("error_code", {}).get("val", -1) == 1:  # SUCCESS
                    solution = values.get("solution", {})
                    joint_state = solution.get("joint_state", {})
                    positions = joint_state.get("position", [])
                    
                    if len(positions) >= 6:
                        return positions[:6]  # Return first 6 joints for UR5e
                    
                return None
                
        except Exception as e:
            print(f"IK computation error: {e}")
            return None

    def simple_ik_approximation(self, position: List[float], orientation: List[float] = [0.0, 0.0, 0.0, 1.0]) -> List[float]:
        """
        Simple IK approximation for UR5e when MoveIt is not available
        This is a simplified geometric solution - not as accurate as MoveIt
        """
        
        x, y, z = position[0], position[1], position[2]
        
        # UR5e DH parameters (approximate)
        d1 = 0.1625  # base to shoulder
        a2 = -0.425  # shoulder to elbow
        a3 = -0.39225  # elbow to wrist
        d4 = 0.1333  # wrist 1 offset
        d5 = 0.0997  # wrist 2 offset
        d6 = 0.0996  # wrist 3 to tool
        
        # Joint 1 (base rotation)
        theta1 = math.atan2(y, x)
        
        # Simplified approach - position end effector above target
        # This is very basic and should be replaced with proper IK
        r = math.sqrt(x*x + y*y)
        
        # Joint 2 and 3 (simplified)
        theta2 = -1.57 + math.atan2(z - d1, r) * 0.5
        theta3 = math.atan2(z - d1, r) * 0.3
        
        # Wrist joints (simplified orientation)
        theta4 = -theta2 - theta3
        theta5 = 1.57 if abs(math.sin(theta1)) > 0.1 else 0.0
        theta6 = 0.0
        
        return [theta1, theta2, theta3, theta4, theta5, theta6]

    def compute_cartesian_path(self, waypoints: List[List[float]], group_name: str = "ur_manipulator") -> Tuple[List[List[float]], float]:
        """
        Compute cartesian path through waypoints
        
        Args:
            waypoints: List of [x, y, z] positions
            group_name: MoveIt planning group
            
        Returns:
            (trajectory_points, fraction_achieved)
        """
        
        # Convert waypoints to pose messages
        poses = []
        for wp in waypoints:
            poses.append({
                "position": {"x": wp[0], "y": wp[1], "z": wp[2]},
                "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
            })
        
        message = {
            "op": "call_service",
            "service": "/compute_cartesian_path",
            "args": {
                "header": {
                    "frame_id": "base_link"
                },
                "start_state": {
                    "is_diff": False
                },
                "group_name": group_name,
                "link_name": "tool0",
                "waypoints": poses,
                "max_step": 0.01,
                "jump_threshold": 0.0,
                "avoid_collisions": True
            },
            "id": f"cartesian_path_{hash(str(waypoints)) % 10000}"
        }
        
        try:
            self.ws_manager.send(message)
            response = self.ws_manager.receive_service_response(timeout=15.0)
            
            if response:
                data = json.loads(response)
                values = data.get("values", {})
                
                trajectory = values.get("solution", {})
                fraction = values.get("fraction", 0.0)
                
                # Extract joint trajectory points
                points = trajectory.get("joint_trajectory", {}).get("points", [])
                joint_positions = []
                
                for point in points:
                    positions = point.get("positions", [])
                    if len(positions) >= 6:
                        joint_positions.append(positions[:6])
                
                return joint_positions, fraction
            
        except Exception as e:
            print(f"Cartesian path computation error: {e}")
            
        return [], 0.0
