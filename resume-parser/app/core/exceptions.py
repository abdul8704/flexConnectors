"""Application exception types and error codes."""

from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        self.code = code
        self.message = message
        super().__init__(status_code=status_code, detail=message)

