"""
Launch Manager - Minimal process management for Gazebo and ROS bridge
"""

import subprocess
import time
from typing import Dict, Optional, Any


class LaunchManager:
    """Minimal launch manager for Gazebo and ROS bridge"""
    
    def __init__(self):
        self.gazebo_process = None
        self.bridge_process = None
        self.robot_processes = {}  # robot_name -> process
    
    def start_gazebo(self, world_name: str = "empty.sdf") -> str:
        """Start Ignition Gazebo"""
        if self.gazebo_process and self.gazebo_process.poll() is None:
            return "Gazebo already running"
        
        try:
            # Set up environment for GUI applications
            env = {
                "DISPLAY": ":0",
                "PATH": "/home/ausaf/anaconda3/envs/ros-env/bin:/home/ausaf/anaconda3/condabin:/home/ausaf/.nvm/versions/node/v20.19.2/bin:/opt/ros/humble/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin",
                "HOME": "/home/ausaf",
                "USER": "ausaf",
                "USERNAME": "ausaf",
                "QT_ACCESSIBILITY": "1",
                "QT_IM_MODULE": "ibus",
                # ROS environment variables
                "ROS_VERSION": "2",
                "ROS_PYTHON_VERSION": "3",
                "ROS_DISTRO": "humble",
                "ROS_LOCALHOST_ONLY": "0",
                "AMENT_PREFIX_PATH": "/opt/ros/humble",
                "PYTHONPATH": "/opt/ros/humble/lib/python3.10/site-packages:/opt/ros/humble/local/lib/python3.10/dist-packages",
                "LD_LIBRARY_PATH": "/opt/ros/humble/opt/rviz_ogre_vendor/lib:/opt/ros/humble/lib/x86_64-linux-gnu:/opt/ros/humble/lib"
            }
            
            cmd = ["/usr/bin/ign", "gazebo", "-v", "4", world_name]
            self.gazebo_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            time.sleep(3)  # Give Gazebo time to start
            
            if self.gazebo_process.poll() is None:
                return f"Gazebo started with world '{world_name}'"
            else:
                # Process failed - get the actual error
                stdout, stderr = self.gazebo_process.communicate()
                error_msg = stderr.decode().strip() if stderr else stdout.decode().strip()
                return f"Failed to start Gazebo: {error_msg}"
        except Exception as e:
            return f"Error starting Gazebo: {e}"
    
    def start_bridge(self) -> str:
        """Start ROS WebSocket bridge"""
        if self.bridge_process and self.bridge_process.poll() is None:
            return "Bridge already running"
        
        try:
            # Set up environment for ROS applications
            env = {
                "DISPLAY": ":0",
                "PATH": "/home/ausaf/.nvm/versions/node/v20.19.2/bin:/opt/ros/humble/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin",
                "HOME": "/home/ausaf",
                "USER": "ausaf",
                "USERNAME": "ausaf",
                "QT_ACCESSIBILITY": "1",
                "QT_IM_MODULE": "ibus",
                # ROS environment variables
                "ROS_VERSION": "2",
                "ROS_PYTHON_VERSION": "3",
                "ROS_DISTRO": "humble",
                "ROS_LOCALHOST_ONLY": "0",
                "AMENT_PREFIX_PATH": "/opt/ros/humble",
                "PYTHONPATH": "/opt/ros/humble/lib/python3.10/site-packages:/opt/ros/humble/local/lib/python3.10/dist-packages",
                "LD_LIBRARY_PATH": "/opt/ros/humble/opt/rviz_ogre_vendor/lib:/opt/ros/humble/lib/x86_64-linux-gnu:/opt/ros/humble/lib"
            }
            
            cmd = ["/opt/ros/humble/bin/ros2", "launch", "rosbridge_server", "rosbridge_websocket_launch.xml"]
            self.bridge_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
            time.sleep(2)  # Give bridge time to start
            
            if self.bridge_process.poll() is None:
                return "ROS WebSocket bridge started"
            else:
                # Process failed - get the actual error
                stdout, stderr = self.bridge_process.communicate()
                error_msg = stderr.decode().strip() if stderr else stdout.decode().strip()
                return f"Failed to start bridge: {error_msg}"
        except Exception as e:
            return f"Error starting bridge: {e}"
    
    def start_simulation(self, world_name: str = "empty") -> str:
        """Start complete simulation stack"""
        results = []
        
        # Start Gazebo first
        gazebo_result = self.start_gazebo(world_name)
        results.append(f"Gazebo: {gazebo_result}")
        
        # Start bridge
        bridge_result = self.start_bridge()
        results.append(f"Bridge: {bridge_result}")
        
        return ". ".join(results)
    
    def stop_gazebo(self) -> str:
        """Stop Gazebo"""
        if not self.gazebo_process:
            return "Gazebo not running"
        
        try:
            self.gazebo_process.terminate()
            self.gazebo_process.wait(timeout=5)
            self.gazebo_process = None
            return "Gazebo stopped"
        except subprocess.TimeoutExpired:
            self.gazebo_process.kill()
            self.gazebo_process = None
            return "Gazebo force killed"
        except Exception as e:
            return f"Error stopping Gazebo: {e}"
    
    def stop_bridge(self) -> str:
        """Stop ROS bridge"""
        if not self.bridge_process:
            return "Bridge not running"
        
        try:
            self.bridge_process.terminate()
            self.bridge_process.wait(timeout=5)
            self.bridge_process = None
            return "Bridge stopped"
        except subprocess.TimeoutExpired:
            self.bridge_process.kill()
            self.bridge_process = None
            return "Bridge force killed"
        except Exception as e:
            return f"Error stopping bridge: {e}"
    
    def stop_simulation(self) -> str:
        """Stop complete simulation stack"""
        results = []
        
        # Stop robot processes first
        for robot_name in list(self.robot_processes.keys()):
            result = self.stop_robot_nodes(robot_name)
            results.append(f"Robot {robot_name}: {result}")
        
        # Stop bridge
        bridge_result = self.stop_bridge()
        results.append(f"Bridge: {bridge_result}")
        
        # Stop Gazebo last
        gazebo_result = self.stop_gazebo()
        results.append(f"Gazebo: {gazebo_result}")
        
        return ". ".join(results)
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all processes"""
        return {
            "gazebo_running": self.gazebo_process and self.gazebo_process.poll() is None,
            "bridge_running": self.bridge_process and self.bridge_process.poll() is None,
            "robot_processes": len(self.robot_processes),
            "active_robots": list(self.robot_processes.keys())
        }
    
    def start_robot_nodes(self, robot_name: str, robot_type: str) -> str:
        """Start ROS nodes for a specific robot (placeholder)"""
        # TODO: Implement dynamic robot node launching based on robot_type
        # For now, just track that we would start nodes
        self.robot_processes[robot_name] = f"placeholder_for_{robot_type}"
        return f"Robot nodes started for {robot_name} ({robot_type})"
    
    def stop_robot_nodes(self, robot_name: str) -> str:
        """Stop ROS nodes for a specific robot"""
        if robot_name in self.robot_processes:
            # TODO: Actually terminate robot processes
            del self.robot_processes[robot_name]
            return f"Robot nodes stopped for {robot_name}"
        return f"No robot nodes found for {robot_name}"
