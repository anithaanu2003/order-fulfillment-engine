# Order Fulfillment & Delivery Promise Engine

A Python-based order fulfillment system that models inventory availability, warehouse capacity, carrier serviceability, shipment lifecycle events, and delivery promise calculations.

## 1. Project Overview

The Order Fulfillment & Delivery Promise Engine models how customer orders can be allocated to fulfillment nodes while considering stock availability, warehouse processing capacity, supported carrier services, and delivery timelines.

The project uses SQLite for relational data storage and Python for business logic, data generation, validation, and shipment lifecycle management.

## 2. Key Features

- **Relational database:** Structured entities with primary keys, foreign keys, uniqueness constraints, and validation checks.
- **Synthetic data generation:** Scripts for master data, inventory, warehouse capacity, carrier-service mappings, orders, and order lines.
- **Inventory-aware allocation:** Checks unreserved stock before allocating order lines.
- **Warehouse capacity validation:** Considers order-line and unit capacity during allocation.
- **Carrier-service selection:** Identifies active carrier services supporting the destination zone.
- **Delivery promise calculation:** Accounts for service cutoffs, business days, and configured holidays.
- **Shipment persistence:** Stores shipments, shipment lines, tracking events, and delivery promises.
- **Lifecycle validation:** Checks permitted shipment transitions and chronological event ordering.
- **Automated testing:** Uses pytest to test business rules, edge cases, and persistence behavior.

## 3. Technology Stack

- Python
- SQLite
- pytest
- Git and GitHub

## 4. Project Structure

```text
order-fulfillment-engine/
├── src/
│   ├── init_db.py
│   ├── generate_orders.py
│   ├── seed_master_data.py
│   ├── seed_inventory.py
│   ├── seed_capacity.py
│   ├── seed_carrier_services.py
│   ├── allocate_orders.py
│   ├── load_allocation_data.py
│   ├── select_carrier_service.py
│   ├── calculate_delivery_promise.py
│   ├── persist_allocations.py
│   └── shipment_lifecycle.py
├── tests/
├── data/
├── docs/
├── sql/
│   └── schema.sql
├── check_counts.py
├── requirements.txt
└── README.md
```

## 5. Prerequisites

- Python 3.11 or later
- Git
- PowerShell or another terminal

The project has been developed locally using Python 3.13.

## 6. Installation and Setup

Clone the repository:

```powershell
git clone https://github.com/anithaanu2003/order-fulfillment-engine.git
cd order-fulfillment-engine
```

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

## 7. Generating the Dataset

Run the supporting data scripts in order:

```powershell
python -m src.seed_master_data
python -m src.seed_inventory
python -m src.seed_capacity
python -m src.seed_carrier_services
```

Generate orders:

```powershell
python -m src.generate_orders
```

The order generator targets 50,000 orders and adds the number required based on the current database count.

**Note:** For a reproducible fresh run, start with a clean database and follow the documented generation sequence. Re-running seed scripts against a populated database may preserve existing records, so identical output should be verified rather than assumed.

## 8. Running the Tests

Run the test suite from the project root:

```powershell
python -m pytest -v
```

During development, the test suite reported 130 passing tests and 2 passing subtests. Re-run the suite against the final submitted commit to confirm the current results.

## 9. Data Model

The database models the following entities:

- SKUs
- Fulfillment nodes
- Orders and order lines
- Inventory
- Warehouse capacity
- Carriers and service levels
- Carrier-service-zone mappings
- Shipments and shipment lines
- Tracking events
- Delivery promises

The schema is maintained in `sql/schema.sql`. The SQLite database is created locally and is not committed to the repository.

## 10. Business Rules

- Unreserved inventory is calculated as available quantity minus reserved quantity.
- An order line requires sufficient unreserved stock to be allocated.
- Warehouse capacity must be sufficient for the requested order lines and units.
- Different lines in an order may be allocated to different fulfillment nodes.
- Carrier services must be active and support the destination zone.
- Delivery promises account for service cutoffs and business-day calculations.
- Shipment events must follow permitted lifecycle transitions and chronological ordering.
- Failed allocation operations should not leave partial reservations or partially persisted records.

## 11. Validation and Limitations

Validation includes automated tests for allocation logic, delivery-date calculations, shipment lifecycle rules, and database persistence.

Database integrity can be checked by verifying record counts and foreign-key constraints.

Areas requiring additional verification before final submission include:

- End-to-end processing of the complete 50,000-order dataset.
- Capacity selection based on the relevant order date.
- Reproducible generation from a clean database.
- Required CSV/JSON exports and a separate ground-truth dataset.
- Explicit anomaly injection and validation of anomaly labels.
- Complete execution instructions for the full assignment workflow.

Only features that have been implemented and verified should be considered complete.

## 12. Development Workflow

The project was developed incrementally, starting with database design and data preparation, followed by business logic, shipment lifecycle management, and testing.

The development process included:

1. **Database design:** Defined entities, relationships, primary keys, foreign keys, and database constraints.
2. **Data preparation:** Created scripts to populate master data, inventory, warehouse capacity, carrier services, orders, and order lines.
3. **Business logic:** Implemented inventory checks, fulfillment-node selection, warehouse capacity validation, and delivery promise calculations.
4. **Shipment management:** Added shipment persistence and validation of tracking-event sequences and lifecycle transitions.
5. **Testing and debugging:** Executed automated tests, inspected database records, investigated errors, and refined the implementation based on test results.
6. **Version control:** Maintained the code in a public GitHub repository and tracked changes through Git commits.

### Use of Development Tools

AI-assisted tools were used occasionally for technical clarification, troubleshooting errors, and exploring implementation approaches. The project was run and tested locally, with database queries and automated tests used to check the behavior of implemented features.

### Example Prompts

Examples of technical questions used during development include:

- "How should primary keys and foreign keys be structured for an order fulfillment database?"
- "How can I validate available inventory and warehouse capacity before allocating an order?"
- "How can I test that shipment tracking events follow valid chronological transitions?"
- "What could cause a database persistence test to fail, and how can I investigate it?"
- "How can I verify database record counts and foreign-key integrity?"

## 13. Repository

GitHub: https://github.com/anithaanu2003/order-fulfillment-engine
