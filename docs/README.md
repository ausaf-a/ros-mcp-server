# Robot + Scene Management System Documentation

This directory contains the complete architecture and design documentation for the enhanced MCP server with URDF dataset integration and hybrid scene management system.

## 📚 Documentation Overview

### Core Architecture
- **[System Architecture](./architecture.md)** - Complete system overview and component relationships
- **[Data Flow Design](./data-flow.md)** - How data moves through the system during operations
- **[Scene Management](./scene-management.md)** - Hybrid scene composition system (SDF + USD + Fuel)

### Component Documentation  
- **[Robot Management](./robot-management.md)** - URDF dataset integration and robot control
- **[Object Repository](./object-repository.md)** - Fuel integration and object management
- **[USD Integration](./usd-integration.md)** - USD format for advanced scene composition

### Implementation Guides
- **[API Reference](./api-reference.md)** - Complete MCP tool functions and usage
- **[Setup Guide](./setup-guide.md)** - Installation and configuration instructions
- **[Usage Examples](./usage-examples.md)** - Common workflows and use cases

### Development
- **[Contributing](./contributing.md)** - Development guidelines and contribution process
- **[Roadmap](./roadmap.md)** - Future features and planned enhancements

## 🚀 Quick Start

1. Read [System Architecture](./architecture.md) for high-level understanding
2. Follow [Setup Guide](./setup-guide.md) for installation
3. Try [Usage Examples](./usage-examples.md) for hands-on experience

## 🎯 Key Features

### Robot Management
- **300+ robots** from comprehensive URDF dataset
- **Intelligent search** by name, type, manufacturer, specifications
- **Multi-robot spawning** and control by instance name
- **Natural language interface** for robot discovery

### Scene Management  
- **Hybrid approach** combining SDF, USD, and Fuel models
- **Template-based** scene creation (factory, warehouse, lab)
- **Dynamic object placement** from Fuel repository
- **Collaborative editing** through USD layers

### Integration
- **Gazebo compatibility** through SDF format
- **Industry standards** through USD format
- **Existing assets** through Fuel integration
- **Version control** through layered composition

## 🏗️ System Components

```
MCP Server
├── Robot Management (Enhanced)
│   ├── URDF Dataset (300+ robots)
│   ├── Search Engine
│   └── Multi-Robot Control
├── Scene Management (New)
│   ├── Template System
│   ├── Object Repository (Fuel)
│   └── USD Integration
└── Communication Layer
    ├── WebSocket → ROS2 → Gazebo
    └── Real-time Control
```

## 📖 Architecture Philosophy

### Design Principles
1. **Hybrid Compatibility** - Support multiple formats for different use cases
2. **Industry Standards** - Leverage USD for future-proofing
3. **Collaborative Workflow** - Enable team-based scene development
4. **Natural Interface** - Human-friendly robot and scene management

### Technical Decisions
- **SDF for Gazebo** - Immediate simulation compatibility
- **USD for Composition** - Advanced scene layering and collaboration  
- **Fuel for Assets** - Leverage existing object repository
- **Backwards Compatibility** - Existing robot management continues to work

## 🔄 Workflow Integration

### Typical User Journey
1. **Discovery**: Search for robots and objects using natural language
2. **Composition**: Build scenes using templates and custom objects
3. **Simulation**: Spawn multiple robots and interact with scene
4. **Collaboration**: Share and version scenes with team members

### Development Workflow
1. **Scene Templates** developed in USD with multiple layers
2. **Object Integration** from Fuel repository via API
3. **Robot Integration** from URDF dataset with specifications
4. **Testing & Validation** in Gazebo simulation environment

---

For detailed information, explore the individual documentation files in this directory.
