# Order Fulfillment & Delivery Promise Engine

## 1. Project Overview

This project simulates an e-commerce fulfillment workflow using deterministic synthetic data. It evaluates inventory availability, warehouse capacity, carrier serviceability, carrier cutoff times, shipping calendars, and delivery service levels to allocate orders and calculate delivery promises.

## 2. Database Design Principles

- Every entity must have a primary key.
- Every relationship must use a valid foreign key where applicable.
- Many-to-many relationships must use bridge tables.
- Event history must be preserved rather than overwritten.
- Derived values must be calculated from source records and documented business rules.
- Deliberately injected anomalies must be labelled separately in ground-truth data.
- The data generator must support a fixed random seed and configurable dataset sizes.

## 3. Core Entities

1. Order
2. OrderLine
3. SKU
4. FulfillmentNode
5. Inventory
6. WarehouseCapacity
7. Carrier
8. ServiceLevel
9. Shipment
10. TrackingEvent
11. DeliveryPromise

## 4. Supporting Entities

The implementation may also use supporting tables for:

- Order allocations and shipment-line allocations
- Carrier operating calendars and cutoff times
- Holidays
- Carrier service-zone eligibility
- Shipment status history
- Validation results and anomaly ground truth

## 5. Initial Business Rules

1. An order contains one or more order lines.
2. Each order line references a valid SKU.
3. Inventory is tracked by SKU and fulfillment node.
4. Allocations must respect available inventory and warehouse capacity.
5. Carrier and service-level combinations must support the destination zone.
6. Delivery promises must be calculated using documented processing times, cutoffs, holidays, calendars, and transit rules.
7. Split shipments are allowed when a single node cannot fulfill an order and a valid multi-node allocation is possible.
8. An order is fully delivered only when all its required quantities have been delivered.
9. Tracking events must preserve their original timestamps and history.
10. Known injected anomalies must be recorded separately from input features.

## 6. Identifier Conventions

- Orders: ORD-2026-000001
- Fulfillment nodes: FUL-2026-000001
- Shipments: SHP-2026-000001
- Tracking events: TRK-<shipment-id>-001
- Delivery promises: PROM-<order-id>-01

Identifiers are immutable and must be consistent across tables and exported files.

## 7. Reproducibility

The default synthetic-data seed is 20261022. Dataset sizes must be configurable so the same generator can produce starter and full datasets.

## 8. Validation Goals

- Primary-key uniqueness
- Foreign-key integrity
- Valid enumerated values
- Inventory and capacity reconciliation
- Valid date ordering and lifecycle transitions
- Correct delivery-promise calculations
- Correct order-level status for split shipments
- Reproducible outputs and checksums.