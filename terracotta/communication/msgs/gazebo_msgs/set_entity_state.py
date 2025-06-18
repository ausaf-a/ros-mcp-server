import json
from typing import List


class SetEntityState:
    """Set entity pose/state in Gazebo via rosbridge websocket"""
    
    def __init__(self, ws_manager, service_name="/set_entity_state"):
        self.ws_manager = ws_manager
        self.service_name = service_name

    def set_model_pose(self, name: str, position: List[float] = [0.0, 0.0, 0.0],
                      orientation: List[float] = [0.0, 0.0, 0.0, 1.0],
                      linear_velocity: List[float] = [0.0, 0.0, 0.0],
                      angular_velocity: List[float] = [0.0, 0.0, 0.0]) -> str:
        """Set model pose and velocity in Gazebo"""
        
        message = {
            "op": "call_service", 
            "service": self.service_name,
            "args": {
                "state": {
                    "name": name,
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
                    },
                    "twist": {
                        "linear": {
                            "x": linear_velocity[0],
                            "y": linear_velocity[1],
                            "z": linear_velocity[2]
                        },
                        "angular": {
                            "x": angular_velocity[0],
                            "y": angular_velocity[1],
                            "z": angular_velocity[2]
                        }
                    },
                    "reference_frame": "world"
                }
            },
            "id": f"set_pose_{name}_{hash(name) % 10000}"
        }
        
        try:
            self.ws_manager.send(message)
            response = self.ws_manager.receive_service_response(timeout=5.0)
            
            if response:
                data = json.loads(response)
                if data.get("result", False):
                    return f"Successfully set pose for {name}"
                else:
                    return f"Failed to set pose for {name}: {data.get('values', {})}"
            else:
                return f"No response when setting pose for {name}"
                
        except Exception as e:
            return f"Error setting pose for {name}: {e}"
