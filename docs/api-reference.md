# API Reference

## Overview

This document provides a comprehensive reference for all MCP tool functions available in the Robot + Scene Management System. The API is organized into functional categories for easy navigation.

## Robot Management API

### Robot Discovery

#### `search_robots_in_dataset`
Search for robots in the URDF dataset with various filters.

```python
@mcp.tool()
def search_robots_in_dataset(
    name_pattern: str = None,
    robot_type: str = None, 
    manufacturer: str = None,
    source: str = None,
    include_dataset: bool = True
) -> Dict[str, Any]:
```

**Parameters:**
- `name_pattern` (str, optional): Pattern to match in robot names (e.g., "UR5", "Panda")
- `robot_type` (str, optional): Filter by type ("robotic arm", "mobile robot", etc.)
- `manufacturer` (str, optional): Filter by manufacturer ("Universal Robots", "ABB", etc.)
- `source` (str, optional): Filter by source ("ros-industrial", "matlab", etc.)
- `include_dataset` (bool): Whether to include dataset robots (default: True)

**Returns:** Dictionary with search results and metadata

**Example:**
```python
# Search for Universal Robots arms
result = search_robots_in_dataset(
    manufacturer="Universal Robots",
    robot_type="robotic arm"
)

# Search for collaborative robots
result = search_robots_in_dataset(name_pattern="cobot")
```

#### `get_dataset_statistics`
Get comprehensive statistics about the robot dataset.

```python
@mcp.tool()
def get_dataset_statistics() -> Dict[str, Any]:
```

**Returns:** Statistics including total robots, breakdown by type, manufacturer, and source

#### `find_collaborative_robots`
Find robots suitable for human-robot collaboration.

```python
@mcp.tool()
def find_collaborative_robots() -> Dict[str, Any]:
```

**Returns:** Dictionary of collaborative robots with specifications

### Robot Spawning

#### `spawn_robot_by_name`
Spawn a robot by name from the dataset.

```python
@mcp.tool()
def spawn_robot_by_name(
    robot_name: str,
    instance_name: str = None,
    position: List[float] = None,
    orientation: List[float] = None,
    source: str = None
) -> str:
```

**Parameters:**
- `robot_name` (str): Name of robot to spawn (e.g., "UR5e", "Panda")
- `instance_name` (str, optional): Unique name for this robot instance
- `position` (List[float], optional): [x, y, z] position in meters
- `orientation` (List[float], optional): [x, y, z, w] quaternion orientation
- `source` (str, optional): Specific source if multiple versions exist

**Returns:** Status message about spawning operation

#### `get_spawned_robots`
Get list of all currently spawned robots.

```python
@mcp.tool()
def get_spawned_robots() -> Dict[str, Any]:
```

**Returns:** Dictionary of spawned robots with their information

### Robot Control

#### `move_robot_by_name`
Move a specific robot to a new position.

```python
@mcp.tool()
def move_robot_by_name(
    instance_name: str,
    position: List[float],
    orientation: List[float] = None
) -> str:
```

#### `move_robot_to_position`
Move robot end-effector to Cartesian position using inverse kinematics.

```python
@mcp.tool()
def move_robot_to_position(
    instance_name: str,
    position: List[float],
    orientation: List[float] = [0.0, 0.0, 0.0, 1.0]
) -> str:
```

#### `compute_inverse_kinematics`
Compute inverse kinematics for a target pose without moving robot.

```python
@mcp.tool()
def compute_inverse_kinematics(
    instance_name: str,
    position: List[float],
    orientation: List[float] = [0.0, 0.0, 0.0, 1.0]
) -> Dict[str, Any]:
```

#### `remove_robot`
Remove a robot from the scene.

```python
@mcp.tool()
def remove_robot(instance_name: str) -> str:
```

## Scene Management API

### Scene Templates

#### `create_scene_from_template`
Create a new scene from a predefined template.

```python
@mcp.tool()
def create_scene_from_template(
    template_name: str,
    config: Dict[str, Any] = None
) -> str:
```

**Parameters:**
- `template_name` (str): Name of template ("factory", "warehouse", "laboratory")
- `config` (Dict, optional): Template customization parameters

#### `list_available_templates`
Get list of available scene templates.

```python
@mcp.tool()
def list_available_templates() -> List[Dict[str, Any]]:
```

### Object Management

#### `search_objects_in_fuel`
Search for objects in the Fuel repository.

```python
@mcp.tool()
def search_objects_in_fuel(
    category: str = None,
    keyword: str = None,
    size_filter: str = None,
    manufacturer: str = None
) -> Dict[str, Any]:
```

#### `add_object_to_scene`
Add an object from Fuel to the current scene.

```python
@mcp.tool()
def add_object_to_scene(
    object_id: str,
    instance_name: str = None,
    position: List[float] = [0, 0, 0],
    rotation: List[float] = [0, 0, 0],
    scale: List[float] = [1, 1, 1]
) -> str:
```

#### `place_conveyor_belt`
Place and configure a conveyor belt system.

```python
@mcp.tool()
def place_conveyor_belt(
    start_position: List[float],
    end_position: List[float],
    belt_config: Dict[str, Any]
) -> str:
```

### Scene State Management

#### `save_scene`
Save current scene in specified format.

```python
@mcp.tool()
def save_scene(
    scene_name: str,
    format: str = "usd"
) -> str:
```

#### `load_scene`
Load a previously saved scene.

```python
@mcp.tool()
def load_scene(scene_path: str) -> str:
```

#### `get_scene_summary`
Get summary of current scene contents.

```python
@mcp.tool()
def get_scene_summary() -> Dict[str, Any]:
```

## Usage Patterns

### Common Workflows

#### Basic Robot Setup
```python
# 1. Search for suitable robot
robots = search_robots_in_dataset(robot_type="robotic arm", manufacturer="Universal Robots")

# 2. Spawn robot
spawn_robot_by_name("UR5e", "main_arm", [0, 0, 0])

# 3. Move robot
move_robot_to_position("main_arm", [0.5, 0.3, 0.2])

# 4. Check robot status
robot_info = get_robot_info("main_arm")
```

#### Factory Scene Creation
```python
# 1. Create factory template
factory_config = {
    "dimensions": {"length": 40, "width": 25, "height": 8},
    "conveyor_count": 2,
    "robot_cells": 3
}
create_scene_from_template("factory", factory_config)

# 2. Add specific equipment
add_object_to_scene("CNC_Machine_01", "cnc1", [10, 5, 0])
place_conveyor_belt([0, 10, 0.8], [35, 10, 0.8], {"speed": 1.2})

# 3. Add robots
spawn_robot_by_name("UR5e", "assembly_robot", [20, 6, 0])
spawn_robot_by_name("Fetch", "material_handler", [5, 15, 0])

# 4. Save scene
save_scene("automotive_line", "usd")
```

#### Multi-Robot Coordination
```python
# 1. Find collaborative robots
cobots = find_collaborative_robots()

# 2. Spawn multiple robots
spawn_robot_by_name("UR5e", "robot1", [0, 1, 0])
spawn_robot_by_name("Panda", "robot2", [0, -1, 0])
spawn_robot_by_name("Fetch", "mobile_helper", [2, 0, 0])

# 3. Coordinate movements
move_robot_by_name("robot1", [0.5, 1, 0.3])
move_robot_by_name("robot2", [0.5, -1, 0.3])
move_robot_by_name("mobile_helper", [1, 0, 0])

# 4. Monitor all robots
all_robots = get_spawned_robots()
```

#### Collaborative Scene Development
```python
# 1. Create collaborative scene
create_collaborative_scene("shared_factory", ["alice", "bob", "charlie"])

# 2. Assign layers to team members
assign_user_layer("shared_factory", "alice", "lighting")
assign_user_layer("shared_factory", "bob", "layout") 
assign_user_layer("shared_factory", "charlie", "robots")

# 3. Each user works on their layer independently
# ... user contributions ...

# 4. Merge final scene
merge_collaborative_scene("shared_factory", "final_factory")
```

## Error Handling

### Standard Error Responses

All API functions return standardized error responses when operations fail:

```python
{
    "success": False,
    "error_type": "InvalidParameter" | "NotFound" | "SystemError",
    "error_message": "Human-readable error description",
    "suggestions": ["Try this", "Or try that"]
}
```

### Common Error Types

#### Robot Management Errors
- `RobotNotFound`: Specified robot not in dataset
- `InstanceNameConflict`: Robot instance name already exists
- `SpawnFailed`: Robot failed to spawn in Gazebo
- `InvalidConfiguration`: Robot configuration parameters invalid

#### Scene Management Errors
- `TemplateNotFound`: Scene template does not exist
- `ObjectNotFound`: Object not found in repository
- `PlacementError`: Object placement failed (collision, bounds, etc.)
- `FormatError`: Invalid scene file format

## Natural Language Interface

The system supports natural language commands that map to API functions:

### Robot Commands
- "Find UR5 robots" → `search_robots_in_dataset(name_pattern="UR5")`
- "Spawn a Panda robot" → `spawn_robot_by_name("Panda")`
- "Move main_arm to position 0.5, 0, 0.3" → `move_robot_to_position("main_arm", [0.5, 0, 0.3])`
- "What robots are currently spawned?" → `get_spawned_robots()`
- "Remove the assembly robot" → `remove_robot("assembly_robot")`

### Scene Commands
- "Create a factory scene" → `create_scene_from_template("factory")`
- "Add a conveyor belt from 0,0,0 to 10,0,0" → `place_conveyor_belt([0,0,0], [10,0,0])`
- "Place a work table at position 5,5,0" → `add_object_to_scene("work_table", position=[5,5,0])`
- "Save the current scene as production_line" → `save_scene("production_line")`

### Information Commands
- "Show me dataset statistics" → `get_dataset_statistics()`
- "What collaborative robots are available?" → `find_collaborative_robots()`
- "Give me a scene summary" → `get_scene_summary()`

## Performance Guidelines

### Optimization Tips

1. **Batch Operations**: Group multiple robot spawns or object placements
2. **Lazy Loading**: Use search functions before spawning to avoid unnecessary loading
3. **Scene Complexity**: Monitor scene complexity with `get_scene_summary()`
4. **Memory Management**: Remove unused robots/objects with cleanup functions

### Rate Limiting

- Robot spawning: Max 10 robots per minute
- Object placement: Max 50 objects per minute  
- Scene operations: Max 5 scene loads per minute
- Search operations: No limit (cached results)

### Best Practices

1. **Instance Naming**: Use descriptive, unique instance names
2. **Position Validation**: Check positions are within scene bounds
3. **Error Handling**: Always check return values for success/failure
4. **Resource Cleanup**: Remove unused robots and objects
5. **Scene Saving**: Regularly save complex scenes to avoid data loss

---

This API reference provides the foundation for building complex robotics scenarios with natural language interfaces, collaborative editing, and industry-standard scene management capabilities.
