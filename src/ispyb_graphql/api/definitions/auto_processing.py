# from __future__ import annotations

import enum
from typing import Optional

import strawberry

from ispyb_graphql import models


@strawberry.type
class UnitCell:
    a: float
    b: float
    c: float
    alpha: float
    beta: float
    gamma: float


@strawberry.enum
class MergingStatisticsType(enum.Enum):
    OVERALL = "overall"
    INNER_SHELL = "innerShell"
    OUTER_SHELL = "outerShell"


@strawberry.type
class MergingStatistics:
    shell: MergingStatisticsType
    d_min: float
    d_max: float
    r_merge: Optional[float]
    mean_isigi: Optional[float]
    completeness: Optional[float]
    multiplicity: Optional[float]
    anomalous_completeness: Optional[float]
    anomalous_multiplicity: Optional[float]
    cc_half: Optional[float]
    cc_anom: Optional[float]

    @classmethod
    def from_instance(cls, instance: models.AutoProcScalingStatistics):
        return cls(
            shell=instance.scalingStatisticsType,
            d_min=instance.resolutionLimitHigh,
            d_max=instance.resolutionLimitLow,
            r_merge=instance.rMerge,
            mean_isigi=instance.meanIOverSigI,
            completeness=instance.completeness,
            multiplicity=instance.multiplicity,
            anomalous_completeness=instance.anomalousCompleteness,
            anomalous_multiplicity=instance.anomalousMultiplicity,
            cc_half=instance.ccHalf,
            cc_anom=instance.ccAnomalous,
        )


@strawberry.type
class AutoProcessingResult:
    program: str
    space_group: str
    unit_cell: UnitCell

    auto_proc_id: strawberry.Private[int]

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
            auto_proc_id=instance.AutoProc.autoProcId,
        )

    @strawberry.field
    async def merging_statistics(
        self, info, shell: MergingStatisticsType
    ) -> Optional[MergingStatistics]:
        merging_stats = await info.context["merging_statistics_loader"].load(
            self.auto_proc_id
        )
        return next((ms for ms in merging_stats if ms.shell == shell.value), None)
