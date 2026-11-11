from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from wapang.api import api_router
from wapang.common.source_hash import get_source_hash
from wapang.common.exceptions import (
    WapangException,
    MissingRequiredFieldException,
    InvalidFormatException,
)

app = FastAPI()

app.include_router(api_router, prefix="/api")


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "hash": get_source_hash()}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if any(error["type"] == "missing" for error in exc.errors()):
        error = MissingRequiredFieldException()
    else:
        error = InvalidFormatException()
    return await wapang_exception_handler(request, error)

@app.exception_handler(WapangException)
async def wapang_exception_handler(request: Request, exc: WapangException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "error_msg": exc.error_msg
        }
    )