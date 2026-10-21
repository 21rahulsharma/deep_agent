from src.config import settings
from .gemini_client import initialize_gemini_client
from src.logger import get_logger

logger = get_logger(__name__)

class LLMClientRegistry:
    """
    A registry for managing LLM clients.
    """

    def __init__(self):
        self._clients = {}

    def register_client(self, name: str, client):
        """
        Register a new LLM client.

        :param name: The name of the client.
        :param client: The client instance.
        """
        self._clients[name] = client

    def get_client(self, name: str):
        """
        Retrieve a registered LLM client by name.

        :param name: The name of the client.
        :return: The client instance if found, else None.
        """
        provider = name.split("/")[0]
        if provider.lower() in self._clients:
            return self._clients.get(name)
        return self._clients.get("gemini") # Default LLM Client
    async def register_llm_clients(self):
        """
        Register all the LLM Clients
        """
        if settings.enable_gemini:
            gemini_client = await initialize_gemini_client()
            self.register_client("gemini", gemini_client)
            logger.info("Gemini client initialized successfully")

    async def close_all_clients(self):
        """
        Close all registered LLM clients.
        """
        for client in self._clients.values():
            await client.aclose()