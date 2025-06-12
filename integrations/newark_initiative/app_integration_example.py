"""
Example Integration for Newark Agents into HigherSelf Network Server App

This example shows how to integrate the Newark Well initiative agents
into the main FastAPI application of the HigherSelf Network Server.
"""

import os

from fastapi import Depends, FastAPI
from loguru import logger

# Import the Newark integration module
from integrations.newark_initiative.server_integration import (
    get_newark_router,
    initialize_newark,
)

# Create the FastAPI application
app = FastAPI(
    title="HigherSelf Network Server",
    description="API for the HigherSelf Network including Newark Well initiative agents",
    version="1.0.0",
)

# Import other routers from the HigherSelf Network Server
# from routes.main_router import main_router
# from routes.auth_router import auth_router
# etc.


# Add startup event to initialize Newark agents
@app.on_event("startup")
async def startup_event():
    # Initialize other components of the HigherSelf Network Server
    # ...

    # Initialize Newark integration if enabled
    if os.getenv("NEWARK_API_ENABLED", "False").lower() == "true":
        success = await initialize_newark()
        if success:
            logger.info("Newark Well initiative agents initialized successfully")

            # Include the Newark API router
            newark_router = get_newark_router()
            app.include_router(
                newark_router, prefix="/api/newark", tags=["Newark Initiative"]
            )
        else:
            logger.warning(
                "Failed to initialize Newark agents, endpoints not available"
            )
    else:
        logger.info("Newark initiative integration is disabled")


# Include other routers from the HigherSelf Network Server
# app.include_router(main_router)
# app.include_router(auth_router)
# etc.


# Define root endpoint
@app.get("/")
async def root():
    return {
        "name": "HigherSelf Network Server",
        "status": "online",
        "integrations": {
            "newark_well": os.getenv("NEWARK_API_ENABLED", "False").lower() == "true"
        },
    }


# If this file is executed directly, run the server (for development)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
