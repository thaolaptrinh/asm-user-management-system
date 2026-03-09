from fastapi import HTTPException, status


class AppException(HTTPException):
    pass


class NotFoundError(AppException):
    def __init__(self, resource: str, id: object | None = None) -> None:
        detail = (
            f"{resource} not found" if id is None else f"{resource} {id!r} not found"
        )
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(AppException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Could not validate credentials") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
