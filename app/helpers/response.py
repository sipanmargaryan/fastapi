from fastapi import status
from fastapi.responses import JSONResponse


class Response(JSONResponse):
    def __init__(
        self,
        payload=None,
        message=None,
        debug_message=None,
        status_code=status.HTTP_200_OK,
        **kwargs
    ):
        payload = payload or {}
        if kwargs.get("data") is not None:
            payload["data"] = kwargs.get("data")
        if message:
            payload["message"] = message
        if debug_message:
            payload["debug_message"] = debug_message
        if "code" in kwargs:
            payload["code"] = kwargs.get("code")
        if "meta_data" in kwargs:
            if not isinstance(kwargs.get("meta_data"), dict):
                raise ValueError("meta_data is not a dict object")
            payload["metaData"] = kwargs.get("meta_data")
        super().__init__(content=payload, status_code=status_code)
