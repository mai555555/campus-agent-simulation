VALID_LOCATIONS = {
    "宿舍区",
    "教学楼",
    "图书馆",
    "食堂",
    "操场",
    "商业街",
    "校务处",
}


def get_current_day(conn):
    row = conn.execute(
        "SELECT value FROM simulation_state WHERE key = 'current_day'"
    ).fetchone()
    return int(row["value"]) if row else 1


def get_resident(conn, resident_id):
    return conn.execute(
        """
        SELECT id, name, role, personality, goal, money, location
        FROM residents
        WHERE id = ?
        """,
        (resident_id,),
    ).fetchone()


def add_event(conn, day, event_type, description):
    conn.execute(
        """
        INSERT INTO city_events (day, event_type, description)
        VALUES (?, ?, ?)
        """,
        (day, event_type, description),
    )


def add_memory(conn, resident_id, day, content, importance=1):
    conn.execute(
        """
        INSERT INTO memories (resident_id, day, content, importance)
        VALUES (?, ?, ?, ?)
        """,
        (resident_id, day, content, importance),
    )


def change_relationship(conn, from_id, to_id, delta, note):
    conn.execute(
        """
        INSERT INTO relationships (from_resident_id, to_resident_id, score, notes)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(from_resident_id, to_resident_id)
        DO UPDATE SET
            score = score + excluded.score,
            notes = CASE
                WHEN relationships.notes = '' THEN excluded.notes
                ELSE relationships.notes || '; ' || excluded.notes
            END
        """,
        (from_id, to_id, delta, note),
    )


def get_inventory_quantity(conn, resident_id, item_name):
    row = conn.execute(
        """
        SELECT quantity FROM inventory
        WHERE resident_id = ? AND item_name = ?
        """,
        (resident_id, item_name),
    ).fetchone()
    return int(row["quantity"]) if row else 0


def add_inventory(conn, resident_id, item_name, quantity):
    conn.execute(
        """
        INSERT INTO inventory (resident_id, item_name, quantity)
        VALUES (?, ?, ?)
        ON CONFLICT(resident_id, item_name)
        DO UPDATE SET quantity = quantity + excluded.quantity
        """,
        (resident_id, item_name, quantity),
    )


def move_resident(conn, resident_id, destination):
    resident = get_resident(conn, resident_id)
    if not resident:
        raise ValueError("找不到这个 Agent")
    if destination not in VALID_LOCATIONS:
        raise ValueError("地点不存在")

    day = get_current_day(conn)
    conn.execute(
        "UPDATE residents SET location = ? WHERE id = ?",
        (destination, resident_id),
    )
    description = f"{resident['name']} 从 {resident['location']} 移动到 {destination}。"
    add_event(conn, day, "agent_move", description)
    add_memory(conn, resident_id, day, description, importance=2)
    conn.commit()
    return {"message": "移动成功", "description": description}


def chat_between(conn, speaker_id, listener_id, message):
    speaker = get_resident(conn, speaker_id)
    listener = get_resident(conn, listener_id)
    if not speaker or not listener:
        raise ValueError("找不到聊天对象")

    day = get_current_day(conn)
    description = f"{speaker['name']} 对 {listener['name']} 说：{message}"
    add_event(conn, day, "agent_chat", description)
    add_memory(conn, speaker_id, day, description, importance=2)
    add_memory(conn, listener_id, day, description, importance=2)
    change_relationship(conn, speaker_id, listener_id, 2, "校园交流增加熟悉度")
    change_relationship(conn, listener_id, speaker_id, 1, "收到对方交流")
    conn.commit()
    return {"message": "聊天成功", "description": description}


def buy_sell(conn, buyer_id, seller_id, item_name, quantity, unit_price):
    buyer = get_resident(conn, buyer_id)
    seller = get_resident(conn, seller_id)
    if not buyer or not seller:
        raise ValueError("找不到买家或卖家")
    if quantity <= 0 or unit_price <= 0:
        raise ValueError("数量和单价必须大于 0")

    total_price = quantity * unit_price
    if int(buyer["money"]) < total_price:
        raise ValueError("买家余额不足")

    stock = get_inventory_quantity(conn, seller_id, item_name)
    if stock < quantity:
        raise ValueError("卖家库存不足")

    day = get_current_day(conn)
    conn.execute("UPDATE residents SET money = money - ? WHERE id = ?", (total_price, buyer_id))
    conn.execute("UPDATE residents SET money = money + ? WHERE id = ?", (total_price, seller_id))
    add_inventory(conn, buyer_id, item_name, quantity)
    add_inventory(conn, seller_id, item_name, -quantity)
    conn.execute(
        """
        INSERT INTO transactions (buyer_id, seller_id, item_name, quantity, unit_price, total_price)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (buyer_id, seller_id, item_name, quantity, unit_price, total_price),
    )
    description = f"{buyer['name']} 向 {seller['name']} 购买 {quantity} 份 {item_name}，总价 {total_price} 校园币。"
    add_event(conn, day, "trade", description)
    add_memory(conn, buyer_id, day, description, importance=2)
    add_memory(conn, seller_id, day, description, importance=2)
    conn.commit()
    return {"message": "交易成功", "description": description}
