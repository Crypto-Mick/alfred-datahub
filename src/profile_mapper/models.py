from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# -----------------------------
# Profile & Meta
# -----------------------------

@dataclass(frozen=True)
class ProfileInfo:
    name: str
    version: int
    hash: str  # sha1:<hex>


# -----------------------------
# Resolution (diagnostic only)
# -----------------------------

@dataclass(frozen=True)
class ResolutionCounts:
    item_ids: int
    locations: int
    qualities: int
    request_units: int


@dataclass(frozen=True)
class ResolutionInfo:
    counts: ResolutionCounts
    item_ids_preview: List[str]
    item_ids_preview_truncated: bool


# -----------------------------
# Guardrails
# -----------------------------

@dataclass(frozen=True)
class GuardrailBeforeAfter:
    item_ids: int
    request_units: int


@dataclass(frozen=True)
class GuardrailInfo:
    applied: bool
    policy: Optional[str] = None           # e.g. "max_request_units" | "max_item_ids"
    reason: Optional[str] = None           # human-readable
    method: Optional[str] = None           # e.g. "priority_groups"
    before: Optional[GuardrailBeforeAfter] = None
    after: Optional[GuardrailBeforeAfter] = None


# -----------------------------
# Outputs
# -----------------------------

@dataclass(frozen=True)
class OutputsInfo:
    generated_task_path: Optional[str]     # None if denied/error
    report_path: str                       # always present


# -----------------------------
# Mapper Result (core contract)
# -----------------------------

@dataclass
class MapperResult:
    """
    Canonical result of Profile Mapper v1 execution.
    """

    status: str                            # "ok" | "trimmed" | "denied" | "error"
    input_summary: Dict[str, Any]
    profile: ProfileInfo
    resolution: Optional[ResolutionInfo]
    guardrails: Optional[GuardrailInfo]
    task_yaml: Optional[Dict[str, Any]]    # declarative v1; None if denied/error
    outputs: OutputsInfo
    warnings: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)

    # --------- helpers (constructors) ---------

    @staticmethod
    def ok(
        *,
        input_summary: Dict[str, Any],
        profile: ProfileInfo,
        resolution: ResolutionInfo,
        guardrails: Optional[GuardrailInfo],
        task_yaml: Dict[str, Any],
        report_path: str,
        warnings: Optional[List[str]] = None,
    ) -> "MapperResult":
        return MapperResult(
            status="ok",
            input_summary=input_summary,
            profile=profile,
            resolution=resolution,
            guardrails=guardrails,
            task_yaml=task_yaml,
            outputs=OutputsInfo(
                generated_task_path="output/task.yaml",
                report_path=report_path,
            ),
            warnings=warnings or [],
            errors=[],
        )

    @staticmethod
    def trimmed(
        *,
        input_summary: Dict[str, Any],
        profile: ProfileInfo,
        resolution: ResolutionInfo,
        guardrails: GuardrailInfo,
        task_yaml: Dict[str, Any],
        report_path: str,
        warnings: Optional[List[str]] = None,
    ) -> "MapperResult":
        return MapperResult(
            status="trimmed",
            input_summary=input_summary,
            profile=profile,
            resolution=resolution,
            guardrails=guardrails,
            task_yaml=task_yaml,
            outputs=OutputsInfo(
                generated_task_path="output/task.yaml",
                report_path=report_path,
            ),
            warnings=warnings or ["Request trimmed deterministically by profile guardrails"],
            errors=[],
        )

    @staticmethod
    def denied(
        *,
        input_summary: Dict[str, Any],
        profile: ProfileInfo,
        guardrails: GuardrailInfo,
        report_path: str,
        message: str,
    ) -> "MapperResult":
        return MapperResult(
            status="denied",
            input_summary=input_summary,
            profile=profile,
            resolution=None,
            guardrails=guardrails,
            task_yaml=None,
            outputs=OutputsInfo(
                generated_task_path=None,
                report_path=report_path,
            ),
            warnings=[],
            errors=[{
                "code": "MAPPER_DENIED",
                "message": message,
            }],
        )

    @staticmethod
    def error(
        *,
        input_summary: Dict[str, Any],
        profile: Optional[ProfileInfo],
        report_path: str,
        message: str,
    ) -> "MapperResult":
        return MapperResult(
            status="error",
            input_summary=input_summary,
            profile=profile or ProfileInfo(name="unknown", version=0, hash=""),
            resolution=None,
            guardrails=None,
            task_yaml=None,
            outputs=OutputsInfo(
                generated_task_path=None,
                report_path=report_path,
            ),
            warnings=[],
            errors=[{
                "code": "MAPPER_INTERNAL_ERROR",
                "message": message,
            }],
        )
