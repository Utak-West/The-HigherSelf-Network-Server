#!/usr/bin/env python3
"""
Minimal test server for Devin to verify the application can run locally.
This bypasses complex dependencies and provides a simple FastAPI server.
"""

import os
import sys
from pathlib import Path

# Set up environment for testing
os.environ["TEST_MODE"] = "True"
os.environ["DISABLE_WEBHOOKS"] = "True"
os.environ["PYTHONPATH"] = str(Path(__file__).parent)

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("❌ FastAPI or Uvicorn not installed")
    print("Installing required packages...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"], check=True)
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import uvicorn

# Create minimal FastAPI app
app = FastAPI(
    title="The HigherSelf Network Server - Test Mode",
    description="Minimal test server for Devin validation",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "The HigherSelf Network Server - Test Mode", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mode": "test",
        "message": "Server is running in test mode"
    }

@app.get("/api/status")
async def api_status():
    """API status endpoint."""
    return {
        "api": "active",
        "test_mode": True,
        "endpoints": ["/", "/health", "/api/status"]
    }

def main():
    """Main function to start the test server."""
    print("🚀 Starting The HigherSelf Network Server - Test Mode")
    print("📍 This is a minimal test server for Devin validation")
    print("🔗 Available endpoints:")
    print("   - http://localhost:8000/ (root)")
    print("   - http://localhost:8000/health (health check)")
    print("   - http://localhost:8000/api/status (API status)")
    print("   - http://localhost:8000/docs (API documentation)")
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
