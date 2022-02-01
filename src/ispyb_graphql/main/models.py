from __future__ import annotations

import itertools
import logging
import operator
import re
import typing

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
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)

re_proposal = re.compile(r"([a-z][a-z])([0-9]+)")


def proposal_code_and_number_from_name(name: str) -> tuple[str, int]:
    m = re_proposal.match(name)
    assert m
    code, number = m.groups()
    return code, int(number)


def get_proposal(db: Session, name: str) -> Proposal:
    code, number = proposal_code_and_number_from_name(name)
    query = (
        db.query(Proposal)
        .filter(Proposal.proposalCode == code)
        .filter(Proposal.proposalNumber == number)
    )
    return query.one()


def get_data_collections_for_proposal(
    db: Session, proposal_id: int
) -> typing.List[DataCollection]:
    query = (
        db.query(DataCollection)
        .join(BLSession, DataCollection.SESSIONID == BLSession.sessionId)
        .filter(BLSession.proposalId == proposal_id)
    )
    return query.all()


def get_sample(db: Session, sample_id: int) -> BLSample:
    query = db.query(BLSample).filter(BLSample.blSampleId == sample_id)
    return query.one()


def get_data_collections_for_sample(
    db: Session, sample_id: int
) -> typing.List[DataCollection]:
    print(f"Getting data collections for {sample_id=}")
    query = (
        db.query(DataCollection)
        .join(BLSample, DataCollection.BLSAMPLEID == BLSample.blSampleId)
        .filter(BLSample.blSampleId == sample_id)
    )
    return query.all()


def get_data_collections_for_samples(
    db: Session, sample_ids: typing.List[int]
) -> typing.List[typing.List[DataCollection]]:
    print(f"Getting data collections for {sample_ids=}")
    query = (
        db.query(DataCollection)
        .join(BLSample, DataCollection.BLSAMPLEID == BLSample.blSampleId)
        .filter(BLSample.blSampleId.in_(sample_ids))
    )
    results = query.all()
    grouped = {
        k: list(g) for k, g in itertools.groupby(results, lambda g: g.BLSAMPLEID)
    }
    return [[dc for dc in grouped[sid]] if sid in grouped else [] for sid in sample_ids]
    return query.all()


def get_samples_for_proposal(db: Session, proposal_id: int) -> typing.List[BLSample]:
    query = (
        db.query(BLSample)
        .join(Crystal, Crystal.crystalId == BLSample.crystalId)
        .join(Protein, Protein.proteinId == Crystal.proteinId)
        .join(Container, Container.containerId == BLSample.containerId)
        .join(Proposal, Proposal.proposalId == Protein.proposalId)
        .filter(Proposal.proposalId == proposal_id)
    )
    return query.all()


def get_auto_proc_for_data_collection(
    db: Session, dcid: int
) -> typing.List[AutoProcIntegration]:
    print(f"Getting autoprocessings for dcid: {dcid}")
    query = (
        db.query(AutoProc)
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
        .filter(DataCollection.dataCollectionId == dcid)
    )
    return query.all()


def get_auto_procs_for_data_collections(
    db: Session, dcids: List[dcid]
) -> typing.List[typing.List[AutoProcIntegration]]:
    print(f"Getting autoprocessings for dcids: {dcids}")
    query = (
        db.query(DataCollection.dataCollectionId, AutoProc)
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
    results = query.all()
    grouped = {
        k: list(g) for k, g in itertools.groupby(results, lambda g: g.dataCollectionId)
    }
    return [
        [result.AutoProc for result in grouped[dcid]] if dcid in grouped else []
        for dcid in dcids
    ]
