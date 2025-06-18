#!/usr/bin/env python3
"""
Enhanced Robot Manager for spawning robots from URDF dataset in Ignition Gazebo

This module extends the existing robot manager to support:
- Loading robots from the comprehensive URDF files dataset
- Automatic robot discovery and categorization
- Advanced filtering and search capabilities
- Dataset metadata integration
- Improved robot spawning with dataset robots
"""

import os
import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import yaml
import re
from dataclasses import dataclass, asdict
from enum import Enum

class RobotType(Enum):
    """Robot type categories from the dataset"""
    ROBOTIC_ARM = "robotic arm"
    DUAL_ARM_ROBOT = "dual arm robot"
    MOBILE_ROBOT = "mobile robot"
    MOBILE_MANIPULATOR = "mobile manipulator"
    HUMANOID_ROBOT = "humanoid robot"
    QUADRUPEDAL_ROBOT = "quadrupedal robot"
    END_EFFECTOR = "end effector"
    UNKNOWN = "unknown"

@dataclass
class RobotInfo:
    """Robot information from the dataset"""
    name: str
    variant: str
    robot_type: str
    manufacturer: str
    source: str
    urdf_path: str
    description: str = ""
    default_position: List[float] = None
    default_orientation: List[float] = None
    gripper_mount: str = "tool0"
    supported_grippers: List[str] = None
    specifications: Dict[str, Any] = None

    def __post_init__(self):
        if self.default_position is None:
            self.default_position = [0.0, 0.0, 0.0]
        if self.default_orientation is None:
            self.default_orientation = [0.0, 0.0, 0.0, 1.0]
        if self.supported_grippers is None:
            self.supported_grippers = []
        if self.specifications is None:
            self.specifications = {}

class EnhancedRobotManager:
    """Enhanced Robot Manager with URDF dataset integration"""
    
    def __init__(self, world_name="empty"):
        self.world_name = world_name
        self.spawned_robots = {}  # Track robots in scene
        self.available_robots = {}  # Available robot definitions
        self.available_grippers = {}  # Available gripper definitions
        self.dataset_robots = {}  # Robots from URDF dataset
        
        # Get paths relative to project root (not this file's location)
        self.base_path = Path(__file__).parent.parent.parent  # Go up to project root
        self.urdf_path = self.base_path / "terracotta" / "robots" / "urdf"  # Local URDFs in package
        self.gripper_path = self.base_path / "terracotta" / "robots" / "grippers"  # Local grippers in package
        self.dataset_path = self.base_path / "robots" / "urdf_files_dataset"  # Dataset at project root
        
        # Initialize robot database FIRST (before loading anything that needs it)
        self._initialize_robot_database()
        
        # Load robots and grippers
        self._load_robot_definitions()
        self._load_gripper_definitions()
        self._load_dataset_robots()
    
    def _initialize_robot_database(self):
        """Initialize robot database with known robots from the dataset"""
        # This is extracted from the dataset README table
        self.robot_database = {
            # Universal Robots
            "UR3": {
                "type": "robotic arm",
                "manufacturer": "Universal Robots",
                "specifications": {"reach": 0.5, "payload": 3.0, "dof": 6}
            },
            "UR5": {
                "type": "robotic arm", 
                "manufacturer": "Universal Robots",
                "specifications": {"reach": 0.85, "payload": 5.0, "dof": 6}
            },
            "UR5e": {
                "type": "robotic arm",
                "manufacturer": "Universal Robots", 
                "specifications": {"reach": 0.85, "payload": 5.0, "dof": 6}
            },
            "UR10": {
                "type": "robotic arm",
                "manufacturer": "Universal Robots",
                "specifications": {"reach": 1.3, "payload": 10.0, "dof": 6}
            },
            "UR10e": {
                "type": "robotic arm",
                "manufacturer": "Universal Robots",
                "specifications": {"reach": 1.3, "payload": 12.5, "dof": 6}
            },
            "UR16e": {
                "type": "robotic arm",
                "manufacturer": "Universal Robots",
                "specifications": {"reach": 0.9, "payload": 16.0, "dof": 6}
            },
            
            # Franka Emika
            "Panda": {
                "type": "robotic arm",
                "manufacturer": "Franka Emika",
                "specifications": {"reach": 0.855, "payload": 3.0, "dof": 7}
            },
            "FR3": {
                "type": "robotic arm", 
                "manufacturer": "Franka Emika",
                "specifications": {"reach": 0.855, "payload": 3.0, "dof": 7}
            },
            
            # KUKA
            "LBR iiwa 7": {
                "type": "robotic arm",
                "manufacturer": "KUKA",
                "specifications": {"reach": 0.8, "payload": 7.0, "dof": 7}
            },
            "LBR iiwa 14": {
                "type": "robotic arm",
                "manufacturer": "KUKA", 
                "specifications": {"reach": 0.82, "payload": 14.0, "dof": 7}
            },
            
            # ABB
            "IRB 120": {
                "type": "robotic arm",
                "manufacturer": "ABB",
                "specifications": {"reach": 0.58, "payload": 3.0, "dof": 6}
            },
            "YuMi": {
                "type": "dual arm robot",
                "manufacturer": "ABB", 
                "specifications": {"reach": 0.559, "payload": 0.5, "dof": 14}
            },
            
            # Boston Dynamics
            "Spot": {
                "type": "quadrupedal robot",
                "manufacturer": "Boston Dynamics",
                "specifications": {"payload": 14.0, "speed": 1.6}
            },
            "Atlas": {
                "type": "humanoid robot",
                "manufacturer": "Boston Dynamics",
                "specifications": {"height": 1.5, "weight": 80.0}
            },
            
            # Fetch Robotics
            "Fetch": {
                "type": "mobile manipulator", 
                "manufacturer": "Fetch Robotics",
                "specifications": {"reach": 1.2, "payload": 6.0, "dof": 7}
            },
            
            # Kinova
            "Gen3": {
                "type": "robotic arm",
                "manufacturer": "Kinova Robotics",
                "specifications": {"reach": 0.902, "payload": 2.0, "dof": 7}
            },
            
            # Grippers
            "2F-85 gripper": {
                "type": "end effector",
                "manufacturer": "Robotiq",
                "specifications": {"stroke": 85, "force": 235}
            },
            "2F-140 gripper": {
                "type": "end effector", 
                "manufacturer": "Robotiq",
                "specifications": {"stroke": 140, "force": 125}
            }
        }
    
    def _load_robot_definitions(self):
        """Load robot definitions from local URDF files"""
        if not self.urdf_path.exists():
            print(f"[EnhancedRobotManager] URDF path not found: {self.urdf_path}")
            return
            
        for urdf_file in self.urdf_path.glob("*.urdf"):
            try:
                robot_name = urdf_file.stem
                
                # Try to load companion config file
                config_file = urdf_file.with_suffix('.yaml')
                config = {}
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f) or {}
                
                # Get robot info from database if available
                db_info = self.robot_database.get(robot_name, {})
                
                robot_info = RobotInfo(
                    name=robot_name,
                    variant="none",
                    robot_type=db_info.get("type", "robotic arm"),
                    manufacturer=db_info.get("manufacturer", "Unknown"),
                    source="local",
                    urdf_path=str(urdf_file),
                    description=config.get("description", f"{robot_name} robot"),
                    default_position=config.get("default_position", [0.0, 0.0, 0.0]),
                    default_orientation=config.get("default_orientation", [0.0, 0.0, 0.0, 1.0]),
                    gripper_mount=config.get("gripper_mount", "tool0"),
                    supported_grippers=config.get("supported_grippers", []),
                    specifications=db_info.get("specifications", {})
                )
                
                self.available_robots[robot_name] = robot_info
                print(f"[EnhancedRobotManager] Loaded local robot: {robot_name}")
                
            except Exception as e:
                print(f"[EnhancedRobotManager] Error loading robot {urdf_file}: {e}")
    
    def _load_gripper_definitions(self):
        """Load gripper definitions"""
        if not self.gripper_path.exists():
            print(f"[EnhancedRobotManager] Gripper path not found: {self.gripper_path}")
            return
            
        for gripper_file in self.gripper_path.glob("*.urdf"):
            try:
                gripper_name = gripper_file.stem
                
                # Load gripper config
                config_file = gripper_file.with_suffix('.yaml')
                config = {}
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f) or {}
                
                self.available_grippers[gripper_name] = {
                    "urdf_file": str(gripper_file),
                    "config": config,
                    "description": config.get("description", f"{gripper_name} gripper"),
                    "mount_offset": config.get("mount_offset", [0.0, 0.0, 0.0]),
                    "mount_rotation": config.get("mount_rotation", [0.0, 0.0, 0.0, 1.0]),
                    "compatible_robots": config.get("compatible_robots", [])
                }
                print(f"[EnhancedRobotManager] Loaded gripper: {gripper_name}")
                
            except Exception as e:
                print(f"[EnhancedRobotManager] Error loading gripper {gripper_file}: {e}")
    
    def _load_dataset_robots(self):
        """Load robots from the URDF dataset"""
        if not self.dataset_path.exists():
            print(f"[EnhancedRobotManager] Dataset path not found: {self.dataset_path}")
            return
        
        urdf_files_path = self.dataset_path / "urdf_files"
        if not urdf_files_path.exists():
            print(f"[EnhancedRobotManager] Dataset urdf_files not found: {urdf_files_path}")
            return
        
        print(f"[EnhancedRobotManager] Scanning dataset for URDF files...")
        
        # Recursively find all URDF files in the dataset
        for urdf_file in urdf_files_path.rglob("*.urdf"):
            try:
                # Extract robot information from path and filename
                relative_path = urdf_file.relative_to(urdf_files_path)
                source = relative_path.parts[0]  # e.g., 'ros-industrial', 'matlab', etc.
                
                # Get robot name from filename
                robot_filename = urdf_file.stem
                
                # Try to parse manufacturer/robot info from path
                path_parts = relative_path.parts
                manufacturer = "Unknown"
                robot_name = robot_filename
                
                # Extract robot name and variant from filename
                variant = "none"
                
                # Look for robot in database to get proper name
                for db_robot_name, db_info in self.robot_database.items():
                    if db_robot_name.lower() in robot_filename.lower():
                        robot_name = db_robot_name
                        manufacturer = db_info.get("manufacturer", "Unknown")
                        robot_type = db_info.get("type", "unknown")
                        specifications = db_info.get("specifications", {})
                        break
                else:
                    # Fallback to parsing from path/filename
                    robot_type = self._infer_robot_type(robot_filename, str(relative_path))
                    specifications = {}
                
                # Create unique key for this robot instance
                robot_key = f"{source}_{robot_filename}"
                
                robot_info = RobotInfo(
                    name=robot_name,
                    variant=variant,
                    robot_type=robot_type,
                    manufacturer=manufacturer,
                    source=source,
                    urdf_path=str(urdf_file),
                    description=f"{robot_name} from {source}",
                    specifications=specifications
                )
                
                self.dataset_robots[robot_key] = robot_info
                
            except Exception as e:
                print(f"[EnhancedRobotManager] Error processing dataset robot {urdf_file}: {e}")
        
        print(f"[EnhancedRobotManager] Loaded {len(self.dataset_robots)} robots from dataset")
    
    def _infer_robot_type(self, filename: str, path: str) -> str:
        """Infer robot type from filename and path"""
        filename_lower = filename.lower()
        path_lower = path.lower()
        
        # Check for specific patterns
        if any(term in filename_lower for term in ['gripper', 'hand', 'finger']):
            return "end effector"
        elif any(term in filename_lower for term in ['mobile', 'base', 'platform', 'fetch']):
            return "mobile manipulator"
        elif any(term in filename_lower for term in ['humanoid', 'atlas', 'valkyrie']):
            return "humanoid robot"
        elif any(term in filename_lower for term in ['spot', 'anymal', 'quadruped']):
            return "quadrupedal robot"
        elif any(term in filename_lower for term in ['dual', 'two_arm', 'baxter', 'yumi']):
            return "dual arm robot"
        elif any(term in filename_lower for term in ['ur', 'arm', 'manipulator', 'robot']):
            return "robotic arm"
        else:
            return "unknown"
    
    def get_available_robots(self, include_dataset: bool = True) -> Dict[str, RobotInfo]:
        """Get list of available robot definitions"""
        robots = {}
        
        # Add local robots
        for name, robot_info in self.available_robots.items():
            robots[f"local_{name}"] = robot_info
        
        # Add dataset robots if requested
        if include_dataset:
            robots.update(self.dataset_robots)
        
        return robots
    
    def search_robots(self, 
                     name_pattern: str = None,
                     robot_type: str = None, 
                     manufacturer: str = None,
                     source: str = None,
                     include_dataset: bool = True) -> Dict[str, RobotInfo]:
        """Search for robots with filters"""
        all_robots = self.get_available_robots(include_dataset)
        filtered_robots = {}
        
        for key, robot_info in all_robots.items():
            # Apply filters
            if name_pattern and name_pattern.lower() not in robot_info.name.lower():
                continue
            if robot_type and robot_type.lower() != robot_info.robot_type.lower():
                continue
            if manufacturer and manufacturer.lower() not in robot_info.manufacturer.lower():
                continue
            if source and source != robot_info.source:
                continue
            
            filtered_robots[key] = robot_info
        
        return filtered_robots
    
    def get_robot_types(self) -> List[str]:
        """Get list of available robot types"""
        types = set()
        for robot_info in self.get_available_robots().values():
            types.add(robot_info.robot_type)
        return sorted(list(types))
    
    def get_manufacturers(self) -> List[str]:
        """Get list of available manufacturers"""
        manufacturers = set()
        for robot_info in self.get_available_robots().values():
            manufacturers.add(robot_info.manufacturer)
        return sorted(list(manufacturers))
    
    def get_sources(self) -> List[str]:
        """Get list of available sources"""
        sources = set()
        for robot_info in self.get_available_robots().values():
            sources.add(robot_info.source)
        return sorted(list(sources))
    
    def get_spawned_robots(self) -> Dict:
        """Get list of currently spawned robots"""
        return self.spawned_robots.copy()
    
    def spawn_robot(self, robot_key: str, instance_name: Optional[str] = None, 
                   position: List[float] = None, orientation: List[float] = None,
                   gripper_name: Optional[str] = None) -> str:
        """Spawn a robot from local or dataset collection"""
        
        # Get robot from available robots or dataset
        all_robots = self.get_available_robots(include_dataset=True)
        
        if robot_key not in all_robots:
            return f"Robot '{robot_key}' not found. Use search_robots() to find available robots."
        
        robot_info = all_robots[robot_key]
        
        # Generate instance name if not provided
        if instance_name is None:
            instance_name = f"{robot_info.name}_{robot_info.source}_instance"
        
        # Use default position/orientation if not provided
        if position is None:
            position = robot_info.default_position
        if orientation is None:
            orientation = robot_info.default_orientation
        
        # Validate gripper compatibility
        if gripper_name:
            if gripper_name not in self.available_grippers:
                return f"Gripper '{gripper_name}' not found. Available grippers: {list(self.available_grippers.keys())}"
        
        try:
            # Convert URDF to SDF
            sdf_content = self._urdf_to_sdf(robot_info.urdf_path, instance_name, gripper_name)
            
            # Create SDF file
            sdf_dir = "/tmp/robot_models"
            os.makedirs(sdf_dir, exist_ok=True)
            sdf_file_path = f"{sdf_dir}/{instance_name}.sdf"
            
            with open(sdf_file_path, 'w') as f:
                f.write(sdf_content)
            
            # Spawn using Ignition Gazebo
            cmd = [
                'ign', 'service', '-s', f'/world/{self.world_name}/create',
                '--reqtype', 'ignition.msgs.EntityFactory',
                '--reptype', 'ignition.msgs.Boolean',
                '--timeout', '5000',
                '--req', 
                f'sdf_filename: "{sdf_file_path}", '
                f'name: "{instance_name}", '
                f'pose: {{position: {{x: {position[0]}, y: {position[1]}, z: {position[2]}}}, '
                f'orientation: {{x: {orientation[0]}, y: {orientation[1]}, z: {orientation[2]}, w: {orientation[3]}}}}}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Store robot info
                self.spawned_robots[instance_name] = {
                    "robot_key": robot_key,
                    "robot_info": asdict(robot_info),
                    "position": position,
                    "orientation": orientation,
                    "gripper": gripper_name,
                    "sdf_file": sdf_file_path
                }
                
                gripper_msg = f" with {gripper_name} gripper" if gripper_name else ""
                return f"Successfully spawned {robot_info.name} ({robot_info.source}) as '{instance_name}'{gripper_msg} at {position}"
            else:
                return f"Failed to spawn robot: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return f"Timeout while spawning robot {instance_name}"
        except Exception as e:
            return f"Error spawning robot {instance_name}: {e}"
    
    def _urdf_to_sdf(self, urdf_file: str, robot_name: str, gripper_name: Optional[str] = None) -> str:
        """Convert URDF to SDF format, optionally with gripper attached"""
        try:
            # Read the URDF file
            with open(urdf_file, 'r') as f:
                urdf_content = f.read()
            
            # If gripper specified, combine URDFs
            if gripper_name and gripper_name in self.available_grippers:
                urdf_content = self._attach_gripper_urdf(urdf_content, gripper_name)
            
            # Create temporary URDF file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as temp_urdf:
                temp_urdf.write(urdf_content)
                temp_urdf_path = temp_urdf.name
            
            # Convert URDF to SDF using gz command
            try:
                cmd = ['ign', 'sdf', '-p', temp_urdf_path]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    sdf_content = result.stdout
                else:
                    print(f"[EnhancedRobotManager] ign sdf conversion failed: {result.stderr}")
                    # Fallback: create basic SDF wrapper
                    sdf_content = self._create_sdf_wrapper(urdf_content, robot_name)
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print(f"[EnhancedRobotManager] ign command not available, using fallback")
                sdf_content = self._create_sdf_wrapper(urdf_content, robot_name)
            
            # Clean up temporary files
            try:
                os.unlink(temp_urdf_path)
            except:
                pass
            
            return sdf_content
            
        except Exception as e:
            print(f"[EnhancedRobotManager] Error converting URDF to SDF: {e}")
            return self._create_fallback_sdf(robot_name)
    
    def _attach_gripper_urdf(self, robot_urdf: str, gripper_name: str) -> str:
        """Attach gripper URDF to robot URDF"""
        try:
            gripper_info = self.available_grippers[gripper_name]
            
            # Read gripper URDF
            with open(gripper_info["urdf_file"], 'r') as f:
                gripper_urdf = f.read()
            
            # Parse both URDFs
            robot_root = ET.fromstring(robot_urdf)
            gripper_root = ET.fromstring(gripper_urdf)
            
            # Get mount point and offset
            mount_offset = gripper_info.get("mount_offset", [0.0, 0.0, 0.0])
            mount_rotation = gripper_info.get("mount_rotation", [0.0, 0.0, 0.0])
            
            # Add gripper links to robot
            for link in gripper_root.findall("link"):
                original_name = link.get("name")
                new_name = f"gripper_{original_name}"
                link.set("name", new_name)
                robot_root.append(link)
            
            # Add gripper joints to robot
            for joint in gripper_root.findall("joint"):
                original_name = joint.get("name")
                new_name = f"gripper_{original_name}"
                joint.set("name", new_name)
                
                # Update child link names
                child = joint.find("child")
                if child is not None:
                    old_child = child.get("link")
                    child.set("link", f"gripper_{old_child}")
                
                # Update parent link names (except for mount joint)
                parent = joint.find("parent")
                if parent is not None:
                    old_parent = parent.get("link")
                    if old_parent != "tool0":  # Don't rename mount link
                        parent.set("link", f"gripper_{old_parent}")
                
                robot_root.append(joint)
            
            # Create mount joint between robot and gripper
            mount_joint = ET.Element("joint", name=f"{gripper_name}_mount", type="fixed")
            ET.SubElement(mount_joint, "parent", link="tool0")
            ET.SubElement(mount_joint, "child", link=f"gripper_{gripper_root.find('link').get('name')}")
            
            # Add mount offset
            origin = ET.SubElement(mount_joint, "origin")
            origin.set("xyz", f"{mount_offset[0]} {mount_offset[1]} {mount_offset[2]}")
            origin.set("rpy", f"{mount_rotation[0]} {mount_rotation[1]} {mount_rotation[2]}")
            
            robot_root.append(mount_joint)
            
            return ET.tostring(robot_root, encoding='unicode')
            
        except Exception as e:
            print(f"[EnhancedRobotManager] Error attaching gripper: {e}")
            return robot_urdf
    
    def _create_sdf_wrapper(self, urdf_content: str, robot_name: str) -> str:
        """Create SDF wrapper around URDF content"""
        return f"""<?xml version="1.0"?>
<sdf version="1.6">
  <model name="{robot_name}">
    {urdf_content}
  </model>
</sdf>"""
    
    def _create_fallback_sdf(self, robot_name: str) -> str:
        """Create fallback SDF for when URDF loading fails"""
        return f"""<?xml version="1.0"?>
<sdf version="1.6">
  <model name="{robot_name}">
    <static>false</static>
    <link name="base_link">
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
            <size>0.2 0.2 0.1</size>
          </box>
        </geometry>
      </collision>
      <visual name="visual">
        <geometry>
          <box>
            <size>0.2 0.2 0.1</size>
          </box>
        </geometry>
        <material>
          <ambient>0.5 0.5 0.5 1</ambient>
          <diffuse>0.8 0.8 0.8 1</diffuse>
        </material>
      </visual>
    </link>
  </model>
</sdf>"""
    
    def remove_robot(self, instance_name: str) -> str:
        """Remove a robot from the scene"""
        try:
            cmd = [
                'ign', 'service', '-s', f'/world/{self.world_name}/remove',
                '--reqtype', 'ignition.msgs.Entity',
                '--reptype', 'ignition.msgs.Boolean',
                '--timeout', '5000',
                '--req', f'name: "{instance_name}", type: MODEL'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Clean up tracking and files
                if instance_name in self.spawned_robots:
                    robot_info = self.spawned_robots[instance_name]
                    sdf_file = robot_info.get("sdf_file")
                    if sdf_file and os.path.exists(sdf_file):
                        try:
                            os.remove(sdf_file)
                        except:
                            pass
                    del self.spawned_robots[instance_name]
                
                return f"Successfully removed robot '{instance_name}'"
            else:
                return f"Failed to remove robot: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return f"Timeout while removing robot {instance_name}"
        except Exception as e:
            return f"Error removing robot {instance_name}: {e}"
    
    def move_robot(self, instance_name: str, position: List[float], 
                  orientation: List[float] = None) -> str:
        """Move a robot to a new pose"""
        if instance_name not in self.spawned_robots:
            return f"Robot '{instance_name}' not found in scene"
        
        if orientation is None:
            orientation = [0.0, 0.0, 0.0, 1.0]
        
        try:
            cmd = [
                'ign', 'service', '-s', f'/world/{self.world_name}/set_pose',
                '--reqtype', 'ignition.msgs.Pose',
                '--reptype', 'ignition.msgs.Boolean',
                '--timeout', '5000',
                '--req', 
                f'name: "{instance_name}", '
                f'position: {{x: {position[0]}, y: {position[1]}, z: {position[2]}}}, '
                f'orientation: {{x: {orientation[0]}, y: {orientation[1]}, z: {orientation[2]}, w: {orientation[3]}}}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Update tracking
                self.spawned_robots[instance_name]["position"] = position
                self.spawned_robots[instance_name]["orientation"] = orientation
                return f"Successfully moved robot '{instance_name}' to {position}"
            else:
                return f"Failed to move robot: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return f"Timeout while moving robot {instance_name}"
        except Exception as e:
            return f"Error moving robot {instance_name}: {e}"
    
    def clear_all_robots(self) -> str:
        """Remove all spawned robots"""
        results = []
        for robot_name in list(self.spawned_robots.keys()):
            result = self.remove_robot(robot_name)
            results.append(f"{robot_name}: {result}")
        
        return f"Cleared {len(results)} robots. " + " ".join(results)
    
    def get_robot_statistics(self) -> Dict[str, Any]:
        """Get statistics about the robot dataset"""
        all_robots = self.get_available_robots(include_dataset=True)
        
        stats = {
            "total_robots": len(all_robots),
            "local_robots": len(self.available_robots),
            "dataset_robots": len(self.dataset_robots),
            "by_type": {},
            "by_manufacturer": {},
            "by_source": {},
            "spawned_robots": len(self.spawned_robots)
        }
        
        # Count by type
        for robot_info in all_robots.values():
            robot_type = robot_info.robot_type
            stats["by_type"][robot_type] = stats["by_type"].get(robot_type, 0) + 1
        
        # Count by manufacturer
        for robot_info in all_robots.values():
            manufacturer = robot_info.manufacturer
            stats["by_manufacturer"][manufacturer] = stats["by_manufacturer"].get(manufacturer, 0) + 1
        
        # Count by source
        for robot_info in all_robots.values():
            source = robot_info.source
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
        
        return stats
    
    def export_robot_catalog(self, output_file: str = None) -> str:
        """Export robot catalog to JSON file"""
        all_robots = self.get_available_robots(include_dataset=True)
        
        catalog = {
            "metadata": {
                "total_robots": len(all_robots),
                "generated_by": "EnhancedRobotManager",
                "sources": self.get_sources()
            },
            "robots": {}
        }
        
        for key, robot_info in all_robots.items():
            catalog["robots"][key] = asdict(robot_info)
        
        if output_file is None:
            output_file = "/tmp/robot_catalog.json"
        
        try:
            with open(output_file, 'w') as f:
                json.dump(catalog, f, indent=2)
            return f"Robot catalog exported to {output_file}"
        except Exception as e:
            return f"Error exporting catalog: {e}"
    
    def find_similar_robots(self, robot_key: str, max_results: int = 5) -> List[Tuple[str, RobotInfo, float]]:
        """Find robots similar to the given robot"""
        all_robots = self.get_available_robots(include_dataset=True)
        
        if robot_key not in all_robots:
            return []
        
        target_robot = all_robots[robot_key]
        similar_robots = []
        
        for key, robot_info in all_robots.items():
            if key == robot_key:
                continue
            
            similarity_score = 0.0
            
            # Same type gets high score
            if robot_info.robot_type == target_robot.robot_type:
                similarity_score += 40.0
            
            # Same manufacturer gets medium score
            if robot_info.manufacturer == target_robot.manufacturer:
                similarity_score += 30.0
            
            # Similar name gets low score
            if target_robot.name.lower() in robot_info.name.lower() or robot_info.name.lower() in target_robot.name.lower():
                similarity_score += 20.0
            
            # Compare specifications if available
            if target_robot.specifications and robot_info.specifications:
                spec_matches = 0
                for spec_key in target_robot.specifications:
                    if spec_key in robot_info.specifications:
                        target_val = target_robot.specifications[spec_key]
                        robot_val = robot_info.specifications[spec_key]
                        if isinstance(target_val, (int, float)) and isinstance(robot_val, (int, float)):
                            # Score based on how close the values are
                            if target_val > 0:
                                ratio = min(target_val, robot_val) / max(target_val, robot_val)
                                spec_matches += ratio * 2.0  # Max 2 points per spec
                        elif target_val == robot_val:
                            spec_matches += 2.0
                similarity_score += spec_matches
            
            if similarity_score > 0:
                similar_robots.append((key, robot_info, similarity_score))
        
        # Sort by similarity score and return top results
        similar_robots.sort(key=lambda x: x[2], reverse=True)
        return similar_robots[:max_results]