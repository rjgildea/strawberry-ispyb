from __future__ import annotations

import asyncio
from typing import Optional

import strawberry
from strawberry.arguments import UNSET

from ispyb_graphql import crud, models

from .data_collection import DataCollection, ScanType
from .pagination import Connection, Edge, PageInfo
from .sample import Sample


@strawberry.type
class Proposal:
    proposal_id: int
    name: str

    @strawberry.field
    async def data_collections(
        self,
        info,
        scan_type: ScanType = None,
        first: int = 10,
        after: Optional[strawberry.ID] = UNSET,
    ) -> Connection[DataCollection]:

        after = after if after is not UNSET else None
        db = info.context["db"]
        dcids = await crud.get_dcids_for_proposal(
            db,
            self.proposal_id,
            scan_type=scan_type.value if scan_type else None,
            after=after,
            limit=first + 1,
        )
        data_collections = await asyncio.gather(
            *(info.context["data_collections_loader"].load(dcid) for dcid in dcids)
        )

        edges = [Edge(node=dc, cursor=dc.dcid) for dc in data_collections]
        return Connection(
            page_info=PageInfo(
                has_previous_page=False,
                has_next_page=len(data_collections) > first,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-2].cursor if len(edges) > 1 else None,
            ),
            edges=edges[
                :-1
            ],  # exclude last one as it was fetched to know if there is a next page
        )

    @strawberry.field
    async def samples(self, info) -> list[Sample]:
        db = info.context["db"]
        samples = await crud.get_samples_for_proposal(db, self.proposal_id)
        return [Sample.from_instance(sample) for sample in samples]

    @classmethod
    def from_instance(cls, instance: models.Proposal):
        return cls(
            proposal_id=instance.proposalId,
            name=f"{instance.proposalCode}{instance.proposalNumber}",
        )
