from typing import List

import strawberry
from strawberry.extensions import Extension

from main import models
from main.database import SessionLocal

from .definitions import DataCollection, Proposal, Sample


class SQLAlchemySession(Extension):
    # def on_request_start(self):
    #     self.execution_context.context["db"] = SessionLocal()

    def on_request_end(self):
        self.execution_context.context["db"].close()


@strawberry.type
class Query:
    @strawberry.field
    async def proposal(self, info, name: strawberry.ID) -> Proposal:
        db = info.context["db"]
        proposal = await models.get_proposal(db, name=name)
        return Proposal.from_instance(proposal)


schema = strawberry.Schema(Query, extensions=[SQLAlchemySession])
