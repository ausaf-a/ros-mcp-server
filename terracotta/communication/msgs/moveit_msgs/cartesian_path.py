import json
from typing import List, Tuple


class CartesianPath:
    """Cartesian path planning via rosbridge websocket"""
    
    def __init__(self, ws_manager, service_name="/compute_cartesian_path"):
        self.ws_manager = ws_manager
        self.service_name = service_name

    def plan_cartesian_path(self, waypoints: List[List[float]], 
                           group_name: str = "ur_manipulator",
                           max_step: float = 0.01) -> Tuple[List[List[float]], float]:
        """
        Plan a cartesian path through multiple waypoints
        
        Args:
            waypoints: List of [x, y, z] positions to move through
            group_name: MoveIt planning group name
            max_step: Maximum step size for path interpolation
            
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
            "service": self.service_name,
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
                "max_step": max_step,
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
            print(f"Cartesian path planning error: {e}")
            
        return [], 0.0
