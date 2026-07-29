from __future__ import annotations

import heapq
from math import inf


RISK_FACTORS = {
    "low": 1.0,
    "medium": 1.2,
    "high": 1.6,
}


class RouteNotFoundError(LookupError):
    pass


def edge_travel_minutes(edge, speed_m_per_min):
    properties = edge.get("properties") or {}
    risk_factor = float(
        properties.get(
            "risk_factor",
            RISK_FACTORS.get(str(properties.get("risk_level") or "low"), 1.0),
        )
    )
    environment_factor = (
        float(edge.get("congestion_factor") or 1.0)
        * float(edge.get("weather_factor") or 1.0)
        * max(1.0, risk_factor)
    )
    return (
        float(edge["distance_meters"])
        / float(speed_m_per_min)
        * environment_factor
    )


def edge_is_accessible(edge, accessibility_needs):
    properties = edge.get("properties") or {}
    if not accessibility_needs:
        return True
    if accessibility_needs.get("step_free") or accessibility_needs.get("wheelchair"):
        return bool(properties.get("accessible", False)) and not bool(
            properties.get("stairs", False)
        )
    return True


def plan_route(
    nodes,
    edges,
    start_node_id,
    target_node_id,
    speed_m_per_min,
    accessibility_needs=None,
):
    node_by_id = {int(node["id"]): node for node in nodes}
    start_node_id = int(start_node_id)
    target_node_id = int(target_node_id)
    if start_node_id not in node_by_id or target_node_id not in node_by_id:
        raise RouteNotFoundError("Route endpoint does not exist")
    if node_by_id[target_node_id].get("status") != "open":
        raise RouteNotFoundError("Destination is closed")
    if start_node_id == target_node_id:
        return {
            "node_ids": [start_node_id],
            "edge_ids": [],
            "distance_meters": 0.0,
            "estimated_minutes": 0.0,
            "cost_minutes": 0.0,
        }

    adjacency = {node_id: [] for node_id in node_by_id}
    for edge in edges:
        if edge.get("status") != "open":
            continue
        if not edge_is_accessible(edge, accessibility_needs or {}):
            continue
        from_id = int(edge["from_node_id"])
        to_id = int(edge["to_node_id"])
        if (
            from_id not in node_by_id
            or to_id not in node_by_id
            or node_by_id[from_id].get("status") != "open"
            or node_by_id[to_id].get("status") != "open"
        ):
            continue
        cost = edge_travel_minutes(edge, speed_m_per_min)
        adjacency[from_id].append((to_id, cost, edge))
        if edge.get("bidirectional"):
            adjacency[to_id].append((from_id, cost, edge))

    best = {start_node_id: 0.0}
    previous = {}
    queue = [(0.0, start_node_id)]
    while queue:
        current_cost, node_id = heapq.heappop(queue)
        if current_cost > best.get(node_id, inf):
            continue
        if node_id == target_node_id:
            break
        for next_id, edge_cost, edge in adjacency.get(node_id, []):
            candidate = current_cost + edge_cost
            if candidate >= best.get(next_id, inf):
                continue
            best[next_id] = candidate
            previous[next_id] = (node_id, edge)
            heapq.heappush(queue, (candidate, next_id))

    if target_node_id not in previous:
        raise RouteNotFoundError("No traversable route to destination")

    node_ids = [target_node_id]
    route_edges = []
    cursor = target_node_id
    while cursor != start_node_id:
        prior, edge = previous[cursor]
        route_edges.append(edge)
        node_ids.append(prior)
        cursor = prior
    node_ids.reverse()
    route_edges.reverse()
    distance = sum(float(edge["distance_meters"]) for edge in route_edges)
    direct_minutes = distance / float(speed_m_per_min)
    return {
        "node_ids": node_ids,
        "edge_ids": [int(edge["id"]) for edge in route_edges],
        "distance_meters": round(distance, 3),
        "estimated_minutes": round(direct_minutes, 3),
        "cost_minutes": round(best[target_node_id], 3),
    }
