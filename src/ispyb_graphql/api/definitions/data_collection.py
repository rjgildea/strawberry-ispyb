from __future__ import annotations

import datetime
import enum
import os
import pathlib
from typing import TYPE_CHECKING, List, NewType, Optional

import strawberry

from ispyb_graphql import models

from .auto_processing import AutoProcessingResult

if TYPE_CHECKING:
    from .sample import Sample


Path = strawberry.scalar(
    NewType("Path", str),
    serialize=lambda v: os.fspath(v),
    parse_value=lambda v: pathlib.Path(v),
)


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
    sample_id: Optional[int] = None
    rotation_axis: Optional[str] = None
    phi_start: Optional[float] = None
    kappa_start: Optional[float] = None
    omega_start: Optional[float] = None
    chi_start: Optional[float] = None

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
    async def auto_processings(self, info) -> List[AutoProcessingResult]:
        return await info.context["auto_processing_loader"].load(self.dcid)

    @strawberry.field
    async def sample(self, info) -> Optional[strawberry.LazyType["Sample", "sample"]]:
        if self.sample_id is not None:
            return await info.context["sample_loader"].load(self.sample_id)
