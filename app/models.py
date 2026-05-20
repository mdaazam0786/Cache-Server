# Equivalent of UIBean.java and ResponseData.java

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class UIBean(BaseModel, Generic[T]):
    """
    Generic response envelope — wraps all API responses.
    Equivalent of UIBean<T> in Java.
    """
    data: Optional[T] = None
    success: bool = False
    message: Optional[str] = None
    response: Optional[str] = None


class ResponseData(BaseModel):
    """
    Equivalent of ResponseData.java — holds a bulk key/value map.
    """
    bulk_response: Optional[dict[str, str]] = None
