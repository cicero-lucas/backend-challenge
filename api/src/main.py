from fastapi import FastAPI
from .routers import roles, users

app = FastAPI(title="Shipay API", version="1.0.0")

app.include_router(roles.router)
app.include_router(users.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
