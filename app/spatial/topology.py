from __future__ import annotations

from math import dist


WALKING_BASE_METERS_PER_MINUTE = 78.0

NODE_SEEDS = [
    {
        "code": "dorm",
        "name": "宿舍区",
        "node_type": "building",
        "parent_code": None,
        "x": -135.0,
        "y": 0.0,
        "z": -115.0,
        "radius": 24.0,
        "capacity": 600,
        "location": "宿舍区",
    },
    {
        "code": "teaching",
        "name": "教学楼",
        "node_type": "building",
        "parent_code": None,
        "x": -30.0,
        "y": 0.0,
        "z": -45.0,
        "radius": 22.0,
        "capacity": 450,
        "location": "教学楼",
    },
    {
        "code": "library",
        "name": "图书馆",
        "node_type": "building",
        "parent_code": None,
        "x": 130.0,
        "y": 0.0,
        "z": -35.0,
        "radius": 20.0,
        "capacity": 220,
        "location": "图书馆",
    },
    {
        "code": "canteen",
        "name": "食堂",
        "node_type": "building",
        "parent_code": None,
        "x": -25.0,
        "y": 0.0,
        "z": 95.0,
        "radius": 20.0,
        "capacity": 300,
        "location": "食堂",
    },
    {
        "code": "playground",
        "name": "操场",
        "node_type": "zone",
        "parent_code": None,
        "x": 120.0,
        "y": 0.0,
        "z": 105.0,
        "radius": 38.0,
        "capacity": 500,
        "location": "操场",
    },
    {
        "code": "business",
        "name": "商业街",
        "node_type": "zone",
        "parent_code": None,
        "x": 65.0,
        "y": 0.0,
        "z": 35.0,
        "radius": 24.0,
        "capacity": 180,
        "location": "商业街",
    },
    {
        "code": "admin",
        "name": "校务处",
        "node_type": "building",
        "parent_code": None,
        "x": -145.0,
        "y": 0.0,
        "z": 25.0,
        "radius": 16.0,
        "capacity": 80,
        "location": "校务处",
    },
    *[
        {
            "code": f"{code}_entrance",
            "name": f"{name}入口",
            "node_type": "entrance",
            "parent_code": code,
            "x": x,
            "y": 0.0,
            "z": z,
            "radius": 4.0,
            "capacity": 0,
            "location": "",
        }
        for code, name, x, z in (
            ("dorm", "宿舍区", -120.0, -95.0),
            ("teaching", "教学楼", -30.0, -25.0),
            ("library", "图书馆", 110.0, -20.0),
            ("canteen", "食堂", -25.0, 75.0),
            ("playground", "操场", 100.0, 85.0),
            ("business", "商业街", 55.0, 30.0),
            ("admin", "校务处", -125.0, 20.0),
        )
    ],
    *[
        {
            "code": code,
            "name": name,
            "node_type": "path_point",
            "parent_code": None,
            "x": x,
            "y": 0.0,
            "z": z,
            "radius": 3.0,
            "capacity": 0,
            "location": "",
        }
        for code, name, x, z in (
            ("path_west", "西侧道路节点", -90.0, -20.0),
            ("path_central", "中央道路节点", -20.0, 15.0),
            ("path_north", "北侧道路节点", 15.0, 65.0),
            ("path_east", "东侧道路节点", 80.0, 20.0),
            ("path_southeast", "东南道路节点", 85.0, 75.0),
        )
    ],
]

EDGE_SEEDS = [
    ("dorm", "dorm_entrance", "building_access"),
    ("teaching", "teaching_entrance", "building_access"),
    ("library", "library_entrance", "building_access"),
    ("canteen", "canteen_entrance", "building_access"),
    ("playground", "playground_entrance", "zone_access"),
    ("business", "business_entrance", "zone_access"),
    ("admin", "admin_entrance", "building_access"),
    ("dorm_entrance", "path_west", "campus_walkway"),
    ("admin_entrance", "path_west", "campus_walkway"),
    ("path_west", "path_central", "campus_walkway"),
    ("teaching_entrance", "path_central", "campus_walkway"),
    ("path_central", "path_north", "campus_walkway"),
    ("canteen_entrance", "path_north", "campus_walkway"),
    ("path_central", "path_east", "campus_walkway"),
    ("business_entrance", "path_east", "campus_walkway"),
    ("library_entrance", "path_east", "campus_walkway"),
    ("path_east", "path_southeast", "campus_walkway"),
    ("path_north", "path_southeast", "campus_walkway"),
    ("path_north", "business_entrance", "campus_walkway"),
    ("playground_entrance", "path_southeast", "campus_walkway"),
]


def build_edge_seed(from_node, to_node, path_type):
    distance_meters = round(
        dist(
            (from_node["x"], from_node["y"], from_node["z"]),
            (to_node["x"], to_node["y"], to_node["z"]),
        ),
        2,
    )
    return {
        "distance_meters": distance_meters,
        "base_minutes": round(distance_meters / WALKING_BASE_METERS_PER_MINUTE, 3),
        "bidirectional": True,
        "status": "open",
        "congestion_factor": 1.0,
        "weather_factor": 1.0,
        "properties": {
            "path_type": path_type,
            "accessible": True,
            "risk_level": "low",
        },
    }
