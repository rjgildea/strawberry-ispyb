# from __future__ import annotations

import datetime
import os
import pathlib
import typing

import strawberry
from main import models
from sqlalchemy.orm import Session

Path = strawberry.scalar(
    typing.NewType("Path", str),
    serialize=lambda v: os.fspath(v),
    parse_value=lambda v: pathlib.Path(v),
)


@strawberry.type
class UnitCell:
    a: float
    b: float
    c: float
    alpha: float
    beta: float
    gamma: float


@strawberry.type
class AutoProc:
    space_group: str
    unit_cell: UnitCell

    @classmethod
    def from_instance(cls, instance: models.AutoProc):
        return cls(
            space_group=instance.spaceGroup,
            unit_cell=UnitCell(
                instance.refinedCell_a,
                instance.refinedCell_b,
                instance.refinedCell_c,
                instance.refinedCell_alpha,
                instance.refinedCell_beta,
                instance.refinedCell_gamma,
            ),
        )


async def load_auto_processings(
    db: Session, dcids: typing.List[strawberry.ID]
) -> typing.List[typing.List[AutoProc]]:
    result = await models.get_auto_procs_for_data_collections(db, dcids)
    return [
        [AutoProc.from_instance(ap) for ap in auto_processings]
        for auto_processings in result
    ]


async def load_data_collections_for_samples(
    db: Session, sample_ids: typing.List[strawberry.ID]
) -> typing.List[typing.List["DataCollection"]]:
    result = await models.get_data_collections_for_samples(db, sample_ids)
    return [
        [DataCollection.from_instance(dc) for dc in data_collections]
        for data_collections in result
    ]


async def load_data_collections_for_visit(
    db: Session, blsession_ids: typing.List[strawberry.ID]
) -> typing.List[typing.List["DataCollection"]]:
    result = await models.get_data_collections_for_blsessions(db, blsession_ids)
    return [
        [DataCollection.from_instance(dc) for dc in data_collections]
        for data_collections in result
    ]


async def load_samples(
    db: Session, sample_ids: typing.List[strawberry.ID]
) -> typing.List[typing.List["Samples"]]:
    samples = await models.get_samples(db, sample_ids)
    return [Sample.from_instance(sample) for sample in samples]


@strawberry.type
class DataCollection:
    dcid: int
    filename: Path
    start_time: datetime.datetime
    end_time: datetime.datetime
    sample_id: typing.Optional[int] = None

    # instance: strawberry.Private[models.DataCollection]

    @classmethod
    def from_instance(cls, instance: models.DataCollection):
        return cls(
            dcid=instance.dataCollectionId,
            filename=f"{instance.imageDirectory}{instance.fileTemplate}",
            sample_id=instance.BLSAMPLEID,
            start_time=instance.startTime,
            end_time=instance.endTime,
        )

    @strawberry.field
    async def auto_processings(self, info) -> typing.List[AutoProc]:
        db = info.context["db"]
        return await info.context["auto_processing_loader"].load(self.dcid)

    @strawberry.field
    async def sample(self, info) -> typing.Optional["Sample"]:
        if self.sample_id is not None:
            db = info.context["db"]
            return await info.context["sample_loader"].load(self.sample_id)


@strawberry.type
class Proposal:
    proposal_id: int
    name: str

    instance: strawberry.Private[models.Proposal]

    @strawberry.field
    async def data_collections(self, info) -> typing.List[DataCollection]:
        proposal: models.Proposal = self.instance
        db = info.context["db"]
        data_collections = await models.get_data_collections_for_proposal(
            db, proposal.proposalId
        )
        return [DataCollection.from_instance(dc) for dc in data_collections]

    @strawberry.field
    async def samples(self, info) -> typing.List["Sample"]:
        proposal: Proposal = self.instance
        db = info.context["db"]
        samples = await models.get_samples_for_proposal(db, proposal.proposalId)
        return [Sample.from_instance(sample) for sample in samples]

    @classmethod
    def from_instance(cls, instance: models.Proposal):
        return cls(
            proposal_id=instance.proposalId,
            name=f"{instance.proposalCode}{instance.proposalNumber}",
            instance=instance,
        )


@strawberry.type
class Visit:
    session_id: int
    name: str
    start_time: datetime.datetime
    end_time: datetime.datetime

    instance: strawberry.Private[models.BLSession]

    @strawberry.field
    async def data_collections(self, info) -> typing.List[DataCollection]:
        session: BLSession = self.instance
        db = info.context["db"]
        return await info.context["data_collections_for_visit_loader"].load(
            self.session_id
        )

    @classmethod
    def from_instance(cls, instance: models.BLSession):
        return cls(
            session_id=instance.sessionId,
            name=f"{instance.Proposal.proposalCode}{instance.Proposal.proposalNumber}-{instance.visit_number}",
            start_time=instance.startDate,
            end_time=instance.endDate,
            instance=instance,
        )


@strawberry.type
class Sample:
    name: str
    sample_id: int
    crystal_id: int

    @strawberry.field
    async def data_collections(self, info) -> typing.List[DataCollection]:
        db = info.context["db"]
        return await info.context["data_collections_loader"].load(self.sample_id)

    @classmethod
    def from_instance(cls, instance: models.BLSample):
        return cls(
            name=instance.name,
            sample_id=instance.blSampleId,
            crystal_id=instance.crystalId,
        )


@strawberry.type
class Beamline:
    name: str

    @strawberry.field
    async def visits(
        self,
        info,
        start_time: datetime.datetime = None,
        end_time: datetime.datetime = datetime.datetime.now(),
    ) -> typing.List[Visit]:
        db = info.context["db"]
        blsessions = await models.get_blsessions_for_beamline(
            db, self.name, start_time=start_time, end_time=end_time
        )
        return [Visit.from_instance(blsession) for blsession in blsessions]
