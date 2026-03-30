def ok(data=None, message: str = "") -> dict:
    return {"success": True, "data": data or {}, "message": message}
