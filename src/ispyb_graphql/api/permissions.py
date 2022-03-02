from __future__ import annotations

import typing

from fastapi import Request, WebSocket
from fastapi.responses import HTMLResponse
from strawberry.permission import BasePermission
from strawberry.types import Info

from ispyb_graphql import crud


class IsAuthenticatedForProposal(BasePermission):
    message = "User is not authenticated"

    async def has_permission(
        self, source: typing.Any, info: Info, *, name: str, **kwargs
    ) -> bool:
        request: typing.Union[Request, WebSocket] = info.context["request"]

        user = request.session.get("user")
        if not user:
            return HTMLResponse(
                'Login required. <a href="/login">Login</a>', status_code=403
            )

        db = info.context["db"]
        return await crud.proposal_has_person(db, name, user["user"])


class IsAuthenticatedForBeamline(BasePermission):
    message = "User is not authenticated"

    async def has_permission(
        self, source: typing.Any, info: Info, *, name: str, **kwargs
    ) -> bool:
        request: typing.Union[Request, WebSocket] = info.context["request"]

        user = request.session.get("user")
        if not user:
            return False

        db = info.context["db"]
        return await crud.user_is_admin_for_beamline(db, user["user"], name)


class IsAuthenticatedForVisit(BasePermission):
    message = "User is not authenticated"

    async def has_permission(
        self, source: typing.Any, info: Info, *, name: str, **kwargs
    ) -> bool:
        request: typing.Union[Request, WebSocket] = info.context["request"]

        user = request.session.get("user")
        print(f"{user=}")
        if not user:
            return False

        db = info.context["db"]
        blsession = await crud.get_blsession(db, name)
        is_admin = await crud.user_is_admin_for_beamline(
            db, user, blsession.beamLineName
        )
        return is_admin or await crud.session_has_person(db, name, user["user"])
