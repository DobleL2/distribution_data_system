# Este archivo principal inicia la aplicación FastAPI y carga las rutas

from fastapi import FastAPI
from app.routers import user

app = FastAPI(title="Sistema de distribucion de informacion", version="0.0.1")

# Include the user router
app.include_router(user.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to my FastAPI application!"}
