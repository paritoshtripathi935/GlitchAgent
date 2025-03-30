from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class ActionType(str, Enum):
    """Types of browser actions that can be performed"""
    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    WAIT = "wait"
    SUBMIT = "submit"
    PRESS = "press"
    SELECT = "select"
    HOVER = "hover"
    SCREENSHOT = "screenshot"
    EXTRACT = "extract"  # For future Level 2 implementation


class BrowserAction(BaseModel):
    """Model for a single browser action"""
    action: ActionType
    locator: Optional[str] = Field(None, description="CSS selector, XPath, or Playwright locator")
    url: Optional[str] = Field(None, description="URL for navigation")
    text: Optional[str] = Field(None, description="Text to fill in form fields")
    time_ms: Optional[int] = Field(None, description="Time to wait in milliseconds")
    key: Optional[str] = Field(None, description="Key to press")
    value: Optional[str] = Field(None, description="Value to select in dropdown")
    
    class Config:
        schema_extra = {
            "example": {
                "action": "click",
                "locator": "role:button[name='Sign in']"
            }
        }


class CommandRequest(BaseModel):
    """Request model for natural language command"""
    command: str = Field(..., description="Natural language command to execute")
    context: Optional[str] = Field(None, description="Additional context for the command")
    credentials: Optional[Dict[str, str]] = Field(None, description="Credentials for authentication")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options for execution")


class CommandResponse(BaseModel):
    """Response model for command execution"""
    request_id: str = Field(..., description="Unique identifier for the request")
    actions: List[BrowserAction] = Field(..., description="List of actions to execute")
    status: str = Field("pending", description="Status of the command execution")
    message: Optional[str] = Field(None, description="Additional information about the execution")
    created_at: datetime = Field(default_factory=datetime.now, description="When the command was received")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ExecutionResult(BaseModel):
    """Model for execution result"""
    request_id: str = Field(..., description="Unique identifier for the request")
    success: bool = Field(..., description="Whether the execution was successful")
    message: str = Field(..., description="Message about the execution")
    screenshot: Optional[str] = Field(None, description="Base64-encoded screenshot")
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="Data extracted from the page")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    completed_at: datetime = Field(default_factory=datetime.now, description="When the execution completed")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ExecutionHistory(BaseModel):
    """Model for execution history"""
    request_id: str = Field(..., description="Unique identifier for the request")
    command: str = Field(..., description="Original command")
    success: bool = Field(..., description="Whether the execution was successful")
    created_at: datetime = Field(default_factory=datetime.now, description="When the execution was created")
    completed_at: Optional[datetime] = Field(None, description="When the execution completed")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
