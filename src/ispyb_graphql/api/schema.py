from __future__ import annotations

import typing

import strawberry
from fastapi import Request, WebSocket
from fastapi.responses import HTMLResponse
from main import models
from strawberry.permission import BasePermission
from strawberry.types import Info

from .definitions import Beamline, Proposal, Visit


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source: typing.Any, info: Info, **kwargs) -> bool:
        request: typing.Union[Request, WebSocket] = info.context["request"]

        print(f"{source=}")
        print(f"{kwargs}")
        proposal = kwargs.get("name")
        user = request.session.get("user")
        if not user:
            return HTMLResponse(
                'Login required. <a href="/login">Login</a>', status_code=403
            )

        # if user["user"] == "foo":
        #     return True

        db = info.context["db"]
        return models.proposal_has_person(db, proposal, user["user"])


@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def proposal(
        self,
        info,
        name: strawberry.ID,
    ) -> Proposal:
        db = info.context["db"]
        proposal = await models.get_proposal(db, name=name)
        return Proposal.from_instance(proposal)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def visit(
        self,
        info,
        name: strawberry.ID,
    ) -> Visit:
        db = info.context["db"]
        session = await models.get_blsession(db, name=name)
        return Visit.from_instance(session)

    @strawberry.field
    async def beamline(
        self,
        info,
        name: strawberry.ID,
    ) -> Beamline:
        return Beamline(name=name)


schema = strawberry.Schema(Query)
