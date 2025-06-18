import json


class DeleteEntity:
    """Delete entities from Gazebo via rosbridge websocket"""
    
    def __init__(self, ws_manager, service_name="/delete_entity"):
        self.ws_manager = ws_manager
        self.service_name = service_name

    def delete_model(self, name: str) -> str:
        """Delete a model from Gazebo"""
        
        message = {
            "op": "call_service",
            "service": self.service_name,
            "args": {
                "name": name
            },
            "id": f"delete_{name}_{hash(name) % 10000}"
        }
        
        try:
            self.ws_manager.send(message)
            response = self.ws_manager.receive_service_response(timeout=5.0)
            
            if response:
                data = json.loads(response)
                if data.get("result", False):
                    return f"Successfully deleted {name}"
                else:
                    return f"Failed to delete {name}: {data.get('values', {})}"
            else:
                return f"No response when deleting {name}"
                
        except Exception as e:
            return f"Error deleting {name}: {e}"
