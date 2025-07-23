from dataclasses import dataclass


@dataclass(frozen=True)
class TextVerifiedError(Exception):
    """Server-side API Errors."""

    error_code: str
    error_description: str
    context: str = ""

    def __str__(self):
        return f"{self.error_code} - {self.error_description}\n" f"{self.context}"
