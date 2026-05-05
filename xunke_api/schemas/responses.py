from typing import Any, Optional

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


class SessionRegisterRequest(BaseModel):
    account_id: str = Field(..., min_length=1)
    cdp_url: str = Field(..., min_length=1)


class SessionStatus(BaseModel):
    account_id: str
    connected: bool
    cookie_valid: bool
    request_count: int
    cooldown_until: Optional[float] = None

