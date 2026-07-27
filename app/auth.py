from fastapi import Header, HTTPException, Request
from app import db

def get_current_user(request: Request, x_user_id: int = Header(...)):
    user = db.row(
        request.app.state.sf,
        f"select id, name, role from users where id = {x_user_id}",
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid X-User-Id")

    return user

def is_staff(user: dict) -> bool:
    return user["role"] in {"provider", "admin"}