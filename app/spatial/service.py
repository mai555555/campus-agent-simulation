from __future__ import annotations

import hashlib
import json

from app.spatial.repository import SpatialRepository


class SpatialStateNotInitializedError(LookupError):
    pass


class ResidentNotFoundError(LookupError):
    pass


class SpatialService:
    def __init__(self, repository: SpatialRepository):
        self.repository = repository

    def get_scene_graph(self):
        nodes = [dict(row) for row in self.repository.list_nodes()]
        edges = [dict(row) for row in self.repository.list_edges()]
        checksum_source = {
            "nodes": [
                {
                    key: node[key]
                    for key in (
                        "id",
                        "code",
                        "parent_id",
                        "x",
                        "y",
                        "z",
                        "capacity",
                        "status",
                    )
                }
                for node in nodes
            ],
            "edges": [
                {
                    key: edge[key]
                    for key in (
                        "id",
                        "from_node_id",
                        "to_node_id",
                        "distance_meters",
                        "status",
                        "congestion_factor",
                        "weather_factor",
                    )
                }
                for edge in edges
            ],
        }
        checksum = hashlib.sha256(
            json.dumps(checksum_source, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return {
            "coordinate_system": "right-handed-meters",
            "schema_version": 1,
            "topology_version": checksum[:16],
            "nodes": nodes,
            "edges": edges,
        }

    def get_occupancy(self):
        spaces = []
        for row in self.repository.list_occupancy():
            item = dict(row)
            capacity = int(item["capacity"])
            occupancy = int(item["occupancy"])
            item["occupancy"] = occupancy
            item["occupancy_ratio"] = round(occupancy / capacity, 4) if capacity else 0
            spaces.append(item)
        return {"spaces": spaces}

    def get_resources(self):
        return {"resources": [dict(row) for row in self.repository.list_resources()]}

    def get_admission_queue(self):
        return {
            "queue": [dict(row) for row in self.repository.list_admission_queue()]
        }

    def get_agent_state(self, resident_id):
        row = self.repository.get_agent_state(resident_id)
        if not row:
            if not self.repository.resident_exists(resident_id):
                raise ResidentNotFoundError(f"Resident {resident_id} does not exist")
            raise SpatialStateNotInitializedError(
                f"Spatial state for resident {resident_id} is not initialized"
            )
        item = dict(row)
        capability = {
            "base_speed_m_per_min": item.pop("base_speed_m_per_min"),
            "mobility_class": item.pop("mobility_class"),
            "accessibility_needs": item.pop("accessibility_needs"),
            "perception_radius_m": item.pop("perception_radius_m"),
            "hearing_radius_m": item.pop("hearing_radius_m"),
            "source": item.pop("capability_source"),
            "version": item.pop("capability_version"),
        }
        item["capability"] = capability
        return item

    def list_agent_states(self):
        return {
            "agents": [
                self._serialize_agent_state(row)
                for row in self.repository.list_agent_states()
            ]
        }

    @staticmethod
    def _serialize_agent_state(row):
        item = dict(row)
        item["capability"] = {
            "base_speed_m_per_min": item.pop("base_speed_m_per_min"),
            "mobility_class": item.pop("mobility_class"),
            "accessibility_needs": item.pop("accessibility_needs"),
            "perception_radius_m": item.pop("perception_radius_m"),
            "hearing_radius_m": item.pop("hearing_radius_m"),
            "source": item.pop("capability_source"),
            "version": item.pop("capability_version"),
        }
        return item

    def get_trajectory(
        self,
        resident_id,
        experiment_run_id=None,
        branch_key="main",
        from_tick=None,
        to_tick=None,
    ):
        if not self.repository.resident_exists(resident_id):
            raise ResidentNotFoundError(f"Resident {resident_id} does not exist")
        run_id = experiment_run_id or self.repository.latest_experiment_run_id()
        if run_id is None:
            return {
                "resident_id": resident_id,
                "experiment_run_id": None,
                "branch_key": branch_key,
                "from_tick": 0,
                "to_tick": 0,
                "trajectory": [],
            }
        latest = self.repository.latest_trajectory_tick(
            resident_id, run_id, branch_key
        )
        effective_to = int(to_tick if to_tick is not None else latest or 0)
        effective_from = int(
            from_tick if from_tick is not None else max(0, effective_to - 200)
        )
        if effective_from < 0 or effective_to < effective_from:
            raise ValueError("Invalid trajectory tick window")
        if effective_to - effective_from > 10_000:
            raise ValueError("Trajectory tick window cannot exceed 10000")
        rows = self.repository.list_trajectory(
            resident_id,
            run_id,
            branch_key,
            effective_from,
            effective_to,
        )
        return {
            "resident_id": resident_id,
            "experiment_run_id": run_id,
            "branch_key": branch_key,
            "from_tick": effective_from,
            "to_tick": effective_to,
            "trajectory": [dict(row) for row in rows],
        }
