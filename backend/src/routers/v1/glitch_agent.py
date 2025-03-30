from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional
import logging
import os
from datetime import datetime
import uuid

from src.models.glitch_agent import (
    CommandRequest,
    CommandResponse,
    ExecutionResult,
    ExecutionHistory
)
from src.services.browser_automation_service import BrowserAutomationService
from src.utils.database.mongo_handler import MongoHandler as MongoDBHandler
from dotenv import load_dotenv

load_dotenv()

# Create router
GlitchAgent_Api_Router = APIRouter(prefix="/v1/glitch-agent")

# Initialize MongoDB handler
mongo_handler = MongoDBHandler()

# Dictionary to store active browser automation services
active_services = {}

# Dictionary to store execution results
execution_results = {}


def get_browser_automation_service():
    """Dependency to get the BrowserAutomation service instance"""
    api_key = os.getenv("CLOUDFLARE_API_KEY")
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    
    if not api_key or not account_id:
        logging.error("Missing Cloudflare API credentials")
        raise HTTPException(
            status_code=500, 
            detail="Server configuration error: Missing API credentials"
        )
    
    return BrowserAutomationService(api_key=api_key, account_id=account_id)


browser_automation_service_instance = get_browser_automation_service()


async def execute_actions_background(
    service_id: str,
    request_id: str,
    actions: list
):
    """Background task to execute browser actions"""
    try:
        # Get the service instance
        service = active_services.get(service_id)
        if not service:
            service = browser_automation_service_instance
            active_services[service_id] = service
            
        # Execute the actions
        result = await service.execute_actions(actions, request_id)
        
        # Store the result
        execution_results[request_id] = result
        
        # Update the database - Fix the update operation
        await mongo_handler.update_one(
            collection="command_executions",
            query={"request_id": request_id},
            update={
                "$set": {
                    "status": "completed" if result.success else "failed",
                    "completed_at": datetime.now(),
                    "success": result.success,
                    "message": result.message,
                    "error": result.error
                }
            }
        )
        
        # Store execution history
        await mongo_handler.insert_one(
            collection="execution_history",
            document={
                "request_id": request_id,
                "success": result.success,
                "completed_at": datetime.now()
            }
        )
        
    except Exception as e:
        logging.error(f"Error in background task: {str(e)}")
        # Update the database with the error - Fix the update operation
        await mongo_handler.update_one(
            collection="command_executions",
            query={"request_id": request_id},
            update={
                "$set": {
                    "status": "failed",
                    "completed_at": datetime.now(),
                    "success": False,
                    "message": "Error in background task",
                    "error": str(e)
                }
            }
        )


@GlitchAgent_Api_Router.post("/interact", response_model=CommandResponse)
async def interact(
    command: str,
    background_tasks: BackgroundTasks,
    context: Optional[str] = None,
):
    """
    Simplified endpoint that takes natural language input and processes it.
    This serves as the main entry point for the Interact API.
    
    Args:
        command: Natural language command to execute
        context: Optional context for the command
        
    Returns:
        CommandResponse with request_id and actions
    """
    try:
        # Create a CommandRequest object from the input
        request = CommandRequest(
            command=command,
            context=context
        )
        
        # Process the command using the existing endpoint logic
        return await process_command(request, background_tasks)
        
    except Exception as e:
        logging.error(f"Error in interact endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing command: {str(e)}")


@GlitchAgent_Api_Router.post("/command", response_model=CommandResponse)
async def process_command(
    request: CommandRequest,
    background_tasks: BackgroundTasks,
):
    """Process a natural language command and translate it into browser actions"""
    try:
        # Generate a service ID
        service_id = str(uuid.uuid4())
        
        # Translate the command to actions
        response = await browser_automation_service_instance.translate_command(request)

        logging.info(f"Command translated to actions: {response.actions}")
        # Check if actions are empty
        if not response.actions:
            raise HTTPException(status_code=400, detail="No actions generated from command")
        
        # Store the command in the database
        await mongo_handler.insert_one(
            collection="command_executions",
            document={
                "request_id": response.request_id,
                "command": request.command,
                "status": "pending",
                "created_at": datetime.now()
            }
        )
        
        # Add a background task to execute the actions
        background_tasks.add_task(
            execute_actions_background,
            service_id,
            response.request_id,
            response.actions
        )
        
        return response
    
    except Exception as e:
        logging.error(f"Error processing command: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing command: {str(e)}")


@GlitchAgent_Api_Router.get("/execution/{request_id}", response_model=ExecutionResult)
async def get_execution_result(request_id: str):
    """Get the result of a command execution"""
    try:
        # Check if the result is in memory
        result = execution_results.get(request_id)
        if result:
            return result
        
        # If not in memory, check the database
        execution_doc = await mongo_handler.find_one(
            collection="command_executions",
            query={"request_id": request_id}
        )
        
        if not execution_doc:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # If the execution is still pending, return a status update
        if execution_doc.get("status") == "pending":
            return ExecutionResult(
                request_id=request_id,
                success=False,
                message="Execution is still in progress",
                completed_at=datetime.now()
            )
        
        # If the execution is completed or failed, return the result
        return ExecutionResult(
            request_id=request_id,
            success=execution_doc.get("success", False),
            message=execution_doc.get("message", ""),
            error=execution_doc.get("error"),
            completed_at=execution_doc.get("completed_at", datetime.now())
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        logging.error(f"Error retrieving execution result: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving execution result: {str(e)}")


@GlitchAgent_Api_Router.get("/history", response_model=List[ExecutionHistory])
async def get_execution_history(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return")
):
    """Get history of command executions"""
    try:
        # Query MongoDB for history items
        cursor = await mongo_handler.find_many(
            collection="execution_history",
            query={},
            skip=skip,
            limit=limit,
            sort=[("created_at", -1)]  # Sort by created_at in descending order
        )
        
        # Convert cursor to list
        history_items = await cursor.to_list(length=limit)
        
        return history_items
    
    except Exception as e:
        logging.error(f"Error retrieving execution history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@GlitchAgent_Api_Router.post("/stop-browser")
async def stop_browser():
    """Stop all browser instances"""
    try:
        for service_id, service in active_services.items():
            await service.stop_browser()
        
        # Clear the active services
        active_services.clear()
        
        return {"message": "All browser instances stopped"}
    
    except Exception as e:
        logging.error(f"Error stopping browsers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error stopping browsers: {str(e)}")
