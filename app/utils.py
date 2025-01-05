from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any


def success_response(status_code: int, message: str, data: Any):
    if isinstance(data, BaseModel):
        data = data.model_dump()
    elif isinstance(data, list) and all(isinstance(item, BaseModel) for item in data):
        data = [item.model_dump() for item in data]
    encoded_data = jsonable_encoder({"message": message, "data": data})
    return JSONResponse(status_code=status_code, content=encoded_data)


def error_response(status_code, message):
    raise HTTPException(status_code=status_code, detail=message)
