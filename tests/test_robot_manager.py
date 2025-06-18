"""Tests for Robot Manager"""
import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from terracotta.robots.manager import EnhancedRobotManager, RobotInfo


class TestEnhancedRobotManager:
    """Test cases for EnhancedRobotManager"""
    
    def test_manager_initialization(self, temp_dir):
        """Test manager can be initialized"""
        manager = EnhancedRobotManager("test_world")
        assert manager.world_name == "test_world"
        assert isinstance(manager.spawned_robots, dict)
        assert isinstance(manager.available_robots, dict)
        
    def test_robot_database_loaded(self):
        """Test robot database contains expected robots"""
        manager = EnhancedRobotManager()
        
        # Check some known robots are in database
        expected_robots = ["UR5", "UR5e", "Panda", "YuMi"]
        for robot_name in expected_robots:
            assert robot_name in manager.robot_database
            
    def test_get_robot_types(self):
        """Test getting available robot types"""
        manager = EnhancedRobotManager()
        types = manager.get_robot_types()
        assert isinstance(types, list)
        assert "robotic arm" in types
        
    def test_get_manufacturers(self):
        """Test getting available manufacturers"""
        manager = EnhancedRobotManager()
        manufacturers = manager.get_manufacturers()
        assert isinstance(manufacturers, list)
        assert "Universal Robots" in manufacturers
        
    def test_get_sources(self):
        """Test getting available sources"""
        manager = EnhancedRobotManager()
        sources = manager.get_sources()
        assert isinstance(sources, list)
        
    def test_search_robots_by_name(self):
        """Test searching robots by name pattern"""
        manager = EnhancedRobotManager()
        
        # Search for UR robots
        ur_robots = manager.search_robots(name_pattern="UR")
        assert isinstance(ur_robots, dict)
        
        # Check that all results contain "UR" in name (if any found)
        if ur_robots:
            for robot_info in ur_robots.values():
                assert "UR" in robot_info.name or "ur" in robot_info.name.lower()
        
        # Test case-insensitive search with a common pattern
        robot_results = manager.search_robots(name_pattern="robot")
        assert isinstance(robot_results, dict)
        
        # If we found any robots, verify search works
        if robot_results:
            for robot_info in robot_results.values():
                assert "robot" in robot_info.name.lower()
            
    def test_search_robots_by_type(self):
        """Test searching robots by type"""
        manager = EnhancedRobotManager()
        
        # Search for robotic arms
        arms = manager.search_robots(robot_type="robotic arm")
        assert isinstance(arms, dict)
        
        # All results should be robotic arms
        for robot_info in arms.values():
            assert robot_info.robot_type == "robotic arm"
            
    def test_search_robots_by_manufacturer(self):
        """Test searching robots by manufacturer"""
        manager = EnhancedRobotManager()
        
        # Search for Universal Robots
        ur_robots = manager.search_robots(manufacturer="Universal Robots")
        assert isinstance(ur_robots, dict)
        
        # All results should be from Universal Robots
        for robot_info in ur_robots.values():
            assert robot_info.manufacturer == "Universal Robots"
            
    def test_get_robot_statistics(self):
        """Test getting robot statistics"""
        manager = EnhancedRobotManager()
        stats = manager.get_robot_statistics()
        
        assert isinstance(stats, dict)
        assert "total_robots" in stats
        assert "by_type" in stats
        assert "by_manufacturer" in stats
        assert stats["total_robots"] >= 0
        
    def test_find_similar_robots(self):
        """Test finding similar robots"""
        manager = EnhancedRobotManager()
        
        # Get all robots first
        all_robots = manager.get_available_robots(include_dataset=True)
        if all_robots:
            # Pick first robot and find similar ones
            robot_key = list(all_robots.keys())[0]
            similar = manager.find_similar_robots(robot_key, max_results=3)
            
            assert isinstance(similar, list)
            assert len(similar) <= 3


class TestRobotInfo:
    """Test cases for RobotInfo dataclass"""
    
    def test_robot_info_creation(self):
        """Test creating RobotInfo instance"""
        robot = RobotInfo(
            name="TestRobot",
            variant="v1",
            robot_type="robotic arm",
            manufacturer="TestCorp",
            source="test",
            urdf_path="/test/path.urdf"
        )
        
        assert robot.name == "TestRobot"
        assert robot.robot_type == "robotic arm"
        assert robot.default_position == [0.0, 0.0, 0.0]
        assert robot.supported_grippers == []
        
    def test_robot_info_defaults(self):
        """Test RobotInfo default values"""
        robot = RobotInfo(
            name="Test",
            variant="none",
            robot_type="arm",
            manufacturer="Test",
            source="test",
            urdf_path="/test.urdf"
        )
        
        # Check defaults are set correctly
        assert robot.default_position == [0.0, 0.0, 0.0]
        assert robot.default_orientation == [0.0, 0.0, 0.0, 1.0]
        assert robot.gripper_mount == "tool0"
        assert robot.supported_grippers == []
        assert robot.specifications == {}
