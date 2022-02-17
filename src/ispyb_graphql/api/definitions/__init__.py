# from __future__ import annotations

import datetime
import enum
import os
import pathlib
import typing

import strawberry
from sqlalchemy.orm import Session

from ispyb_graphql import crud, models

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
class AutoProcessingResult:
    program: str
    space_group: str
    unit_cell: UnitCell

    @classmethod
    def from_instance(
        cls,
        instance: models.AutoProcessingResult,
    ):
        return cls(
            program=instance.AutoProcProgram.processingPrograms,
            space_group=instance.AutoProc.spaceGroup,
            unit_cell=UnitCell(
                instance.AutoProc.refinedCell_a,
                instance.AutoProc.refinedCell_b,
                instance.AutoProc.refinedCell_c,
                instance.AutoProc.refinedCell_alpha,
                instance.AutoProc.refinedCell_beta,
                instance.AutoProc.refinedCell_gamma,
            ),
        )


async def load_auto_processings(
    db: Session, dcids: typing.List[strawberry.ID]
) -> typing.List[typing.List[AutoProcessingResult]]:
    result = await crud.get_auto_processing_results_for_dcids(db, dcids)
    return [
        [AutoProcessingResult.from_instance(ap) for ap in auto_processings]
        for auto_processings in result
    ]


async def load_data_collections(
    db: Session, dcids: typing.List[strawberry.ID]
) -> typing.List[typing.List["DataCollection"]]:
    data_collections = await crud.get_data_collections(db, dcids)
    return [DataCollection.from_instance(dc) for dc in data_collections]


async def load_samples(
    db: Session, sample_ids: typing.List[strawberry.ID]
) -> typing.List[typing.List["Sample"]]:
    samples = await crud.get_samples(db, sample_ids)
    return [Sample.from_instance(sample) for sample in samples]


@strawberry.enum
class ScanType(enum.Enum):
    ROTATION = "rotation"
    GRID = "grid"
    SCREENING = "screening"


@strawberry.type
class DataCollection:
    dcid: int
    filename: Path
    start_time: datetime.datetime
    end_time: datetime.datetime
    axis_start: float
    axis_end: float
    axis_range: float
    overlap: float
    number_of_images: int
    start_image_number: int
    exposure_time: float
    sample_id: typing.Optional[int] = None
    rotation_axis: typing.Optional[str] = None
    phi_start: typing.Optional[float] = (None,)
    kappa_start: typing.Optional[float] = None
    omega_start: typing.Optional[float] = (None,)
    chi_start: typing.Optional[float] = (None,)

    @classmethod
    def from_instance(cls, instance: models.DataCollection):
        return cls(
            dcid=instance.dataCollectionId,
            filename=f"{instance.imageDirectory}{instance.fileTemplate}",
            sample_id=instance.BLSAMPLEID,
            start_time=instance.startTime,
            end_time=instance.endTime,
            axis_start=instance.axisStart,
            axis_end=instance.axisEnd,
            axis_range=instance.axisRange,
            overlap=instance.overlap,
            number_of_images=instance.numberOfImages,
            start_image_number=instance.startImageNumber,
            exposure_time=instance.exposureTime,
            rotation_axis=instance.rotationAxis,
            phi_start=instance.phiStart,
            kappa_start=instance.kappaStart,
            omega_start=instance.omegaStart,
            chi_start=instance.chiStart,
        )

    @strawberry.field
    async def auto_processings(self, info) -> typing.List[AutoProcessingResult]:
        return await info.context["auto_processing_loader"].load(self.dcid)

    @strawberry.field
    async def sample(self, info) -> typing.Optional["Sample"]:
        if self.sample_id is not None:
            return await info.context["sample_loader"].load(self.sample_id)


@strawberry.type
class Proposal:
    proposal_id: int
    name: str

    @strawberry.field
    async def data_collections(
        self, info, scan_type: typing.Optional[ScanType] = None
    ) -> typing.List[DataCollection]:
        db = info.context["db"]
        dcids = await crud.get_dcids_for_proposal(
            db, self.proposal_id, scan_type.value if scan_type else None
        )
        data_collections = [
            info.context["data_collections_loader"].load(dcid) for dcid in dcids
        ]
        return data_collections

    @strawberry.field
    async def samples(self, info) -> typing.List["Sample"]:
        db = info.context["db"]
        samples = await crud.get_samples_for_proposal(db, self.proposal_id)
        return [Sample.from_instance(sample) for sample in samples]

    @classmethod
    def from_instance(cls, instance: crud.Proposal):
        return cls(
            proposal_id=instance.proposalId,
            name=f"{instance.proposalCode}{instance.proposalNumber}",
        )


@strawberry.type
class Visit:
    session_id: int
    name: str
    start_time: datetime.datetime
    end_time: datetime.datetime

    @strawberry.field
    async def data_collections(
        self, info, scan_type: ScanType = None
    ) -> typing.List[DataCollection]:
        db = info.context["db"]
        dcids = await crud.get_dcids_for_blsession(
            db, self.session_id, scan_type.value if scan_type else None
        )
        data_collections = [
            info.context["data_collections_loader"].load(dcid) for dcid in dcids
        ]
        return data_collections

    @classmethod
    def from_instance(cls, instance: models.BLSession):
        return cls(
            session_id=instance.sessionId,
            name=f"{instance.Proposal.proposalCode}{instance.Proposal.proposalNumber}-{instance.visit_number}",
            start_time=instance.startDate,
            end_time=instance.endDate,
        )


@strawberry.type
class Sample:
    name: str
    sample_id: int
    crystal_id: int

    @strawberry.field
    async def data_collections(
        self, info, scan_type: ScanType = None
    ) -> typing.List[DataCollection]:
        db = info.context["db"]
        dcids = await crud.get_dcids_for_sample(
            db, self.sample_id, scan_type=scan_type.value if scan_type else None
        )
        return [info.context["data_collections_loader"].load(dcid) for dcid in dcids]

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
    ) -> typing.List[DataCollection]:
        db = info.context["db"]
        data_collections = await crud.get_data_collections_for_beamline(
            db,
            self.name,
            start_time=start_time,
            end_time=end_time,
            scan_type=scan_type.value if scan_type else scan_type,
        )
        return [DataCollection.from_instance(dc) for dc in data_collections]
