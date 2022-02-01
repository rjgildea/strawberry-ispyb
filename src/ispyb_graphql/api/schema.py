from typing import List

import strawberry
from main import models
from main.database import SessionLocal

from .definitions import DataCollection, Proposal, Sample


@strawberry.type
class Query:
    @strawberry.field
    async def proposal(self, info, name: strawberry.ID) -> Proposal:
        db = info.context["db"]
        proposal = await models.get_proposal(db, name=name)
        return Proposal.from_instance(proposal)


schema = strawberry.Schema(Query)
