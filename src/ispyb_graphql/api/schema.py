from __future__ import annotations

import functools
import typing

import strawberry
from fastapi import Request, WebSocket
from fastapi.responses import HTMLResponse
from strawberry.dataloader import DataLoader
from strawberry.extensions import Extension
from strawberry.permission import BasePermission
from strawberry.types import Info

from ispyb_graphql import crud
from ispyb_graphql.api.definitions import (
    Beamline,
    DataCollection,
    Proposal,
    Sample,
    Visit,
    load_auto_processings,
    load_data_collections,
    load_merging_statistics,
    load_samples,
)
from ispyb_graphql.database import get_db_session


class IsAuthenticated(BasePermission):
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

        # if user["user"] == "foo":
        #     return True

        db = info.context["db"]
        return await crud.proposal_has_person(db, name, user["user"])


@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def proposal(
        self,
        info,
        name: strawberry.ID,
    ) -> Proposal:
        db = info.context["db"]
        proposal = await crud.get_proposal(db, name=name)
        return Proposal.from_instance(proposal)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def visit(
        self,
        info,
        name: strawberry.ID,
    ) -> Visit:
        db = info.context["db"]
        session = await crud.get_blsession(db, name=name)
        return Visit.from_instance(session)

    @strawberry.field
    async def beamline(
        self,
        info,
        name: strawberry.ID,
    ) -> Beamline:
        return Beamline(name=name)

    @strawberry.field
    async def data_collection(
        self,
        info,
        dcid: strawberry.ID,
    ) -> DataCollection:
        return await info.context["data_collections_loader"].load(dcid)

    @strawberry.field
    async def sample(
        self,
        info,
        sample_id: strawberry.ID,
    ) -> Sample:
        return await info.context["sample_loader"].load(sample_id)


class ISPyBGraphQLExtension(Extension):
    async def on_request_start(self):
        db = await get_db_session()
        if self.execution_context.context is None:
            self.execution_context.context = {}
        self.execution_context.context.update(
            {
                "db": db,
                "auto_processing_loader": DataLoader(
                    functools.partial(
                        load_auto_processings,
                        db,
                    )
                ),
                "data_collections_loader": DataLoader(
                    functools.partial(
                        load_data_collections,
                        db,
                    )
                ),
                "merging_statistics_loader": DataLoader(
                    functools.partial(
                        load_merging_statistics,
                        db,
                    )
                ),
                "sample_loader": DataLoader(
                    functools.partial(
                        load_samples,
                        db,
                    )
                ),
            }
        )

    async def on_request_end(self):
        await self.execution_context.context["db"].close()


schema = strawberry.Schema(Query, extensions=[ISPyBGraphQLExtension])
