from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AgentPerceptionEvidenceResponse(BaseModel):
    resident_id: int
    information_boundary: str
    observations: list[dict[str, Any]]
    beliefs: list[dict[str, Any]]
    spatial_memories: list[dict[str, Any]]
    received_information: list[dict[str, Any]]


class ObservationResearchResponse(BaseModel):
    observations: list[dict[str, Any]]
