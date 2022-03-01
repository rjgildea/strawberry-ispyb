from __future__ import annotations

import datetime
from typing import Optional

import strawberry
from strawberry.arguments import UNSET

from ispyb_graphql import crud

from .data_collection import DataCollection, ScanType
from .pagination import Connection, Edge, PageInfo
from .visit import Visit


@strawberry.type
class Beamline:
    name: str

    @strawberry.field
    async def visits(
        self,
        info,
        start_time: datetime.datetime = None,
        end_time: datetime.datetime = datetime.datetime.now(),
    ) -> list[Visit]:
        db = info.context["db"]
        blsessions = await crud.get_blsessions_for_beamline(
            db, self.name, start_time=start_time, end_time=end_time
        )
        return [Visit.from_instance(blsession) for blsession in blsessions]

    @strawberry.field
    async def data_collections(
        self,
        info,
        start_time: datetime.datetime = None,
        end_time: datetime.datetime = datetime.datetime.now(),
        scan_type: ScanType = None,
        first: int = 10,
        after: Optional[strawberry.ID] = UNSET,
    ) -> Connection[DataCollection]:

        after = after if after is not UNSET else None
        db = info.context["db"]
        data_collections = await crud.get_data_collections_for_beamline(
            db,
            self.name,
            start_time=start_time,
            end_time=end_time,
            scan_type=scan_type.value if scan_type else None,
            after=after,
            limit=first + 1,
        )
        edges = [
            Edge(node=DataCollection.from_instance(dc), cursor=dc.dataCollectionId)
            for dc in data_collections
        ]
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
