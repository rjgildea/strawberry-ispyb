from dataclasses import dataclass

from ispyb.sqlalchemy import (
    AutoProc,
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
    Person,
    Proposal,
    ProposalHasPerson,
    Protein,
)

__all__ = [
    "AutoProc",
    "AutoProcIntegration",
    "AutoProcProgram",
    "AutoProcScaling",
    "AutoProcScalingStatistics",
    "AutoProcessingResult",
    "BLSample",
    "BLSession",
    "Container",
    "Crystal",
    "DataCollection",
    "GridInfo",
    "Person",
    "Proposal",
    "ProposalHasPerson",
    "Protein",
]


@dataclass
class AutoProcessingResult:
    AutoProc: AutoProc
    AutoProcIntegration: AutoProcIntegration
    AutoProcProgram: AutoProcProgram
