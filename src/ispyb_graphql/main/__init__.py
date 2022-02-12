from __future__ import annotations

import functools
import typing

from api import definitions
from api.schema import schema
from cas import CASClient
from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from strawberry.dataloader import DataLoader
from strawberry.fastapi import GraphQLRouter

from .database import SessionLocal

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="!secret")


cas_client = CASClient(
    version=3,
    service_url="http://127.0.0.1:8000/login?next=%2Fprofile",
    server_url="http://localhost:8080/cas/",
    # server_url='https://auth.diamond.ac.uk/cas/'
)


@app.get("/")
async def index(request: Request):
    return RedirectResponse(request.url_for("login"))


@app.get("/profile")
async def profile(request: Request):
    user = request.session.get("user")
    if user:
        return HTMLResponse(
            'Logged in as %s. <a href="/logout">Logout</a>' % user["user"]
        )
    return HTMLResponse('Login required. <a href="/login">Login</a>', status_code=403)


@app.get("/login")
def login(
    request: Request,
    next: typing.Optional[str] = None,
    ticket: typing.Optional[str] = None,
):
    if request.session.get("user", None):
        # Already logged in
        return RedirectResponse(request.url_for("profile"))

    if not ticket:
        # No ticket, the request come from end user, send to CAS login
        cas_login_url = cas_client.get_login_url()
        print("CAS login URL: %s", cas_login_url)
        return RedirectResponse(cas_login_url)

    # There is a ticket, the request come from CAS as callback.
    # need call `verify_ticket()` to validate ticket and get user profile.
    user, attributes, pgtiou = cas_client.verify_ticket(ticket)

    print(
        "CAS verify ticket response: user: %s, attributes: %s, pgtiou: %s",
        user,
        attributes,
        pgtiou,
    )

    if not user:
        return HTMLResponse('Failed to verify ticket. <a href="/login">Login</a>')
    else:  # Login successfully, redirect according `next` query parameter.
        response = RedirectResponse(next)
        request.session["user"] = dict(user=user)
        return response


@app.get("/logout")
def logout(request: Request):
    redirect_url = request.url_for("logout_callback")
    cas_logout_url = cas_client.get_logout_url(redirect_url)
    print("CAS logout URL: %s", cas_logout_url)
    return RedirectResponse(cas_logout_url)


@app.get("/logout_callback")
def logout_callback(request: Request):
    # redirect from CAS logout request after CAS logout successfully
    # response.delete_cookie('username')
    request.session.pop("user", None)
    return HTMLResponse('Logged out from CAS. <a href="/login">Login</a>')


async def get_session():
    async with SessionLocal() as session:
        yield session


async def get_context(db=Depends(get_session)):
    return {
        "db": db,
        "auto_processing_loader": DataLoader(
            functools.partial(
                definitions.load_auto_processings,
                db,
            )
        ),
        "data_collections_loader": DataLoader(
            functools.partial(
                definitions.load_data_collections,
                db,
            )
        ),
        "sample_loader": DataLoader(
            functools.partial(
                definitions.load_samples,
                db,
            )
        ),
    }


graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
)


app.include_router(
    graphql_app,
    prefix="/graphql",
)
