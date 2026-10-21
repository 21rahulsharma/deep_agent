import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from src.config import settings 


# Ensure GEMINI_API_KEY is set in your environment


# 1. Initialize Gemini LLM via LangChain
async def initialize_gemini_client():
    gemini_client = ChatGoogleGenerativeAI(
        model=settings.gemini_model_name,
        google_api_key=settings.gemini_api_key,
        temperature=0,
    )
    return gemini_client
