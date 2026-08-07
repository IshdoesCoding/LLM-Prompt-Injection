
from abc import ABC, abstractmethod

class BaseProvider(ABC):
   

    @abstractmethod
    def send(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a prompt to the provider and return the response.

        Args:
            system_prompt (str): The system prompt to set the context for the model.
            user_prompt (str): The user prompt to send to the model."""
        