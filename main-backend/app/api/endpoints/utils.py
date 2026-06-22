from fastapi.responses import JSONResponse

def _ok(data: dict | list) -> JSONResponse:
    return JSONResponse(content={"code": 0, "message": "success", "data": data})
