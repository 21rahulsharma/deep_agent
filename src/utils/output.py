from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4
from src.logger import get_logger
_OUTPUT_DIRECTORY = Path(__file__).parents[2]/"output"

logger = get_logger(__name__)


def message_content_to_text(content: object) -> str:
    """Extract plain text from a model message's text or content-block value."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict) and isinstance(block.get("text"), str):
                text_parts.append(block["text"])
        if text_parts:
            return "\n".join(text_parts)
    raise ValueError("Model response did not contain any text content")


def save_markdown_response(response:str)-> Path:
    try: 
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        output_path = _OUTPUT_DIRECTORY/f"response_{timestamp}_{uuid4().hex[:8]}.md"
        output_path.write_text(response, encoding="utf-8")
        logger.info("Saved final response to %s", output_path)
        return output_path
    except Exception as e: 
        logger.info("Unable to save markdown response")
    