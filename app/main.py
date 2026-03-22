from fastapi import FastAPI
from app.controllers import session_controller

app = FastAPI(title="PTA Simulator Backend")

app.include_router(session_controller.router, prefix="/sessions")

@app.get("/")
def start():
    return {"id": "112"}