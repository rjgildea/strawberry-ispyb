# from __future__ import annotations

from typing import List

import strawberry
from sqlalchemy.orm import Session

from ispyb_graphql import crud

from .auto_processing import AutoProcessingResult, MergingStatistics
from .beamline import Beamline
from .container import Container
from .data_collection import DataCollection
from .proposal import Proposal
from .sample import Sample
from .visit import Visit

__all__ = [
    "AutoProcessingResult",
    "Beamline",
    "Container",
    "DataCollection",
    "MergingStatistics",
    "Proposal",
    "Sample",
    "Visit",
]


async def load_auto_processings(
    db: Session, dcids: List[strawberry.ID]
) -> List[List[AutoProcessingResult]]:
    result = await crud.get_auto_processing_results_for_dcids(db, dcids)
    return [
        [AutoProcessingResult.from_instance(ap) for ap in auto_processings]
        for auto_processings in result
    ]


async def load_merging_statistics(
    db: Session, auto_proc_ids: List[strawberry.ID]
) -> List[List[MergingStatistics]]:
    result = await crud.get_auto_proc_scaling_statistics_for_apids(db, auto_proc_ids)
    return [
        [MergingStatistics.from_instance(shell_stats) for shell_stats in statistics]
        for statistics in result
    ]


async def load_containers(
    db: Session, container_ids: List[strawberry.ID]
) -> List[List[Container]]:
    containers = await crud.get_containers(db, container_ids)
    return [Container.from_instance(container) for container in containers]


async def load_samples(
    db: Session, sample_ids: List[strawberry.ID]
) -> List[List[Sample]]:
    samples = await crud.get_samples(db, sample_ids)
    return [Sample.from_instance(sample) for sample in samples]


async def load_data_collections(
    db: Session, dcids: List[strawberry.ID]
) -> List[List[DataCollection]]:
    data_collections = await crud.get_data_collections(db, dcids)
    return [DataCollection.from_instance(dc) for dc in data_collections]
