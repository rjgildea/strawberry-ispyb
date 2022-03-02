from __future__ import annotations

import functools

import strawberry
from strawberry.dataloader import DataLoader
from strawberry.extensions import Extension

from ispyb_graphql import crud
from ispyb_graphql.database import get_db_session

from .definitions import (
    Beamline,
    DataCollection,
    Proposal,
    Sample,
    Visit,
    load_auto_processings,
    load_containers,
    load_data_collections,
    load_merging_statistics,
    load_samples,
)
from .permissions import (
    IsAuthenticatedForBeamline,
    IsAuthenticatedForProposal,
    IsAuthenticatedForVisit,
)


@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAuthenticatedForProposal])
    async def proposal(
        self,
        info,
        name: strawberry.ID,
    ) -> Proposal:
        db = info.context["db"]
        proposal = await crud.get_proposal(db, name=name)
        return Proposal.from_instance(proposal)

    @strawberry.field(permission_classes=[IsAuthenticatedForVisit])
    async def visit(
        self,
        info,
        name: strawberry.ID,
    ) -> Visit:
        db = info.context["db"]
        session = await crud.get_blsession(db, name=name)
        return Visit.from_instance(session)

    @strawberry.field(permission_classes=[IsAuthenticatedForBeamline])
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
                "container_loader": DataLoader(
                    functools.partial(
                        load_containers,
                        db,
                    )
                ),
            }
        )

    async def on_request_end(self):
        await self.execution_context.context["db"].close()


schema = strawberry.Schema(Query, extensions=[ISPyBGraphQLExtension])
