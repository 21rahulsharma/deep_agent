from pydantic import BaseModel, Field
from typing import Literal

class ChatRequestModel(BaseModel):
    """Request Model for Chat Endpoint"""
    session_id: str | None = Field(default=None, description="session ID for the chat, if None then a new session will be created")
    message: str = Field(..., description="User Message to be sent by the User to the Deep Agent")
    provider: Literal["gemini", "openai", "anthropic"] = Field(default="gemini", description="LLM Provider to be used for generating the response")

class SubAgentInfo(BaseModel):
    subagent_name: str
    subagent_tools: list[str] 
class ExecutionInfo(BaseModel):
    thread_id: str
    tools_called: list[str]
    sub_agents_called: list[SubAgentInfo]
class ResponseResult(BaseModel):
    response: str
class Results(BaseModel):
    info: ExecutionInfo
    result: ResponseResult
class ChatResponseModel(BaseModel):
    """Response Model for Chat Endpoint"""
    results: Results