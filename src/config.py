from pydantic import Field
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration with field-level validation."""

    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    ddg_html_url: str = Field(
        "https://html.duckduckgo.com/html/", description="DuckDuckGo search URL"
    )
    gemini_api_key: Optional[str] = Field(None, description="Gemini API key")
    enable_gemini: bool = Field(True, description="Enable Gemini LLM client")
    gemini_model_name: str = Field(
        "gemini-3.1-flash-lite",
        description="Gemini model name",
    )
    max_sub_questions: int = Field(
        5, description="Maximum number of sub-questions to generate"
    )
    sources_per_question: int = Field(
        3, description="Number of sources to retrieve per sub-question"
    )

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()