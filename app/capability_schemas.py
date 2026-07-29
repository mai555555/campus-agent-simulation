from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CapabilityProfileResponse(BaseModel):
    resident_id: int
    capability_profile: Dict[str, Any]
    opportunities: List[Dict[str, Any]]
    spatial_capability: Optional[Dict[str, Any]]
    interpretation_boundary: str


class CapabilityResearchResponse(BaseModel):
    profiles: List[Dict[str, Any]]
