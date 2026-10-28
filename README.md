# Order Fulfillment & Delivery Promise Engine

A Python and SQLite assessment project that models inventory-aware order allocation, fulfillment-node selection, carrier serviceability, delivery promises, shipment lifecycle events, delivery outcomes, and anomaly validation.

**Repository:** https://github.com/anithaanu2003/order-fulfillment-engine/tree/master

## 1. Problem Statement

Order fulfillment requires more than selecting a warehouse with available stock. A reliable system must consider unreserved inventory, warehouse capacity, destination service zones, carrier cutoffs, transit times, holidays, and carrier operating calendars.

This project implements these business rules and generates a synthetic dataset for testing relational integrity, allocation decisions, delivery promises, shipment histories, and anomalous operational records.

The project is designed to make business decisions traceable and validation results reproducible.

## 2. Verified Project Snapshot

The committed dataset was exported from `final_assessment_v2.db` using the fixed seed configuration `20261022`.

| Metric | Verified result |
|---|---:|
| Orders | 50,000 |
| Order lines | 100,104 |
| Fulfillment nodes | 20 |
| Carriers | 10 |
| SKUs | 5 |
| Allocated orders processed | 20,000 |
| Delivery promises | 20,000 |
| Shipments | 36,374 |
| Shipment lines | 39,818 |
| Tracking events | 174,607 |
| Carrier scans | 36,374 |
| Exported database tables | 16 |
| Total rows across exported tables | 462,018 |

These figures describe the committed dataset snapshot, not a claim that every order has been fulfilled.

### Allocation coverage limitation

The allocation batch processed 20,000 orders. The remaining 30,000 orders are still in the `CREATED` state and have not been allocated in this snapshot. This is an important limitation when interpreting fulfillment coverage and delivery outcomes.

The tracking-event count exceeds the original target of 100,000. A higher event count alone does not establish complete end-to-end fulfillment, so event validity and shipment outcomes must be considered separately.

## 3. Technology Stack

- Python
- SQLite
- pytest
- SQL
- CSV and JSON
- Git and GitHub

The implementation was developed and tested in a Windows environment using Python 3.13.

## 4. Data Model

The relational schema is maintained in `sql/schema.sql`.

The dataset includes 16 tables:

- `skus` — product identifiers and attributes
- `fulfillment_nodes` — fulfillment locations and service zones
- `carriers` — carrier records and active status
- `orders` — order timestamps, destinations, and status
- `order_lines` — SKU quantities and prices
- `inventory` — available and reserved stock
- `warehouse_capacity` — daily warehouse capacity
- `service_levels` — service-level and transit-time information
- `carrier_service_zones` — carrier-service availability by zone
- `shipments` — fulfillment and shipment status
- `shipment_lines` — quantities assigned to each shipment
- `delivery_promises` — promised delivery information
- `tracking_events` — shipment lifecycle history
- `carrier_scans` — carrier scan records
- `holidays` — non-operating dates
- `carrier_calendars` — carrier operating dates and cutoffs

## 5. Business Rules and Design Decisions

### Inventory and allocation

- Allocation considers unreserved inventory.
- Allocations must not exceed available stock.
- Orders may be split across multiple fulfillment nodes.
- Shipment-line quantities must remain consistent with allocated order-line quantities.
- Allocation must respect warehouse capacity.
- Persistence operations use transaction boundaries to prevent partial updates.

### Carrier selection and delivery promises

- The selected carrier service must support the destination zone.
- Delivery promises account for service cutoffs, transit duration, business days, holidays, and carrier calendars.
- Promise records preserve relevant delivery commitments and versions.

### Shipment lifecycle

- Tracking events are appended to shipment histories.
- Event sequences must increase within each shipment.
- Timestamps must follow valid chronology.
- Delivery must not precede dispatch.
- Shipment status must agree with the latest recorded lifecycle event.

### Why these rules matter

Separating inventory, capacity, carrier serviceability, and delivery timing makes allocation decisions easier to test and explain. Transactional persistence helps preserve consistency when allocation cannot be completed. Append-only tracking history provides a record of shipment progress rather than replacing previous events.

## 6. Anomaly Scenarios and Ground Truth

The anomaly dataset is stored separately from the normal operational export in `data/anomaly_cases/`.

It includes five scenarios:

| Scenario | Validation objective |
|---|---|
| Promise before order | Detect invalid promise chronology |
| Allocation exceeds inventory | Detect over-allocation |
| Unsupported carrier zone | Detect an invalid carrier-service combination |
| Delivered before dispatch | Detect invalid lifecycle chronology |
| Incorrect split-shipment rollup | Detect inconsistent shipment totals |

The files are:

- `scenario_inputs.csv` — scenario input features
- `ground_truth.csv` — expected labels and validation outcomes
- `anomaly_cases.json` — structured scenario definitions

Separating ground-truth labels from scenario inputs helps prevent target leakage when these examples are used for downstream analysis.

**Anomaly validation result:** all five scenarios passed the project validator, and the scenario IDs matched their ground-truth labels.

## 7. Exported Deliverables

The final export is located at:

`exports/final_assessment_v2_corrected/`

It contains:

- CSV and JSON exports for the 16 database tables
- `manifest.json` — exported file checksums and row counts
- `source_manifest.json` — source information and artifact checksums
- `seed.sql` — SQL database dump
- `data_dictionary.csv` — table and column metadata
- `validation_summary.json` — validation results and dataset counts

The SQL dump is approximately 64 MB. It is included as a full seed snapshot; GitHub has warned that it exceeds its recommended 50 MB file size.

## 8. Installation

Run the following commands from the repository root in PowerShell.

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

The repository includes database initialization and data preparation scripts under `src/`. Use a fresh, isolated database for data generation and follow the relevant script options before running database-mutating commands.

**Important:** Do not treat a previously populated operational database as a clean reproducibility environment. The committed export is the validated snapshot used for this submission.

## 9. Run the Tests

From the repository root:

```powershell
python -m pytest -q
```

**Recorded result:** 155 tests passed, with 5 subtests passed.

## 10. Verify the Anomaly Dataset

Run:

```powershell
python .\src\validate_anomaly_cases.py
```

The recorded validation confirmed:

- Five input scenarios
- Five ground-truth labels
- Read-only access to the operational database
- Matching scenario identifiers and ground-truth records
- Successful validation of all five scenarios

## 11. Verify the Export

Run:

```powershell
python .\src\verify_export.py .\exports\final_assessment_v2_corrected
```

The recorded verification result was:

- 16 tables checked
- 32 CSV/JSON files checked
- 462,018 rows recorded in the export manifest
- File checksums and row counts matched

The finalization script also reported zero foreign-key violations and zero shipment-status/latest-event mismatches.

These are recorded results for the committed snapshot. Re-run the commands after changing the dataset or code.

## 12. Reproducibility

The project uses the fixed seed `20261022` for synthetic data generation and anomaly scenario creation.

A full reproducibility assessment should use a clean, isolated database, generate the dataset twice, and compare table counts, output checksums, lifecycle validity, allocation results, and anomaly labels.

The exported snapshot has been verified against its manifest. A complete independent, clean-environment regeneration of the entire final dataset has not been established by the checks reported here.

## 13. Limitations and Next Steps

The current snapshot has the following limitations:

1. Only 20,000 of the 50,000 orders were processed by the allocation batch.
2. The remaining 30,000 orders are still `CREATED`.
3. Allocation and delivery coverage should be expanded before claiming complete fulfillment across all orders.
4. Full dataset regeneration should be automated and tested from a clean environment.
5. Repeated-run reproducibility should be demonstrated by comparing independently generated datasets.

These limitations are disclosed so reviewers can distinguish implemented functionality from verified end-to-end coverage.

## 14. AI-Assisted Development Disclosure

AI-assisted tools were used for technical clarification, debugging support, test development, and documentation refinement.

Project behavior was checked through local execution, SQL queries, automated tests, anomaly validation, and export verification. The final dataset was checked for foreign-key violations and shipment-status consistency.


## 15. Submission and Walkthrough

**Public repository:**  
https://github.com/anithaanu2003/order-fulfillment-engine/tree/master

Suggested walkthrough:

1. Explain the fulfillment problem and the data model.
2. Demonstrate how inventory and capacity affect allocation.
3. Explain carrier serviceability and delivery-promise calculations.
4. Walk through shipment lifecycle validation.
5. Demonstrate the five anomaly scenarios and their separate ground truth.
6. Run the automated tests and export verifier.
7. Discuss the allocation coverage limitation, reproducibility approach, and future improvements.

The goal is to make the implementation, assumptions, validation evidence, and limitations understandable to another engineer.
