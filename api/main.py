import sys
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.dependencies import get_settings
from api.routers.auth import auth
from api.routers.data import data
from api.services.endpoint_requester import EndpointRequester

settings = get_settings()


def initialise_logger():
    logger.remove()
    logger.add(sys.stdout, format="{time} {level} {message}", level="INFO")
    logger.add(sys.stderr, format="{time} {level} {message}", level="ERROR")


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialise_logger()

    client = httpx.AsyncClient()

    try:
        app.state.endpoint_requester = EndpointRequester(client)

        yield
    finally:
        await client.aclose()


app = FastAPI(lifespan=lifespan)


# healthcheck route
@app.get("/")
def health_check():
    return {"status": "running"}


app.include_router(auth.router)
app.include_router(data.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, e: Exception):
    """Handles all unhandled exceptions globally."""
    logger.error(f"Unhandled Exception occurred at {request.url} - {e}")

    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again later."},
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all incoming requests."""

    ip_addr = request.client.host
    port = request.client.port
    url = request.url
    req_method = request.method

    log_message = f"{ip_addr}:{port} made {req_method} request to {url}."

    logger.info(log_message)

    logger.info(f"Cookies: {request.cookies}")

    response = await call_next(request)

    set_cookie_headers = response.headers.getlist("set-cookie")
    logger.info(f"Set-Cookie Headers: {set_cookie_headers}")

    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
