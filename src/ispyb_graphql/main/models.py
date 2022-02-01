from __future__ import annotations

import itertools
import logging
import operator
import re

from ispyb.sqlalchemy import (
    AutoProc,
    AutoProcIntegration,
    AutoProcProgram,
    BLSample,
    BLSession,
    Container,
    Crystal,
    DataCollection,
    Proposal,
    Protein,
)
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)

re_proposal = re.compile(r"([a-z][a-z])([0-9]+)")


def proposal_code_and_number_from_name(name: str) -> tuple[str, int]:
    m = re_proposal.match(name)
    assert m
    code, number = m.groups()
    return code, int(number)


async def get_proposal(db: Session, name: str) -> Proposal:
    print(f"Getting proposal {name}")
    code, number = proposal_code_and_number_from_name(name)
    stmt = (
        select(Proposal)
        .filter(Proposal.proposalCode == code)
        .filter(Proposal.proposalNumber == number)
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_data_collections_for_proposal(
    db: Session, proposal_id: int
) -> list[DataCollection]:
    print(f"Getting data collections for {proposal_id=}")
    stmt = (
        select(DataCollection)
        .join(BLSession, DataCollection.SESSIONID == BLSession.sessionId)
        .filter(BLSession.proposalId == proposal_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_sample(db: Session, sample_id: int) -> BLSample:
    print(f"Getting {sample_id=}")
    stmt = select(BLSample).filter(BLSample.blSampleId == sample_id)
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_samples(db: Session, sample_ids: list[int]) -> list[BLSample]:
    print(f"Getting {sample_ids=}")
    stmt = select(BLSample).filter(BLSample.blSampleId.in_(sample_ids))
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_data_collections_for_samples(
    db: Session, sample_ids: list[int]
) -> list[list[DataCollection]]:
    print(f"Getting data collections for {sample_ids=}")
    stmt = (
        select(DataCollection)
        .join(BLSample, DataCollection.BLSAMPLEID == BLSample.blSampleId)
        .filter(BLSample.blSampleId.in_(sample_ids))
    )
    results = await db.execute(stmt)
    grouped = {
        k: list(g)
        for k, g in itertools.groupby(results.scalars().all(), lambda g: g.BLSAMPLEID)
    }
    return [[dc for dc in grouped[sid]] if sid in grouped else [] for sid in sample_ids]


async def get_samples_for_proposal(db: Session, proposal_id: int) -> list[BLSample]:
    print(f"Getting samples for {proposal_id=}")
    stmt = (
        select(BLSample)
        .join(Crystal, Crystal.crystalId == BLSample.crystalId)
        .join(Protein, Protein.proteinId == Crystal.proteinId)
        .join(Container, Container.containerId == BLSample.containerId)
        .join(Proposal, Proposal.proposalId == Protein.proposalId)
        .filter(Proposal.proposalId == proposal_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_auto_procs_for_data_collections(
    db: Session, dcids: list[dcid]
) -> list[list[AutoProcIntegration]]:
    print(f"Getting autoprocessings for dcids: {dcids}")
    stmt = (
        select(DataCollection.dataCollectionId, AutoProc)
        .join(
            AutoProcProgram,
            AutoProcProgram.autoProcProgramId == AutoProc.autoProcProgramId,
        )
        .join(
            AutoProcIntegration,
            AutoProcIntegration.autoProcProgramId == AutoProcProgram.autoProcProgramId,
        )
        .join(
            DataCollection,
            DataCollection.dataCollectionId == AutoProcIntegration.dataCollectionId,
        )
        .filter(DataCollection.dataCollectionId.in_(dcids))
    )
    results = await db.execute(stmt)
    grouped = {
        k: list(g)
        for k, g in itertools.groupby(results.all(), lambda g: g.dataCollectionId)
    }
    return [
        [result.AutoProc for result in grouped[dcid]] if dcid in grouped else []
        for dcid in dcids
    ]
