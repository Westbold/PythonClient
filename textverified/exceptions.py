from dataclasses import dataclass


@dataclass(frozen=True)
class TextVerifiedError(Exception):
    """Server-side API Errors."""

    error_code: str
    error_description: str
    context: str = ""

    def __str__(self):
        return (
            f"{__package__}.{self.__class__.__name__}: {self.error_code}\n"
            f"{self.error_description}\n"
            f"{self.context}"
        )
