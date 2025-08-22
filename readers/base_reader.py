from abc import ABC, abstractmethod

class BaseReader(ABC):
    @abstractmethod
    def read(self, url: str) -> str | dict:
        """
        Reads the content from a given URL.

        Args:
            url: The URL to read from.

        Returns:
            The content of the URL as a string, or a dictionary for complex content.
        """
        pass
