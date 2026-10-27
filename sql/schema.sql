
-- Order Fulfillment & Delivery Promise Engine
PRAGMA foreign_keys = ON;

-- 1. Product master
CREATE TABLE IF NOT EXISTS skus (
    sku_id TEXT PRIMARY KEY,
    sku_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_weight_kg REAL NOT NULL CHECK (unit_weight_kg > 0),
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1))
);

-- 2. Fulfillment node master
CREATE TABLE IF NOT EXISTS fulfillment_nodes (
    node_id TEXT PRIMARY KEY,
    node_name TEXT NOT NULL,
    city TEXT NOT NULL,
    service_zone TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1))
);

-- 3. Carrier master
CREATE TABLE IF NOT EXISTS carriers (
    carrier_id TEXT PRIMARY KEY,
    carrier_name TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1))
);

-- Step 6: Orders and order lines

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    order_timestamp TEXT NOT NULL,
    destination_city TEXT NOT NULL,
    destination_zone TEXT NOT NULL,

    order_status TEXT NOT NULL DEFAULT 'CREATED'
        CHECK (
            order_status IN (
                'CREATED',
                'ALLOCATED',
                'PARTIALLY_SHIPPED',
                'SHIPPED',
                'PARTIALLY_DELIVERED',
                'DELIVERED',
                'CANCELLED',
                'EXCEPTION'
            )
        ),

    created_at TEXT NOT NULL,

    CHECK (length(order_id) > 0)
);

CREATE TABLE IF NOT EXISTS order_lines (
    order_line_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    sku_id TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),

    FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    FOREIGN KEY (sku_id)
        REFERENCES skus(sku_id),

    UNIQUE (order_id, sku_id)
);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    sku_id TEXT NOT NULL,
    available_quantity INTEGER NOT NULL DEFAULT 0
        CHECK (available_quantity >= 0),
    reserved_quantity INTEGER NOT NULL DEFAULT 0
        CHECK (reserved_quantity >= 0),
    updated_at TEXT NOT NULL,

    FOREIGN KEY (node_id)
        REFERENCES fulfillment_nodes(node_id),

    FOREIGN KEY (sku_id)
        REFERENCES skus(sku_id),

    UNIQUE (node_id, sku_id),

    CHECK (reserved_quantity <= available_quantity)
);

CREATE TABLE IF NOT EXISTS warehouse_capacity (
    capacity_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    capacity_date TEXT NOT NULL,
    max_order_lines INTEGER NOT NULL
        CHECK (max_order_lines >= 0),
    used_order_lines INTEGER NOT NULL DEFAULT 0
        CHECK (used_order_lines >= 0),
    max_units INTEGER NOT NULL
        CHECK (max_units >= 0),
    used_units INTEGER NOT NULL DEFAULT 0
        CHECK (used_units >= 0),

    FOREIGN KEY (node_id)
        REFERENCES fulfillment_nodes(node_id),

    UNIQUE (node_id, capacity_date),

    CHECK (used_order_lines <= max_order_lines),
    CHECK (used_units <= max_units)
);

CREATE TABLE IF NOT EXISTS service_levels (
    service_level_id TEXT PRIMARY KEY,
    service_name TEXT NOT NULL UNIQUE,
    transit_days INTEGER NOT NULL CHECK (transit_days >= 0),
    cutoff_time TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS carrier_service_zones (
    carrier_service_zone_id TEXT PRIMARY KEY,
    carrier_id TEXT NOT NULL,
    service_level_id TEXT NOT NULL,
    service_zone TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),

    FOREIGN KEY (carrier_id)
        REFERENCES carriers(carrier_id),

    FOREIGN KEY (service_level_id)
        REFERENCES service_levels(service_level_id),

    UNIQUE (carrier_id, service_level_id, service_zone)
);

CREATE TABLE IF NOT EXISTS shipments (
    shipment_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    carrier_id TEXT NOT NULL,
    service_level_id TEXT NOT NULL,
    shipment_status TEXT NOT NULL DEFAULT 'CREATED'
        CHECK (shipment_status IN (
            'CREATED',
            'ALLOCATED',
            'DISPATCHED',
            'IN_TRANSIT',
            'OUT_FOR_DELIVERY',
            'DELIVERED',
            'EXCEPTION',
            'CANCELLED'
        )),
    created_at TEXT NOT NULL,
    dispatched_at TEXT,
    delivered_at TEXT,

    FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    FOREIGN KEY (node_id)
        REFERENCES fulfillment_nodes(node_id),

    FOREIGN KEY (carrier_id)
        REFERENCES carriers(carrier_id),

    FOREIGN KEY (service_level_id)
        REFERENCES service_levels(service_level_id),

    CHECK (
        delivered_at IS NULL
        OR dispatched_at IS NOT NULL
    ),

    CHECK (
        dispatched_at IS NULL
        OR dispatched_at >= created_at
    ),

    CHECK (
        delivered_at IS NULL
        OR delivered_at >= dispatched_at
    )
);
--shipment
CREATE TABLE IF NOT EXISTS shipment_lines (
    shipment_line_id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL,
    order_line_id TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),

    FOREIGN KEY (shipment_id)
        REFERENCES shipments(shipment_id),

    FOREIGN KEY (order_line_id)
        REFERENCES order_lines(order_line_id),

    UNIQUE (shipment_id, order_line_id)
);
--Tracking

CREATE TABLE IF NOT EXISTS tracking_events (
    tracking_event_id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL,
    event_sequence INTEGER NOT NULL CHECK (event_sequence > 0),
    event_type TEXT NOT NULL
        CHECK (event_type IN (
            'CREATED',
            'ALLOCATED',
            'DISPATCHED',
            'IN_TRANSIT',
            'OUT_FOR_DELIVERY',
            'DELIVERED',
            'EXCEPTION',
            'CANCELLED'
        )),
    event_timestamp TEXT NOT NULL,
    event_location TEXT,
    event_notes TEXT,

    FOREIGN KEY (shipment_id)
        REFERENCES shipments(shipment_id),

    UNIQUE (shipment_id, event_sequence)
);
--Delivery Promise

CREATE TABLE IF NOT EXISTS delivery_promises (
    promise_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    promise_version INTEGER NOT NULL DEFAULT 1
        CHECK (promise_version > 0),
    promised_delivery_start TEXT NOT NULL,
    promised_delivery_end TEXT NOT NULL,
    promise_created_at TEXT NOT NULL,
    promise_status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (promise_status IN (
            'ACTIVE',
            'SUPERSEDED',
            'FULFILLED',
            'BREACHED',
            'CANCELLED'
        )),

    FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    UNIQUE (order_id, promise_version),

    CHECK (
        promised_delivery_end >= promised_delivery_start
    )
);
