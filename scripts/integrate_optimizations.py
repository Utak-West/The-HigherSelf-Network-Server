#!/usr/bin/env python3
"""
Integration script for HigherSelf Network Server optimizations.

This script helps integrate all performance optimizations into the main server
by updating the necessary files and configurations.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def update_main_server_file():
    """Update the main server file to include optimization integrations."""
    
    main_files = [
        "main.py",
        "app.py", 
        "server.py",
        "api/main.py"
    ]
    
    main_file = None
    for file_path in main_files:
        if os.path.exists(file_path):
            main_file = file_path
            break
    
    if not main_file:
        print("❌ Could not find main server file. Please manually integrate optimizations.")
        return False
    
    print(f"📝 Updating {main_file} with optimization integrations...")
    
    # Read current content
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Check if optimizations are already integrated
    if "optimization_integration" in content:
        print("✅ Optimizations already integrated in main server file")
        return True
    
    # Add optimization imports
    optimization_imports = """
# Performance Optimization Imports
from services.optimization_integration import (
    optimization_manager,
    optimized_server_lifespan,
    initialize_optimizations,
    shutdown_optimizations
)
"""
    
    # Add imports after existing imports
    import_section_end = content.find('\nfrom fastapi')
    if import_section_end == -1:
        import_section_end = content.find('\nimport')
    
    if import_section_end != -1:
        # Find the end of the import section
        lines = content.split('\n')
        insert_line = 0
        for i, line in enumerate(lines):
            if line.strip() and not (line.startswith('import ') or line.startswith('from ') or line.startswith('#')):
                insert_line = i
                break
        
        lines.insert(insert_line, optimization_imports.strip())
        content = '\n'.join(lines)
    
    # Add optimization configuration to FastAPI app creation
    if "FastAPI(" in content:
        # Replace FastAPI app creation with optimized version
        content = content.replace(
            "app = FastAPI(",
            "app = FastAPI(\n    lifespan=optimized_server_lifespan,"
        )
        
        # If no lifespan parameter, add it
        if "lifespan=" not in content:
            content = content.replace(
                "FastAPI()",
                "FastAPI(lifespan=optimized_server_lifespan)"
            )
    
    # Add optimization middleware configuration
    middleware_config = """
# Configure optimization middleware and services
optimization_manager.configure_fastapi_app(app)
"""
    
    # Add after app creation
    app_creation_line = content.find("app = FastAPI")
    if app_creation_line != -1:
        # Find the end of the app creation line
        end_of_line = content.find('\n', app_creation_line)
        content = content[:end_of_line] + '\n' + middleware_config + content[end_of_line:]
    
    # Write updated content
    with open(main_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Successfully updated {main_file} with optimization integrations")
    return True


def create_optimization_endpoints():
    """Create API endpoints for monitoring optimizations."""
    
    endpoints_dir = Path("api/routers")
    endpoints_dir.mkdir(exist_ok=True)
    
    endpoints_file = endpoints_dir / "optimization.py"
    
    if endpoints_file.exists():
        print("✅ Optimization endpoints already exist")
        return True
    
    print("📝 Creating optimization monitoring endpoints...")
    
    endpoints_content = '''"""
Optimization monitoring endpoints for HigherSelf Network Server.

Provides endpoints to monitor and manage performance optimizations.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from services.optimization_integration import optimization_manager

router = APIRouter(prefix="/api/optimization", tags=["optimization"])


@router.get("/health")
async def get_optimization_health() -> Dict[str, Any]:
    """Get health status of all optimization services."""
    try:
        return await optimization_manager.health_check()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/summary")
async def get_optimization_summary() -> Dict[str, Any]:
    """Get performance summary of all optimizations."""
    try:
        return await optimization_manager.get_optimization_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary failed: {str(e)}")


@router.get("/metrics")
async def get_optimization_metrics() -> Dict[str, Any]:
    """Get detailed metrics from all optimization services."""
    try:
        health = await optimization_manager.health_check()
        return health.get("metrics", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics failed: {str(e)}")


@router.get("/recommendations")
async def get_optimization_recommendations() -> Dict[str, Any]:
    """Get optimization recommendations based on current performance."""
    try:
        recommendations = await optimization_manager.performance_monitor.get_optimization_recommendations()
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")


@router.post("/restart")
async def restart_optimization_services() -> Dict[str, Any]:
    """Restart all optimization services."""
    try:
        # Shutdown existing services
        await optimization_manager.shutdown()
        
        # Restart services
        success = await optimization_manager.initialize()
        
        return {
            "success": success,
            "message": "Optimization services restarted successfully" if success else "Some services failed to restart"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restart failed: {str(e)}")
'''
    
    with open(endpoints_file, 'w') as f:
        f.write(endpoints_content)
    
    print(f"✅ Created optimization endpoints at {endpoints_file}")
    return True


def update_requirements():
    """Update requirements.txt with optimization dependencies."""
    
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print("⚠️ requirements.txt not found, creating new one...")
        with open(requirements_file, 'w') as f:
            f.write("")
    
    with open(requirements_file, 'r') as f:
        content = f.read()
    
    # Dependencies needed for optimizations
    optimization_deps = [
        "psutil>=5.9.0",  # For system monitoring
        "aiofiles>=23.0.0",  # For async file operations
    ]
    
    updated = False
    for dep in optimization_deps:
        dep_name = dep.split('>=')[0]
        if dep_name not in content:
            content += f"\n{dep}"
            updated = True
    
    if updated:
        with open(requirements_file, 'w') as f:
            f.write(content)
        print("✅ Updated requirements.txt with optimization dependencies")
    else:
        print("✅ Requirements.txt already contains optimization dependencies")
    
    return True


def create_environment_config():
    """Create environment configuration for optimizations."""
    
    env_example_file = ".env.example"
    
    optimization_env_vars = """
# Performance Optimization Settings
CACHE_DEFAULT_TTL=300
CACHE_MAX_SIZE=10000
PERFORMANCE_MONITORING_ENABLED=true
METRICS_COLLECTION_INTERVAL=30
MAX_CONCURRENT_OPERATIONS=50
CONNECTION_POOL_SIZE=10
ENABLE_COMPRESSION=true
MIN_COMPRESSION_SIZE=1024
OPTIMIZATION_DEBUG=false
"""
    
    if os.path.exists(env_example_file):
        with open(env_example_file, 'r') as f:
            content = f.read()
        
        if "CACHE_DEFAULT_TTL" not in content:
            with open(env_example_file, 'a') as f:
                f.write(optimization_env_vars)
            print("✅ Added optimization environment variables to .env.example")
        else:
            print("✅ Optimization environment variables already in .env.example")
    else:
        with open(env_example_file, 'w') as f:
            f.write(optimization_env_vars)
        print("✅ Created .env.example with optimization environment variables")
    
    return True


def run_integration():
    """Run the complete optimization integration process."""
    
    print("🚀 Starting HigherSelf Network Server optimization integration...")
    print("=" * 60)
    
    steps = [
        ("Updating main server file", update_main_server_file),
        ("Creating optimization endpoints", create_optimization_endpoints),
        ("Updating requirements", update_requirements),
        ("Creating environment config", create_environment_config),
    ]
    
    success_count = 0
    
    for step_name, step_function in steps:
        print(f"\n📋 {step_name}...")
        try:
            if step_function():
                success_count += 1
                print(f"✅ {step_name} completed successfully")
            else:
                print(f"❌ {step_name} failed")
        except Exception as e:
            print(f"❌ {step_name} failed with error: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 Integration completed: {success_count}/{len(steps)} steps successful")
    
    if success_count == len(steps):
        print("\n🎉 All optimizations integrated successfully!")
        print("\nNext steps:")
        print("1. Install new dependencies: pip install -r requirements.txt")
        print("2. Update your .env file with optimization settings")
        print("3. Restart your server to activate optimizations")
        print("4. Monitor performance at /api/optimization/health")
        print("5. Run performance tests: pytest tests/performance/")
    else:
        print("\n⚠️ Some integration steps failed. Please check the errors above.")
        print("You may need to manually complete the failed steps.")
    
    return success_count == len(steps)


if __name__ == "__main__":
    success = run_integration()
    sys.exit(0 if success else 1)
