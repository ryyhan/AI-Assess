from fastapi import FastAPI
from .routers import tests

app = FastAPI()

app.include_router(tests.router)

