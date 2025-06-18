import json
from typing import List, Any


class SpawnEntity:
    """Gazebo entity spawning via rosbridge websocket"""
    
    def __init__(self, ws_manager, service_name="/spawn_entity"):
        self.ws_manager = ws_manager
        self.service_name = service_name

    def spawn_model(self, name: str, xml: str, robot_namespace: str = "", 
                   position: List[float] = [0.0, 0.0, 0.0], 
                   orientation: List[float] = [0.0, 0.0, 0.0, 1.0]) -> str:
        """
        Spawn a model in Gazebo
        
        Args:
            name: Model name
            xml: SDF/URDF XML content  
            robot_namespace: Namespace for the robot
            position: [x, y, z] position
            orientation: [x, y, z, w] quaternion
        """
        
        message = {
            "op": "call_service",
            "service": self.service_name,
            "args": {
                "name": name,
                "xml": xml,
                "robot_namespace": robot_namespace,
                "initial_pose": {
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
                "reference_frame": "world"
            },
            "id": f"spawn_{name}_{hash(name) % 10000}"
        }
        
        try:
            self.ws_manager.send(message)
            response = self.ws_manager.receive_service_response(timeout=10.0)
            
            if response:
                data = json.loads(response)
                if data.get("result", False):
                    return f"Successfully spawned {name}"
                else:
                    return f"Failed to spawn {name}: {data.get('values', {})}"
            else:
                return f"No response when spawning {name}"
                
        except Exception as e:
            return f"Error spawning {name}: {e}"

    def spawn_box(self, name: str, size: List[float] = [0.1, 0.1, 0.1], 
                  position: List[float] = [0.0, 0.0, 0.0], 
                  color: str = "red") -> str:
        """Spawn a colored box"""
        
        # Color mapping for Gazebo materials
        color_materials = {
            "red": "Gazebo/Red",
            "blue": "Gazebo/Blue", 
            "green": "Gazebo/Green",
            "yellow": "Gazebo/Yellow",
            "orange": "Gazebo/Orange",
            "purple": "Gazebo/Purple",
            "white": "Gazebo/White",
            "black": "Gazebo/Black",
            "grey": "Gazebo/Grey"
        }
        
        material = color_materials.get(color.lower(), "Gazebo/Red")
        
        sdf_xml = f"""<?xml version="1.0"?>
<sdf version="1.6">
  <model name="{name}">
    <static>false</static>
    <link name="link">
      <inertial>
        <mass>1.0</mass>
        <inertia>
          <ixx>0.083</ixx>
          <ixy>0.0</ixy>
          <ixz>0.0</ixz>
          <iyy>0.083</iyy>
          <iyz>0.0</iyz>
          <izz>0.083</izz>
        </inertia>
      </inertial>
      <collision name="collision">
        <geometry>
          <box>
            <size>{size[0]} {size[1]} {size[2]}</size>
          </box>
        </geometry>
      </collision>
      <visual name="visual">
        <geometry>
          <box>
            <size>{size[0]} {size[1]} {size[2]}</size>
          </box>
        </geometry>
        <material>
          <script>
            <uri>file://media/materials/scripts/gazebo.material</uri>
            <name>{material}</name>
          </script>
        </material>
      </visual>
    </link>
  </model>
</sdf>"""
        
        return self.spawn_model(name, sdf_xml, position=position)

    def spawn_cylinder(self, name: str, radius: float = 0.05, length: float = 0.1,
                      position: List[float] = [0.0, 0.0, 0.0], 
                      color: str = "blue") -> str:
        """Spawn a colored cylinder"""
        
        color_materials = {
            "red": "Gazebo/Red",
            "blue": "Gazebo/Blue", 
            "green": "Gazebo/Green",
            "yellow": "Gazebo/Yellow",
            "orange": "Gazebo/Orange",
            "purple": "Gazebo/Purple",
            "white": "Gazebo/White",
            "black": "Gazebo/Black",
            "grey": "Gazebo/Grey"
        }
        
        material = color_materials.get(color.lower(), "Gazebo/Blue")
        
        sdf_xml = f"""<?xml version="1.0"?>
<sdf version="1.6">
  <model name="{name}">
    <static>false</static>
    <link name="link">
      <inertial>
        <mass>1.0</mass>
        <inertia>
          <ixx>0.083</ixx>
          <ixy>0.0</ixy>
          <ixz>0.0</ixz>
          <iyy>0.083</iyy>
          <iyz>0.0</iyz>
          <izz>0.083</izz>
        </inertia>
      </inertial>
      <collision name="collision">
        <geometry>
          <cylinder>
            <radius>{radius}</radius>
            <length>{length}</length>
          </cylinder>
        </geometry>
      </collision>
      <visual name="visual">
        <geometry>
          <cylinder>
            <radius>{radius}</radius>
            <length>{length}</length>
          </cylinder>
        </geometry>
        <material>
          <script>
            <uri>file://media/materials/scripts/gazebo.material</uri>
            <name>{material}</name>
          </script>
        </material>
      </visual>
    </link>
  </model>
</sdf>"""
        
        return self.spawn_model(name, sdf_xml, position=position)
