# Order Fulfillment & Delivery Promise Engine

## 1. Project Overview

The Order Fulfillment & Delivery Promise Engine is a Python-based data engineering and business-rules project that models order allocation, inventory availability, warehouse capacity, carrier serviceability, delivery promises, shipment tracking, and delivery outcomes.

The assessment focuses on generating a large, reproducible synthetic dataset, enforcing relational integrity and business rules, simulating realistic fulfillment scenarios, validating anomalous records, and exporting data in reusable formats.

The project uses Python, SQLite, pytest, and deterministic data-generation techniques.

## 2. Assessment Objectives

The implementation is designed to address the following requirements:

- Generate a synthetic dataset with 50,000 orders.
- Model 20 fulfillment nodes, 10 carriers, inventory, warehouse capacity, carrier-service zones, service levels, and operating calendars.
- Generate order lines and shipment records with valid primary-key and foreign-key relationships.
- Support split shipments when an order is fulfilled by multiple nodes.
- Calculate delivery promises using service cutoffs, transit times, business days, holidays, and carrier operating calendars.
- Generate chronological shipment tracking events and delivery outcomes using documented lifecycle rules.
- Introduce labelled anomalous scenarios separately from the normal operational dataset.
- Validate data integrity, arithmetic consistency, event sequences, and anomaly classifications.
- Export tables to CSV and JSON, with checksums and row counts recorded in a manifest.
- Verify deterministic output using a fixed random seed and repeat-run comparisons.

**Target scale:** 50,000 orders, 20 fulfillment nodes, 10 carriers, and 100,000 tracking events.

The targets describe the assessment goals; final completion must be confirmed through the validation scripts and generated dataset.

## 3. Technology Stack

- Python 3.11+
- SQLite
- pytest
- CSV and JSON
- Git and GitHub
- PowerShell or another terminal

The project has been developed locally using Python 3.13.

## 4. Data Model

The relational schema is maintained in `sql/schema.sql`.

The principal entities are:

- **Product master:** SKUs and product attributes.
- **Fulfillment nodes:** Warehouses, cities, and service zones.
- **Carrier master:** Carrier identities and active status.
- **Orders and order lines:** Order timestamps, destinations, products, quantities, and prices.
- **Inventory:** Available and reserved quantities by node and SKU.
- **Warehouse capacity:** Daily order-line and unit limits.
- **Service levels:** Transit durations and cutoff times.
- **Carrier-service zones:** Supported carrier, service-level, and destination-zone combinations.
- **Shipments and shipment lines:** Shipment allocation and quantities fulfilled from each node.
- **Tracking events:** Append-only shipment lifecycle history.
- **Delivery promises:** Promised delivery windows and promise versions.
- **Carrier scans:** Detailed carrier scan history.
- **Holiday calendars:** Global, regional, and node-specific non-operating dates.
- **Carrier operating calendars:** Carrier operating dates and cutoff information.

## 5. Business Rules

### Inventory and allocation

- Unreserved inventory is calculated from available and reserved quantities.
- Allocations must not exceed the available unreserved stock.
- Order-line quantities must be fulfilled consistently across allocated shipment lines.
- An order may be split across multiple fulfillment nodes when permitted by inventory and capacity.
- Failed persistence operations must roll back partial changes.

### Warehouse capacity

- Allocation must respect daily order-line and unit limits.
- Capacity usage must be recorded against the relevant fulfillment date.
- Capacity records must exist for the applicable node and date.

### Carrier selection and delivery promises

- The selected carrier service must be active and support the destination zone.
- Delivery promises must respect cutoff times, transit duration, business days, holidays, and carrier operating calendars.
- Promise versions and status changes must preserve historical records.

### Shipment lifecycle

- Tracking events must follow permitted lifecycle transitions.
- Event timestamps must be chronological for each shipment.
- Event sequences must be unique and increasing within each shipment.
- Delivery must not occur before dispatch.
- Shipment and order statuses must remain consistent with recorded outcomes.
- Tracking history must be preserved rather than overwritten.

## 6. Synthetic Data Generation

The project includes scripts for generating and preparing master data, orders, order lines, inventory, warehouse capacity, carrier-service mappings, holiday calendars, and carrier operating calendars.

The target configuration uses the fixed seed `20261022` for reproducibility.

A complete generation workflow must support:

1. Initializing a fresh database.
2. Creating master data.
3. Generating orders and order lines.
4. Preparing inventory and capacity.
5. Configuring carrier services and operating calendars.
6. Allocating eligible orders.
7. Generating shipments, tracking events, and delivery outcomes.
8. Validating and exporting the resulting dataset.

Generation must be repeatable from a clean environment. A populated operational database must not be assumed to produce identical output when generation scripts are rerun.

## 7. Shipment Events and Delivery Outcomes

Shipment tracking histories are designed to represent realistic operational progress, such as:

`CREATED → DISPATCHED → IN_TRANSIT → OUT_FOR_DELIVERY → DELIVERED`

Exceptions may occur where permitted by the lifecycle rules, followed by valid recovery transitions when applicable.

The event generator must use documented rules for event ordering, timestamp progression, shipment status updates, and delivery outcomes. It must not create arbitrary events merely to reach the target count.

The assessment target is 100,000 tracking events. Completion must be verified using actual generated records and lifecycle validation.

## 8. Anomaly Scenarios and Ground Truth

Anomalous examples are maintained separately from normal operational inputs.

The implemented scenario set covers:

| Scenario | Expected validation |
|---|---|
| Promise before order | Reject invalid promise chronology |
| Allocation exceeds inventory | Reject invalid allocation quantity |
| Carrier unsupported for zone | Reject unsupported carrier-service combination |
| Delivered before dispatch | Flag invalid lifecycle chronology |
| Incorrect split-shipment rollup | Flag mismatch between shipment quantities and reported total |

Each scenario has a unique identifier, input fields, an expected anomaly label, and an expected validation decision.

The anomaly labels and expected decisions must remain separate from operational input features to avoid data leakage during downstream analysis.

The anomaly generator and validator are tested for deterministic output and scenario consistency.

## 9. Data Validation

Validation covers the following areas.

### Relational integrity

- Primary-key uniqueness.
- Foreign-key integrity.
- Required fields and valid enumerated values.
- Duplicate business records where uniqueness is required.

### Arithmetic and operational rules

- Inventory availability and reservation limits.
- Warehouse capacity constraints.
- Order-line and shipment-line quantities.
- Split-shipment totals and order-level rollups.
- Carrier-serviceability by destination zone.

### Temporal integrity

- Valid order and promise chronology.
- Dispatch before delivery.
- Chronological tracking-event timestamps.
- Valid lifecycle transitions and event sequences.
- Applicable holidays and carrier operating dates.

### Reproducibility

- Fixed random seed.
- Repeat-run comparison of generated files.
- CSV and JSON row-count verification.
- SHA-256 checksum verification through the export manifest.

## 10. Export Deliverables

The export workflow supports CSV and JSON representations of database tables.

Each export snapshot includes a `manifest.json` file recording table row counts and file checksums.

The assessment deliverables should include:

- CSV exports.
- JSON exports.
- SQL schema and seed data.
- Data dictionary.
- Dataset manifest and source information.
- Validation summary.
- Anomaly scenario inputs.
- Separate anomaly ground-truth labels.
- Reproduction instructions and fixed-seed configuration.

Exports should be written to a new or empty output directory so that existing snapshots are preserved. The export verifier must confirm file integrity and recorded row counts.

## 11. Project Structure

```text
order-fulfillment-engine/
├── src/
│   ├── init_db.py
│   ├── generate_orders.py
│   ├── generate_order_lines.py
│   ├── seed_master_data.py
│   ├── seed_inventory.py
│   ├── seed_capacity.py
│   ├── seed_carrier_services.py
│   ├── seed_calendars.py
│   ├── allocate_orders.py
│   ├── persist_allocations.py
│   ├── calculate_delivery_promise.py
│   ├── calculate_delivery_promise_from_db.py
│   ├── shipment_lifecycle.py
│   ├── generate_tracking_events.py
│   ├── generate_carrier_scans.py
│   ├── generate_anomaly_cases.py
│   ├── validate_anomaly_cases.py
│   ├── export_dataset.py
│   └── verify_export.py
├── tests/
├── data/
│   └── anomaly_cases/
├── exports/
├── docs/
├── sql/
│   └── schema.sql
├── requirements.txt
└── README.md
```

The directory listing above highlights key components; additional source and test files may be present.

## 12. Installation and Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Initialize the database:

```powershell
python -m src.init_db
```

**Important:** Run data-seeding and allocation commands only against a fresh or intentionally prepared database. The existing operational database contains records and should not be treated as a clean starting point.

## 13. Testing

Run the automated test suite from the project root:

```powershell
python -m pytest -v
```

Additional validation commands include:

```powershell
python -m src.validate_anomaly_cases
python -m src.verify_export exports/calendar_snapshot
```

The export path above refers to an existing snapshot. Use the appropriate output directory for any newly generated dataset.

The test suite has previously reported 152 passing tests. Re-run the full suite against the final submission before reporting the final result.

## 14. Reproducibility and Execution

A complete reproducibility check should:

1. Start with a clean, isolated database.
2. Use the documented seed and generation configuration.
3. Generate the same dataset twice in separate clean environments.
4. Compare record counts and output checksums.
5. Verify relational integrity and business rules after each run.
6. Confirm that anomaly labels and expected decisions are unchanged.

The final README should identify the exact commands used to generate the final dataset and reproduce the validation results.

## 15. Current Limitations and Completion Criteria

The project contains implemented database, allocation, delivery-promise, calendar, lifecycle, anomaly, and export components. However, the presence of individual components does not establish that the full assessment has been completed end to end.

Before final submission, verify:

- The full 50,000-order dataset.
- The 20-node and 10-carrier targets.
- The 100,000-event target with valid lifecycle histories.
- Complete delivery outcomes and split-shipment consistency.
- Reproducibility from a clean database.
- CSV, JSON, and SQL deliverables.
- Data dictionary, manifest, and validation summary.
- Zero unexpected foreign-key violations.
- Successful full test-suite execution.
- Separate and validated anomaly ground truth.

Only verified results should be described as completed.

## 16. Development Workflow and Tooling

The project was developed incrementally through database design, synthetic data preparation, business-rule implementation, persistence, lifecycle validation, testing, and debugging.

AI-assisted tools were used for technical clarification and troubleshooting. Code and data behavior were checked through local execution, SQL queries, and automated tests.

## 17. Repository

GitHub: https://github.com/anithaanu2003/order-fulfillment-engine
