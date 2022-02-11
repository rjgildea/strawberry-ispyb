from __future__ import annotations

import datetime
import enum
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
    GridInfo,
    Person,
    Proposal,
    ProposalHasPerson,
    Protein,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, load_only

logger = logging.getLogger(__name__)

re_proposal = re.compile(r"([a-z][a-z])([0-9]+)")
re_visit = re.compile(r"([a-z][a-z])([0-9]+)-([0-9]+)")


DATA_COLLECTION_COLUMNS = (
    DataCollection.dataCollectionId,
    DataCollection.imageDirectory,
    DataCollection.fileTemplate,
    DataCollection.BLSAMPLEID,
    DataCollection.SESSIONID,
    DataCollection.startTime,
    DataCollection.endTime,
    DataCollection.axisStart,
    DataCollection.axisEnd,
    DataCollection.axisRange,
    DataCollection.overlap,
    DataCollection.numberOfImages,
    DataCollection.startImageNumber,
    DataCollection.exposureTime,
    DataCollection.rotationAxis,
    DataCollection.phiStart,
    DataCollection.kappaStart,
    DataCollection.omegaStart,
    DataCollection.chiStart,
)


def proposal_code_and_number_from_name(name: str) -> tuple[str, int]:
    m = re_proposal.match(name)
    assert m
    code, number = m.groups()
    return code, int(number)


def proposal_code_number_and_visit_number_from_name(name: str) -> tuple[str, int]:
    m = re_visit.match(name)
    assert m
    code, number, visit_number = m.groups()
    return code, int(number), int(visit_number)


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


async def get_blsession(db: Session, name: str) -> BLSession:
    print(f"Getting blsession {name}")
    code, number, visit_number = proposal_code_number_and_visit_number_from_name(name)
    stmt = (
        select(BLSession)
        .join(Proposal, Proposal.proposalId == BLSession.proposalId)
        .filter(Proposal.proposalCode == code)
        .filter(Proposal.proposalNumber == number)
        .filter(BLSession.visit_number == visit_number)
        .options(joinedload(BLSession.Proposal))
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_dcids_for_proposal(
    db: Session,
    proposal_id: int,
    scan_type: str = None,
) -> list[int]:
    print(f"Getting dcids for {proposal_id=}")
    stmt = (
        select(DataCollection.dataCollectionId)
        .join(BLSession, DataCollection.SESSIONID == BLSession.sessionId)
        .filter(BLSession.proposalId == proposal_id)
    )
    if scan_type and scan_type.lower() == "rotation":
        stmt = stmt.filter(DataCollection.overlap == 0.0, DataCollection.axisRange > 0)
    elif scan_type and scan_type.lower() == "grid":
        stmt = stmt.join(
            GridInfo, GridInfo.dataCollectionId == DataCollection.dataCollectionId
        )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_dcids_for_blsession(
    db: Session,
    session_id: int,
    scan_type: str = None,
) -> list[int]:
    print(f"Getting data collections for {session_id=}, {scan_type=}")
    stmt = (
        select(DataCollection.dataCollectionId)
        .join(BLSession, DataCollection.SESSIONID == BLSession.sessionId)
        .filter(BLSession.sessionId == session_id)
    )
    if scan_type and scan_type.lower() == "rotation":
        stmt = stmt.filter(DataCollection.overlap == 0.0, DataCollection.axisRange > 0)
    elif scan_type and scan_type.lower() == "grid":
        stmt = stmt.join(
            GridInfo, GridInfo.dataCollectionId == DataCollection.dataCollectionId
        )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_dcids_for_sample(
    db: Session,
    sample_id: int,
    scan_type: str = None,
) -> list[int]:
    print(f"Getting data collections for {sample_id=}, {scan_type=}")
    stmt = (
        select(DataCollection.dataCollectionId)
        .join(BLSample, DataCollection.BLSAMPLEID == BLSample.blSampleId)
        .filter(BLSample.blSampleId == sample_id)
    )
    if scan_type and scan_type.lower() == "rotation":
        stmt = stmt.filter(DataCollection.overlap == 0.0, DataCollection.axisRange > 0)
    elif scan_type and scan_type.lower() == "grid":
        stmt = stmt.join(
            GridInfo, GridInfo.dataCollectionId == DataCollection.dataCollectionId
        )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_data_collections(
    db: Session,
    dcids: list[int],
) -> list[list[DataCollection]]:
    print(f"Getting data collections for {dcids=}")
    stmt = (
        select(DataCollection)
        .options(load_only(*DATA_COLLECTION_COLUMNS))
        .filter(DataCollection.dataCollectionId.in_(dcids))
    )
    results = await db.execute(stmt)
    return results.scalars().all()


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
    db: Session, dcids: list[int]
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
        # .options(joinedload(AutoProc.AutoProcProgram))
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


async def proposal_has_person(db: Session, name: str, fedid: str) -> bool:
    code, number = proposal_code_and_number_from_name(name)
    print(f"{code=}")
    print(f"{number=}")
    stmt = (
        select(func.count(Person.personId))
        .join(ProposalHasPerson, ProposalHasPerson.personId == Person.personId)
        .join(Proposal, Proposal.proposalId == ProposalHasPerson.proposalId)
        .filter(Proposal.proposalCode == code)
        .filter(Proposal.proposalNumber == number)
        .filter(Person.login == fedid)
    )
    count = await db.scalar(stmt)
    print(f"{count=}")

    return True
    # result = await db.execute(stmt)
    if count:
        return True
    return False


async def get_blsessions_for_beamline(
    db: Session,
    beamline: str,
    start_time: datetime.datetime = None,
    end_time: datetime.datetime = None,
) -> list[BLSession]:
    print(f"Getting blsessions for {beamline=}")
    stmt = (
        select(BLSession)
        .filter(BLSession.beamLineName == beamline)
        .options(joinedload(BLSession.Proposal))
    )
    if start_time:
        stmt = stmt.filter(BLSession.endDate >= start_time)
    if end_time:
        if start_time:
            assert end_time > start_time
        stmt = stmt.filter(BLSession.startDate <= end_time)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_data_collections_for_beamline(
    db: Session,
    beamline: str,
    start_time: datetime.datetime = None,
    end_time: datetime.datetime = None,
    scan_type: str = None,
) -> list[BLSession]:
    print(f"Getting data collections for {beamline=}")
    stmt = (
        select(DataCollection)
        .join(BLSession, BLSession.sessionId == DataCollection.SESSIONID)
        .filter(BLSession.beamLineName == beamline)
        .options(load_only(*DATA_COLLECTION_COLUMNS))
    )
    if start_time:
        stmt = stmt.filter(DataCollection.startTime > start_time)
    if end_time:
        if start_time:
            assert end_time > start_time
        stmt = stmt.filter(DataCollection.endTime <= end_time)
    if scan_type and scan_type.lower() == "rotation":
        stmt = stmt.filter(DataCollection.overlap == 0.0, DataCollection.axisRange > 0)
    elif scan_type and scan_type.lower() == "grid":
        stmt = stmt.join(
            GridInfo, GridInfo.dataCollectionId == DataCollection.dataCollectionId
        )
    result = await db.execute(stmt)
    return result.scalars().all()
