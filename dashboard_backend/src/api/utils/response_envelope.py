from typing import Any, Optional, Dict
from pydantic import BaseModel, Field

# PUBLIC_INTERFACE
class APIResponseEnvelope(BaseModel):
    """Standard API success response envelope."""
    success: bool = Field(..., description="True if request succeeded")
    data: Optional[Any] = Field(None, description="Response payload data")
    message: Optional[str] = Field(None, description="Summary or explanation message")

# PUBLIC_INTERFACE
class APIErrorEnvelope(BaseModel):
    """Standard API error response envelope."""
    success: bool = Field(default=False, description="False for any error response")
    error: Dict[str, Any] = Field(..., description="Error object with required code/message fields")
    data: Optional[Any] = Field(default=None, description="Optional partial data for validation errors etc.")

def api_response(data: Any = None, message: str = None):
    """Convenience: return APIResponseEnvelope as dict."""
    return APIResponseEnvelope(success=True, data=data, message=message).model_dump()

def api_error(code: str, message: str, status_code: int = 400, data: Any = None):
    """Convenience: produce response envelope for API errors."""
    env = APIErrorEnvelope(
        success=False, 
        error={"code": code, "message": message},
        data=data,
    )
    return env.model_dump(), status_code
