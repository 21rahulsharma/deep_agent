from uuid import uuid4 
from typing import Annotated
from fastapi import APIRouter, Depends
from src.agent.agent_setup import ChatRequestContext, get_chat_request_context
from src.models import ChatResponseModel
from src.utils import (
    message_content_to_text,
    print_execution_trace,
    save_markdown_response,
)

router = APIRouter(prefix="/api/v1",tags=["v1"])

@router.post("/chat", response_model=ChatResponseModel)
async def chat(
    context: Annotated[ChatRequestContext, Depends(get_chat_request_context)],
):
    request = context.request
    agent_setup = context.agent_setup
    thread_id = request.session_id or str(uuid4())
    result = await agent_setup.agent.ainvoke(
            {"messages": [{"role": "user", "content": request.message}]},
             config = {
                "configurable":{
                    "thread_id": thread_id,
                    "max_tokens": 2000,
                    "temperature": 1.0
                }
             }
        )
    response = message_content_to_text(result["messages"][-1].content)
    info = print_execution_trace(
        result,thread_id, agent_setup.subagent_names, agent_setup.subagent_tools
    )
    save_markdown_response(response)
    return ChatResponseModel.model_validate(
        {
            "results": {
                "info": info,
                "result": {"response": response},
            }
        }
    )
