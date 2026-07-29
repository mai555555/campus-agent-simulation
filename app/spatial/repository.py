from __future__ import annotations

from sqlalchemy import and_, func, select, text
from sqlalchemy.engine import Connection

from app.spatial.models import (
    agent_spatial_capabilities,
    agent_spatial_states,
    agent_trajectories,
    spatial_admission_queue,
    spatial_edges,
    spatial_nodes,
    spatial_resources,
)


class SpatialRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    def list_nodes(self):
        return list(
            self.connection.execute(
                select(spatial_nodes).order_by(spatial_nodes.c.id)
            ).mappings()
        )

    def list_edges(self):
        return list(
            self.connection.execute(
                select(spatial_edges).order_by(spatial_edges.c.id)
            ).mappings()
        )

    def list_occupancy(self):
        occupancy = (
            select(
                agent_spatial_states.c.current_node_id.label("node_id"),
                func.count().label("occupancy"),
            )
            .group_by(agent_spatial_states.c.current_node_id)
            .subquery()
        )
        statement = (
            select(
                spatial_nodes.c.id.label("node_id"),
                spatial_nodes.c.code,
                spatial_nodes.c.name,
                spatial_nodes.c.capacity,
                func.coalesce(occupancy.c.occupancy, 0).label("occupancy"),
            )
            .outerjoin(occupancy, occupancy.c.node_id == spatial_nodes.c.id)
            .where(spatial_nodes.c.capacity > 0)
            .order_by(spatial_nodes.c.id)
        )
        return list(self.connection.execute(statement).mappings())

    def list_resources(self):
        statement = (
            select(
                spatial_resources,
                spatial_nodes.c.code.label("node_code"),
                spatial_nodes.c.name.label("node_name"),
            )
            .join(spatial_nodes, spatial_nodes.c.id == spatial_resources.c.node_id)
            .order_by(spatial_resources.c.node_id, spatial_resources.c.id)
        )
        return list(self.connection.execute(statement).mappings())

    def list_admission_queue(self):
        statement = (
            select(
                spatial_admission_queue,
                spatial_nodes.c.code.label("node_code"),
                spatial_nodes.c.name.label("node_name"),
                spatial_resources.c.resource_key,
                spatial_resources.c.name.label("resource_name"),
            )
            .join(
                spatial_nodes,
                spatial_nodes.c.id == spatial_admission_queue.c.node_id,
            )
            .outerjoin(
                spatial_resources,
                spatial_resources.c.id == spatial_admission_queue.c.resource_id,
            )
            .order_by(
                spatial_admission_queue.c.node_id,
                spatial_admission_queue.c.queue_position,
            )
        )
        return list(self.connection.execute(statement).mappings())

    def _agent_state_statement(self):
        current = spatial_nodes.alias("current_node")
        target = spatial_nodes.alias("target_node")
        return (
            select(
                agent_spatial_states,
                current.c.code.label("current_node_code"),
                current.c.name.label("current_node_name"),
                target.c.code.label("target_node_code"),
                target.c.name.label("target_node_name"),
                agent_spatial_capabilities.c.base_speed_m_per_min,
                agent_spatial_capabilities.c.mobility_class,
                agent_spatial_capabilities.c.accessibility_needs,
                agent_spatial_capabilities.c.perception_radius_m,
                agent_spatial_capabilities.c.hearing_radius_m,
                agent_spatial_capabilities.c.source.label("capability_source"),
                agent_spatial_capabilities.c.version.label("capability_version"),
            )
            .join(current, current.c.id == agent_spatial_states.c.current_node_id)
            .outerjoin(target, target.c.id == agent_spatial_states.c.target_node_id)
            .join(
                agent_spatial_capabilities,
                agent_spatial_capabilities.c.resident_id
                == agent_spatial_states.c.resident_id,
            )
        )

    def get_agent_state(self, resident_id):
        statement = self._agent_state_statement().where(
            agent_spatial_states.c.resident_id == resident_id
        )
        return self.connection.execute(statement).mappings().first()

    def list_agent_states(self):
        statement = self._agent_state_statement().order_by(
            agent_spatial_states.c.resident_id
        )
        return list(self.connection.execute(statement).mappings())

    def resident_exists(self, resident_id):
        row = self.connection.execute(
            text("SELECT 1 FROM residents WHERE id = :resident_id"),
            {"resident_id": resident_id},
        ).first()
        return row is not None

    def latest_experiment_run_id(self):
        row = self.connection.exec_driver_sql(
            "SELECT id FROM experiment_runs ORDER BY id DESC LIMIT 1"
        ).first()
        return int(row[0]) if row else None

    def latest_trajectory_tick(self, resident_id, experiment_run_id, branch_key):
        statement = select(func.max(agent_trajectories.c.tick_number)).where(
            and_(
                agent_trajectories.c.resident_id == resident_id,
                agent_trajectories.c.experiment_run_id == experiment_run_id,
                agent_trajectories.c.branch_key == branch_key,
            )
        )
        return self.connection.execute(statement).scalar_one_or_none()

    def list_trajectory(
        self,
        resident_id,
        experiment_run_id,
        branch_key,
        from_tick,
        to_tick,
    ):
        statement = (
            select(agent_trajectories)
            .where(
                and_(
                    agent_trajectories.c.resident_id == resident_id,
                    agent_trajectories.c.experiment_run_id == experiment_run_id,
                    agent_trajectories.c.branch_key == branch_key,
                    agent_trajectories.c.tick_number >= from_tick,
                    agent_trajectories.c.tick_number <= to_tick,
                )
            )
            .order_by(agent_trajectories.c.tick_number, agent_trajectories.c.id)
        )
        return list(self.connection.execute(statement).mappings())
