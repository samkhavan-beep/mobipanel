import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import Base, engine
from .routers import auth_router, clients_router, inbounds_router, dashboard_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="VPN Panel")

app.include_router(auth_router.router)
app.include_router(clients_router.router)
app.include_router(inbounds_router.router)
app.include_router(dashboard_router.router)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
