from dotenv import load_dotenv
import os
from fastapi import FastAPI

load_dotenv()
from .routers import tests

app = FastAPI()

app.include_router(tests.router)
