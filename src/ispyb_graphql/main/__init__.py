from __future__ import annotations

import functools
import typing

from cas import CASClient as _CASClient
from fastapi import Depends, FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from strawberry.fastapi import GraphQLRouter

from ispyb_graphql.api.schema import schema

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="!secret")


CASClient = functools.partial(
    _CASClient, version=3, server_url="https://auth.diamond.ac.uk/cas/"
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
    if not next:
        next = "profile"
    cas_client = CASClient(service_url=request.url_for("login") + f"?next={next}")
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
    request.session.pop("user", None)
    cas_client = CASClient(service_url=request.url_for("logout"))
    cas_logout_url = cas_client.get_logout_url(redirect_url)
    print("CAS logout URL: %s", cas_logout_url)
    return RedirectResponse(cas_logout_url)


@app.get("/logout_callback")
def logout_callback(request: Request):
    print("deleting user from session")
    request.session.pop("user", None)
    return HTMLResponse('Logged out from CAS. <a href="/login">Login</a>')


graphql_app = GraphQLRouter(
    schema,
)


class RequiresLoginException(Exception):
    def __init__(self, next: typing.Optional[str] = None):
        self.next = next


@app.exception_handler(RequiresLoginException)
async def exception_handler(request: Request, exc: RequiresLoginException) -> Response:
    redirect_url = request.url_for("login") + f"?next={exc.next}"
    return RedirectResponse(redirect_url)


async def get_current_user(request: Request):
    user = request.session.get("user", None)
    print(f"{user=}")
    if not user:
        raise RequiresLoginException(next="graphql")
    return user["user"]


app.include_router(
    graphql_app,
    prefix="/graphql",
    dependencies=[Depends(get_current_user)],
)
