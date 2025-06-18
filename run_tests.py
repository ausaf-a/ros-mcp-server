#!/usr/bin/env python3
"""Simple test runner for robot manager tests"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run the robot manager tests"""
    project_root = Path(__file__).parent
    
    print("🧪 Running Robot Manager Tests")
    print("=" * 40)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(project_root / "tests" / "test_robot_manager.py"),
            "-v", "--tb=short"
        ], cwd=project_root, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
            
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
            
        return result.returncode == 0
        
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
