from __future__ import annotations

import datetime
import itertools
import logging
import re
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, load_only

from ispyb_graphql.models import (
    AutoProc,
    AutoProcessingResult,
    AutoProcIntegration,
    AutoProcProgram,
    AutoProcScaling,
    AutoProcScalingStatistics,
    BLSample,
    BLSession,
    Container,
    Crystal,
    DataCollection,
    GridInfo,
    Permission,
    Person,
    Proposal,
    ProposalHasPerson,
    Protein,
    SessionHasPerson,
    UserGroup,
    t_UserGroup_has_Permission,
    t_UserGroup_has_Person,
)

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


BL_TYPES = {
    "i02": "mx",
    "i02-1": "mx",
    "i02-2": "mx",
    "i03": "mx",
    "i04": "mx",
    "i04-1": "mx",
    "i23": "mx",
    "i24": "mx",
}


def proposal_code_and_number_from_name(name: str) -> tuple[str, int]:
    m = re_proposal.match(name)
    assert m
    code, number = m.groups()
    return code, int(number)


def proposal_code_number_and_visit_number_from_name(name: str) -> tuple[str, int, int]:
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
    limit: Optional[int] = None,
    after: Optional[int] = None,
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
    if after:
        stmt = stmt.filter(DataCollection.dataCollectionId > after)
    if limit:
        stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_dcids_for_blsession(
    db: Session,
    session_id: int,
    scan_type: str = None,
    limit: Optional[int] = None,
    after: Optional[int] = None,
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
    if after:
        stmt = stmt.filter(DataCollection.dataCollectionId > after)
    if limit:
        stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_dcids_for_sample(
    db: Session,
    sample_id: int,
    scan_type: str = None,
    limit: Optional[int] = None,
    after: Optional[int] = None,
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
    if after:
        stmt = stmt.filter(DataCollection.dataCollectionId > after)
    if limit:
        stmt = stmt.limit(limit)
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


async def get_containers(db: Session, container_ids: list[int]) -> list[Container]:
    print(f"Getting {container_ids=}")
    stmt = select(Container).filter(Container.containerId.in_(container_ids))
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_auto_processing_results_for_dcids(
    db: Session, dcids: list[int]
) -> list[list[AutoProcessingResult]]:
    print(f"Getting autoprocessings for dcids: {dcids}")
    stmt = (
        select(
            DataCollection.dataCollectionId,
            AutoProc,
            AutoProcIntegration,
            AutoProcProgram,
        )
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
        [
            AutoProcessingResult(
                AutoProc=result.AutoProc,
                AutoProcIntegration=result.AutoProcIntegration,
                AutoProcProgram=result.AutoProcProgram,
            )
            for result in grouped[dcid]
        ]
        if dcid in grouped
        else []
        for dcid in dcids
    ]


async def get_auto_proc_scaling_statistics_for_apids(
    db: Session, apids: list[int]
) -> list[list[AutoProcScalingStatistics]]:
    print(f"Getting AutoProcScalingStatistics for apids: {apids}")
    stmt = (
        select(
            AutoProc.autoProcId,
            AutoProcScalingStatistics,
        )
        .join(
            AutoProcScaling,
            AutoProcScaling.autoProcScalingId
            == AutoProcScalingStatistics.autoProcScalingId,
        )
        .join(AutoProc, AutoProcScaling.autoProcId == AutoProc.autoProcId)
        .filter(AutoProc.autoProcId.in_(apids))
    )
    results = await db.execute(stmt)
    grouped = {
        k: list(g) for k, g in itertools.groupby(results.all(), lambda g: g.autoProcId)
    }
    return [
        [result.AutoProcScalingStatistics for result in grouped[apid]]
        if apid in grouped
        else []
        for apid in apids
    ]


async def proposal_has_person(db: Session, name: str, fedid: str) -> bool:
    code, number = proposal_code_and_number_from_name(name)
    stmt = (
        select(func.count(Person.personId))
        .join(ProposalHasPerson, ProposalHasPerson.personId == Person.personId)
        .join(Proposal, Proposal.proposalId == ProposalHasPerson.proposalId)
        .filter(Proposal.proposalCode == code)
        .filter(Proposal.proposalNumber == number)
        .filter(Person.login == fedid)
    )
    count = await db.scalar(stmt)
    return count > 0


async def session_has_person(db: Session, name: str, fedid: str) -> bool:
    code, number, visit_number = proposal_code_number_and_visit_number_from_name(name)
    stmt = (
        select(func.count(Person.personId))
        .join(SessionHasPerson, SessionHasPerson.personId == Person.personId)
        .join(BLSession, BLSession.sessionId == SessionHasPerson.sessionId)
        .join(Proposal, Proposal.proposalId == BLSession.proposalId)
        .filter(Proposal.proposalCode == code)
        .filter(Proposal.proposalNumber == number)
        .filter(BLSession.visit_number == visit_number)
        .filter(Person.login == fedid)
    )
    count = await db.scalar(stmt)
    return count > 0


async def get_permissions_and_user_groups(db: Session, fedid: str) -> bool:
    stmt = (
        select(Permission, UserGroup)
        .join(
            t_UserGroup_has_Permission,
            t_UserGroup_has_Permission.c.permissionId == Permission.permissionId,
        )
        .join(
            UserGroup, UserGroup.userGroupId == t_UserGroup_has_Permission.c.userGroupId
        )
        .join(
            t_UserGroup_has_Person,
            t_UserGroup_has_Person.c.userGroupId
            == t_UserGroup_has_Permission.c.userGroupId,
        )
        .join(Person, Person.personId == t_UserGroup_has_Person.c.personId)
        .filter(Person.login == fedid)
    )
    result = await db.execute(stmt)
    return result.all()


async def user_is_admin_for_beamline(db: Session, fedid: str, beamline: str) -> bool:
    result = await get_permissions_and_user_groups(db, fedid)
    for p, ug in result:
        print(p.type, ug.name)

    admin_ptype = set(
        p.type.split("_")[0] for p, _ in result if p.type.endswith("_admin")
    )
    bl_type = BL_TYPES.get(beamline)
    if bl_type and bl_type in admin_ptype:
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


async def get_beamline_for_visit(
    db: Session,
    visit: str,
) -> str:
    print(f"Getting beamline for visit {visit=}")
    blsession = await get_blsession(db, visit)
    return blsession.name


async def get_data_collections_for_beamline(
    db: Session,
    beamline: str,
    start_time: datetime.datetime = None,
    end_time: datetime.datetime = None,
    scan_type: str = None,
    limit: Optional[int] = None,
    after: Optional[int] = None,
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
    if after:
        stmt = stmt.filter(DataCollection.dataCollectionId > after)
    if limit:
        stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
