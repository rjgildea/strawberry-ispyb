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
    "Permission",
    "Person",
    "Proposal",
    "ProposalHasPerson",
    "Protein",
    "SessionHasPerson",
    "UserGroup",
    "t_UserGroup_has_Permission",
    "t_UserGroup_has_Person",
]


@dataclass
class AutoProcessingResult:
    AutoProc: AutoProc
    AutoProcIntegration: AutoProcIntegration
    AutoProcProgram: AutoProcProgram
