from __future__ import annotations

from typing import Any, Optional


class PawPaymentsApiError(Exception):
    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN",
        http_status: Optional[int] = None,
        details: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.details = details

    def __repr__(self) -> str:
        return (
            f"PawPaymentsApiError(code={self.code!r}, http_status={self.http_status!r}, "
            f"message={str(self)!r})"
        )
