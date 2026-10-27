
import unittest


from src.allocate_orders import (
    get_unreserved_quantity,
    can_fulfill_order_line,
    find_fulfillment_node,
    reserve_inventory,
    can_accept_order,
    record_capacity_usage,
    find_eligible_fulfillment_node,
    allocate_order_line,
    allocate_order,
    calculate_order_units,
    calculate_order_line_count,
    validate_order_lines,
)



class TestAllocation(unittest.TestCase):

    def test_calculates_unreserved_stock(self):
        inventory = {
            "available_quantity": 10,
            "reserved_quantity": 2,
        }

        self.assertEqual(get_unreserved_quantity(inventory), 8)

    def test_all_stock_is_reserved(self):
        inventory = {
            "available_quantity": 5,
            "reserved_quantity": 5,
        }

        self.assertEqual(get_unreserved_quantity(inventory), 0)

    def test_rejects_negative_available_quantity(self):
        inventory = {
            "available_quantity": -1,
            "reserved_quantity": 0,
        }

        with self.assertRaises(ValueError):
            get_unreserved_quantity(inventory)

    def test_rejects_negative_reserved_quantity(self):
        inventory = {
            "available_quantity": 10,
            "reserved_quantity": -1,
        }

        with self.assertRaises(ValueError):
            get_unreserved_quantity(inventory)

    def test_rejects_reserved_quantity_above_available(self):
        inventory = {
            "available_quantity": 5,
            "reserved_quantity": 6,
        }

        with self.assertRaises(ValueError):
            get_unreserved_quantity(inventory)
            
    
    def test_can_fulfill_when_stock_is_sufficient(self):
        inventory = {
            "available_quantity": 10,
            "reserved_quantity": 2,
        }

        self.assertTrue(
            can_fulfill_order_line(inventory, 5)
        )

    def test_cannot_fulfill_when_stock_is_insufficient(self):
        inventory = {
            "available_quantity": 10,
            "reserved_quantity": 2,
        }

        self.assertFalse(
            can_fulfill_order_line(inventory, 9)
        )

    def test_rejects_zero_requested_quantity(self):
        inventory = {
            "available_quantity": 10,
            "reserved_quantity": 2,
        }

        with self.assertRaises(ValueError):
            can_fulfill_order_line(inventory, 0)
            
    
    def test_selects_first_warehouse_with_sufficient_stock(self):
        warehouses = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 4,
                "reserved_quantity": 2,
            },
            {
                "node_id": "FUL-2026-000002",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            },
        ]

        result = find_fulfillment_node(
            warehouses, "SKU-000001", 5
        )

        self.assertEqual(result, "FUL-2026-000002")

    def test_returns_none_when_no_warehouse_has_enough_stock(self):
        warehouses = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 4,
                "reserved_quantity": 2,
            }
        ]

        result = find_fulfillment_node(
            warehouses, "SKU-000001", 5
        )

        self.assertIsNone(result)

    def test_ignores_stock_for_a_different_sku(self):
        warehouses = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000002",
                "available_quantity": 100,
                "reserved_quantity": 0,
            }
        ]

        result = find_fulfillment_node(
            warehouses, "SKU-000001", 5
        )

        self.assertIsNone(result)
        
    
    def test_find_warehouse_rejects_zero_quantity(self):
        warehouses = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 0,
            }
        ]

        with self.assertRaises(ValueError):
            find_fulfillment_node(
                warehouses, "SKU-000001", 0
            )
            
    
    def test_selects_warehouse_matching_sku_and_quantity(self):
        warehouses = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 5,
                "reserved_quantity": 2,
            },
            {
                "node_id": "FUL-2026-000002",
                "sku_id": "SKU-000002",
                "available_quantity": 20,
                "reserved_quantity": 0,
            },
            {
                "node_id": "FUL-2026-000003",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 1,
            },
        ]

        result = find_fulfillment_node(
            warehouses, "SKU-000001", 5
        )

        self.assertEqual(result, "FUL-2026-000003")
    
    
    def test_prefers_warehouse_with_less_excess_stock(self):
        warehouses = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 6,
                "reserved_quantity": 0,
            },
            {
                "node_id": "FUL-2026-000002",
                "sku_id": "SKU-000001",
                "available_quantity": 12,
                "reserved_quantity": 0,
            },
        ]

        result = find_fulfillment_node(
            warehouses, "SKU-000001", 5
        )

        self.assertEqual(result, "FUL-2026-000001")
        
    def test_reserves_inventory_when_stock_is_sufficient(self):
        inventory = {
        "available_quantity": 10,
        "reserved_quantity": 2,
        }

        result = reserve_inventory(inventory, 5)

        self.assertTrue(result)
        self.assertEqual(inventory["reserved_quantity"], 7)
        self.assertEqual(inventory["available_quantity"], 10)

    def test_does_not_reserve_when_stock_is_insufficient(self):
        inventory = {
            "available_quantity": 5,
            "reserved_quantity": 2,
        }

        result = reserve_inventory(inventory, 4)

        self.assertFalse(result)
        self.assertEqual(inventory["reserved_quantity"], 2)

    def test_reservation_rejects_zero_quantity(self):
        inventory = {
            "available_quantity": 10,
            "reserved_quantity": 2,
        }

        with self.assertRaises(ValueError):
            reserve_inventory(inventory, 0)

    def test_reservation_rejects_negative_quantity(self):
        inventory = {
            "available_quantity": 10,
            "reserved_quantity": 2,
        }

        with self.assertRaises(ValueError):
            reserve_inventory(inventory, -1)
            
    def test_repeated_reservations_use_updated_stock(self):
        inventory = {
            "available_quantity": 10,
            "reserved_quantity": 2,
        }

        first_result = reserve_inventory(inventory, 5)
        second_result = reserve_inventory(inventory, 4)

        self.assertTrue(first_result)
        self.assertFalse(second_result)
        self.assertEqual(inventory["reserved_quantity"], 7)
        
    def test_accepts_order_when_capacity_is_sufficient(self):
        capacity = {
            "max_order_lines": 100,
            "used_order_lines": 98,
            "max_units": 500,
            "used_units": 490,
        }

        self.assertTrue(can_accept_order(capacity, 2, 10))

    def test_rejects_order_when_line_capacity_is_insufficient(self):
        capacity = {
            "max_order_lines": 100,
            "used_order_lines": 98,
            "max_units": 500,
            "used_units": 490,
        }

        self.assertFalse(can_accept_order(capacity, 3, 10))

    def test_rejects_order_when_unit_capacity_is_insufficient(self):
        capacity = {
            "max_order_lines": 100,
            "used_order_lines": 90,
            "max_units": 500,
            "used_units": 495,
        }

        self.assertFalse(can_accept_order(capacity, 2, 10))

    def test_rejects_zero_requested_capacity(self):
        capacity = {
            "max_order_lines": 100,
            "used_order_lines": 20,
            "max_units": 500,
            "used_units": 100,
        }

        with self.assertRaises(ValueError):
            can_accept_order(capacity, 0, 5)
            
    def test_records_capacity_when_order_fits(self):
        capacity = {
            "max_order_lines": 100,
            "used_order_lines": 98,
            "max_units": 500,
            "used_units": 490,
        }

        result = record_capacity_usage(capacity, 2, 10)

        self.assertTrue(result)
        self.assertEqual(capacity["used_order_lines"], 100)
        self.assertEqual(capacity["used_units"], 500)

    def test_does_not_update_capacity_when_order_does_not_fit(self):
        capacity = {
            "max_order_lines": 100,
            "used_order_lines": 98,
            "max_units": 500,
            "used_units": 490,
        }

        result = record_capacity_usage(capacity, 3, 10)

        self.assertFalse(result)
        self.assertEqual(capacity["used_order_lines"], 98)
        self.assertEqual(capacity["used_units"], 490)

    def test_records_capacity_for_multiple_orders(self):
        capacity = {
            "max_order_lines": 100,
            "used_order_lines": 90,
            "max_units": 500,
            "used_units": 450,
        }

        first_result = record_capacity_usage(capacity, 5, 20)
        second_result = record_capacity_usage(capacity, 5, 30)

        self.assertTrue(first_result)
        self.assertTrue(second_result)
        self.assertEqual(capacity["used_order_lines"], 100)
        self.assertEqual(capacity["used_units"], 500)
        
    def test_rejects_negative_maximum_capacity(self):
        capacity = {
            "max_order_lines": -1,
            "used_order_lines": 0,
            "max_units": 500,
            "used_units": 100,
        }

        with self.assertRaises(ValueError):
            can_accept_order(capacity, 1, 5)

    def test_rejects_used_capacity_above_maximum(self):
        capacity = {
            "max_order_lines": 100,
            "used_order_lines": 101,
            "max_units": 500,
            "used_units": 100,
        }

        with self.assertRaises(ValueError):
            can_accept_order(capacity, 1, 5)
            
    def test_selects_warehouse_with_stock_and_capacity(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 8,
            },
            {
                "node_id": "FUL-2026-000002",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 100,
            },
            {
                "node_id": "FUL-2026-000002",
                "max_order_lines": 100,
                "used_order_lines": 20,
                "max_units": 500,
                "used_units": 100,
            },
        ]

        result = find_eligible_fulfillment_node(
            inventory, capacity, "SKU-000001", 5, 1
        )

        self.assertEqual(result, "FUL-2026-000002")

    def test_returns_none_when_capacity_is_insufficient(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 0,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 10,
                "used_order_lines": 10,
                "max_units": 100,
                "used_units": 50,
            },
        ]

        result = find_eligible_fulfillment_node(
            inventory, capacity, "SKU-000001", 5, 1
        )

        self.assertIsNone(result)

    def test_returns_none_when_inventory_is_insufficient(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 5,
                "reserved_quantity": 2,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 100,
            },
        ]

        result = find_eligible_fulfillment_node(
            inventory, capacity, "SKU-000001", 5, 1
        )

        self.assertIsNone(result)
        
    def test_allocation_updates_inventory_and_capacity(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 20,
                "max_units": 500,
                "used_units": 100,
            },
        ]

        result = allocate_order_line(
            inventory,
            capacity,
            "SKU-000001",
            5,
        )

        self.assertEqual(result, "FUL-2026-000001")
        self.assertEqual(inventory[0]["reserved_quantity"], 7)
        self.assertEqual(capacity[0]["used_order_lines"], 21)
        self.assertEqual(capacity[0]["used_units"], 105)
        
    def test_failed_allocation_does_not_change_inventory_or_capacity(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 5,
                "reserved_quantity": 2,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 20,
                "max_units": 500,
                "used_units": 100,
            },
        ]

        result = allocate_order_line(
            inventory,
            capacity,
            "SKU-000001",
            5,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_order_lines"], 20)
        self.assertEqual(capacity[0]["used_units"], 100)
        
    def test_failed_allocation_when_capacity_is_full(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 100,
                "max_units": 500,
                "used_units": 450,
            },
        ]

        result = allocate_order_line(
            inventory,
            capacity,
            "SKU-000001",
            5,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_order_lines"], 100)
        self.assertEqual(capacity[0]["used_units"], 450)
        
    
    def test_selects_eligible_warehouse_with_least_excess_stock(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 20,
                "reserved_quantity": 5,
            },
            {
                "node_id": "FUL-2026-000002",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 100,
            },
            {
                "node_id": "FUL-2026-000002",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 100,
            },
        ]

        result = find_eligible_fulfillment_node(
            inventory,
            capacity,
            "SKU-000001",
            5,
            1,
        )

        self.assertEqual(result, "FUL-2026-000002")

    
    def test_skips_warehouse_with_insufficient_capacity(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 20,
                "reserved_quantity": 5,
            },
            {
                "node_id": "FUL-2026-000002",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 10,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 100,
            },
            {
                "node_id": "FUL-2026-000002",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 100,
            },
        ]

        result = find_eligible_fulfillment_node(
            inventory,
            capacity,
            "SKU-000001",
            5,
            1,
        )

        self.assertEqual(result, "FUL-2026-000002")
        
    
    def test_allocation_updates_only_the_selected_sku_inventory(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 20,
                "reserved_quantity": 5,
            },
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000002",
                "available_quantity": 30,
                "reserved_quantity": 4,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 100,
            }
        ]

        result = allocate_order_line(
            inventory,
            capacity,
            "SKU-000001",
            3,
        )

        self.assertEqual(result, "FUL-2026-000001")
        self.assertEqual(inventory[0]["reserved_quantity"], 8)
        self.assertEqual(inventory[1]["reserved_quantity"], 4)
        self.assertEqual(capacity[0]["used_order_lines"], 11)
        self.assertEqual(capacity[0]["used_units"], 103)
        
    
    def test_repeated_allocations_cannot_exceed_available_stock(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 7,
            }
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 0,
                "max_units": 500,
                "used_units": 0,
            }
        ]

        first_result = allocate_order_line(
            inventory, capacity, "SKU-000001", 3
        )
        second_result = allocate_order_line(
            inventory, capacity, "SKU-000001", 1
        )

        self.assertEqual(first_result, "FUL-2026-000001")
        self.assertIsNone(second_result)
        self.assertEqual(inventory[0]["reserved_quantity"], 10)
        self.assertEqual(capacity[0]["used_order_lines"], 1)
        self.assertEqual(capacity[0]["used_units"], 3)
        
    
    def test_allocation_rejects_zero_or_negative_quantity(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            }
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 0,
                "max_units": 500,
                "used_units": 0,
            }
        ]

        for quantity in (0, -1):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError):
                    allocate_order_line(
                        inventory,
                        capacity,
                        "SKU-000001",
                        quantity,
                    )

        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_order_lines"], 0)
        self.assertEqual(capacity[0]["used_units"], 0)
        
    
    def test_allocation_fails_when_sku_does_not_exist(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            }
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 0,
                "max_units": 500,
                "used_units": 0,
            }
        ]

        result = allocate_order_line(
            inventory,
            capacity,
            "SKU-999999",
            2,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_order_lines"], 0)
        self.assertEqual(capacity[0]["used_units"], 0)
        
    
    def test_allocation_fails_when_all_warehouses_lack_stock(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 5,
                "reserved_quantity": 3,
            },
            {
                "node_id": "FUL-2026-000002",
                "sku_id": "SKU-000001",
                "available_quantity": 4,
                "reserved_quantity": 2,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 0,
                "max_units": 500,
                "used_units": 0,
            },
            {
                "node_id": "FUL-2026-000002",
                "max_order_lines": 100,
                "used_order_lines": 0,
                "max_units": 500,
                "used_units": 0,
            },
        ]

        result = allocate_order_line(
            inventory,
            capacity,
            "SKU-000001",
            3,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 3)
        self.assertEqual(inventory[1]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_units"], 0)
        self.assertEqual(capacity[1]["used_units"], 0)
        
    
    def test_allocation_fails_when_warehouse_capacity_is_missing(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            }
        ]

        capacity = []

        result = allocate_order_line(
            inventory,
            capacity,
            "SKU-000001",
            3,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        
    
    def test_allocate_order_with_multiple_lines(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            },
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000002",
                "available_quantity": 20,
                "reserved_quantity": 5,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 3,
            },
            {
                "order_line_id": "LINE-000002",
                "sku_id": "SKU-000002",
                "quantity": 4,
            },
        ]

        result = allocate_order(
            inventory,
            capacity,
            order_lines,
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["node_id"], "FUL-2026-000001")
        self.assertEqual(result[1]["node_id"], "FUL-2026-000001")
        self.assertEqual(inventory[0]["reserved_quantity"], 5)
        self.assertEqual(inventory[1]["reserved_quantity"], 9)
        self.assertEqual(capacity[0]["used_order_lines"], 12)
        self.assertEqual(capacity[0]["used_units"], 57)
        
    
    def test_allocate_order_rolls_back_when_a_line_fails(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            },
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000002",
                "available_quantity": 5,
                "reserved_quantity": 4,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 3,
            },
            {
                "order_line_id": "LINE-000002",
                "sku_id": "SKU-000002",
                "quantity": 2,
            },
        ]

        result = allocate_order(
            inventory,
            capacity,
            order_lines,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(inventory[1]["reserved_quantity"], 4)
        self.assertEqual(capacity[0]["used_order_lines"], 10)
        self.assertEqual(capacity[0]["used_units"], 50)
        
    
    def test_allocate_order_rejects_empty_order_lines(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            }
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            }
        ]

        result = allocate_order(
            inventory,
            capacity,
            [],
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_order_lines"], 10)
        self.assertEqual(capacity[0]["used_units"], 50)
        
    
    def test_allocate_order_rejects_duplicate_skus(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            }
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 2,
            },
            {
                "order_line_id": "LINE-000002",
                "sku_id": "SKU-000001",
                "quantity": 3,
            },
        ]

        result = allocate_order(
            inventory,
            capacity,
            order_lines,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_order_lines"], 10)
        self.assertEqual(capacity[0]["used_units"], 50)


    def test_allocate_order_rejects_invalid_quantity_before_allocation(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            },
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000002",
                "available_quantity": 10,
                "reserved_quantity": 1,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 3,
            },
            {
                "order_line_id": "LINE-000002",
                "sku_id": "SKU-000002",
                "quantity": 0,
            },
        ]

        result = allocate_order(
            inventory,
            capacity,
            order_lines,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(inventory[1]["reserved_quantity"], 1)
        self.assertEqual(capacity[0]["used_order_lines"], 10)
        self.assertEqual(capacity[0]["used_units"], 50)

    
    def test_allocate_order_rejects_missing_required_field(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            }
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
            }
        ]

        result = allocate_order(
            inventory,
            capacity,
            order_lines,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_order_lines"], 10)
        self.assertEqual(capacity[0]["used_units"], 50)

    
    def test_allocate_order_rejects_blank_sku_id(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            }
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "   ",
                "quantity": 2,
            }
        ]

        result = allocate_order(
            inventory,
            capacity,
            order_lines,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_order_lines"], 10)
        self.assertEqual(capacity[0]["used_units"], 50)

    
    def test_allocate_order_rejects_fractional_quantity(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            }
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 2.5,
            }
        ]

        result = allocate_order(
            inventory,
            capacity,
            order_lines,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_order_lines"], 10)
        self.assertEqual(capacity[0]["used_units"], 50)

    
    def test_allocate_order_rejects_text_quantity(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            }
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": "3",
            }
        ]

        result = allocate_order(
            inventory,
            capacity,
            order_lines,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_order_lines"], 10)
        self.assertEqual(capacity[0]["used_units"], 50)

    
    def test_allocate_order_rejects_none_quantity(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            }
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": None,
            }
        ]

        result = allocate_order(
            inventory,
            capacity,
            order_lines,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_order_lines"], 10)
        self.assertEqual(capacity[0]["used_units"], 50)

    
    def test_allocate_order_rolls_back_when_later_sku_is_unknown(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            }
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 3,
            },
            {
                "order_line_id": "LINE-000002",
                "sku_id": "SKU-999999",
                "quantity": 2,
            },
        ]

        result = allocate_order(
            inventory,
            capacity,
            order_lines,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_order_lines"], 10)
        self.assertEqual(capacity[0]["used_units"], 50)
        
    
    def test_allocate_order_rejects_duplicate_order_line_ids(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            },
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000002",
                "available_quantity": 10,
                "reserved_quantity": 1,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 2,
            },
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000002",
                "quantity": 3,
            },
        ]

        result = allocate_order(
            inventory,
            capacity,
            order_lines,
        )

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(inventory[1]["reserved_quantity"], 1)
        self.assertEqual(capacity[0]["used_order_lines"], 10)
        self.assertEqual(capacity[0]["used_units"], 50)

    
    def test_allocate_order_rejects_duplicate_skus_without_changes(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            }
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 2,
            },
            {
                "order_line_id": "LINE-000002",
                "sku_id": "SKU-000001",
                "quantity": 3,
            },
        ]

        result = allocate_order(inventory, capacity, order_lines)

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(capacity[0]["used_order_lines"], 10)
        self.assertEqual(capacity[0]["used_units"], 50)
        
    
    def test_allocate_order_can_use_different_warehouses(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            },
            {
                "node_id": "FUL-2026-000002",
                "sku_id": "SKU-000002",
                "available_quantity": 20,
                "reserved_quantity": 1,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            },
            {
                "node_id": "FUL-2026-000002",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            },
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 3,
            },
            {
                "order_line_id": "LINE-000002",
                "sku_id": "SKU-000002",
                "quantity": 4,
            },
        ]

        result = allocate_order(inventory, capacity, order_lines)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["node_id"], "FUL-2026-000001")
        self.assertEqual(result[1]["node_id"], "FUL-2026-000002")
        self.assertEqual(inventory[0]["reserved_quantity"], 5)
        self.assertEqual(inventory[1]["reserved_quantity"], 5)

    
    def test_allocate_order_updates_capacity_at_each_warehouse(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            },
            {
                "node_id": "FUL-2026-000002",
                "sku_id": "SKU-000002",
                "available_quantity": 20,
                "reserved_quantity": 1,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 100,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 50,
            },
            {
                "node_id": "FUL-2026-000002",
                "max_order_lines": 100,
                "used_order_lines": 20,
                "max_units": 500,
                "used_units": 80,
            },
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 3,
            },
            {
                "order_line_id": "LINE-000002",
                "sku_id": "SKU-000002",
                "quantity": 4,
            },
        ]

        result = allocate_order(inventory, capacity, order_lines)

        self.assertIsNotNone(result)

        self.assertEqual(capacity[0]["used_order_lines"], 11)
        self.assertEqual(capacity[0]["used_units"], 53)

        self.assertEqual(capacity[1]["used_order_lines"], 21)
        self.assertEqual(capacity[1]["used_units"], 84)

    
    def test_allocate_order_rolls_back_when_later_line_exceeds_capacity(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            },
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000002",
                "available_quantity": 10,
                "reserved_quantity": 1,
            },
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 11,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 490,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 3,
            },
            {
                "order_line_id": "LINE-000002",
                "sku_id": "SKU-000002",
                "quantity": 2,
            },
        ]

        result = allocate_order(inventory, capacity, order_lines)

        self.assertIsNone(result)
        self.assertEqual(inventory[0]["reserved_quantity"], 2)
        self.assertEqual(inventory[1]["reserved_quantity"], 1)
        self.assertEqual(capacity[0]["used_order_lines"], 10)
        self.assertEqual(capacity[0]["used_units"], 490)

    
    def test_allocate_order_accepts_exact_remaining_capacity(self):
        inventory = [
            {
                "node_id": "FUL-2026-000001",
                "sku_id": "SKU-000001",
                "available_quantity": 10,
                "reserved_quantity": 2,
            }
        ]

        capacity = [
            {
                "node_id": "FUL-2026-000001",
                "max_order_lines": 11,
                "used_order_lines": 10,
                "max_units": 500,
                "used_units": 497,
            }
        ]

        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 3,
            }
        ]

        result = allocate_order(inventory, capacity, order_lines)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(inventory[0]["reserved_quantity"], 5)
        self.assertEqual(capacity[0]["used_order_lines"], 11)
        self.assertEqual(capacity[0]["used_units"], 500)

    
    def test_calculate_order_units(self):
        order_lines = [
            {"order_line_id": "LINE-000001", "sku_id": "SKU-000001", "quantity": 2},
            {"order_line_id": "LINE-000002", "sku_id": "SKU-000002", "quantity": 3},
        ]

        self.assertEqual(calculate_order_units(order_lines), 5)
        
    
    def test_calculate_order_line_count(self):
        order_lines = [
            {"order_line_id": "LINE-000001", "sku_id": "SKU-000001", "quantity": 2},
            {"order_line_id": "LINE-000002", "sku_id": "SKU-000002", "quantity": 3},
        ]

        self.assertEqual(calculate_order_line_count(order_lines), 2)

    
    def test_validate_order_lines_accepts_valid_input(self):
        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 2,
            },
            {
                "order_line_id": "LINE-000002",
                "sku_id": "SKU-000002",
                "quantity": 3,
            },
        ]

        self.assertTrue(validate_order_lines(order_lines))

    
    def test_validate_order_lines_rejects_empty_order(self):
        self.assertFalse(validate_order_lines([]))

    
    def test_validate_order_lines_rejects_missing_quantity(self):
        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
            }
        ]

        self.assertFalse(validate_order_lines(order_lines))
        
    
    def test_validate_order_lines_rejects_duplicate_skus(self):
        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 2,
            },
            {
                "order_line_id": "LINE-000002",
                "sku_id": "SKU-000001",
                "quantity": 3,
            },
        ]

        self.assertFalse(validate_order_lines(order_lines))
        
    
    def test_validate_order_lines_rejects_duplicate_line_ids(self):
        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 2,
            },
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000002",
                "quantity": 3,
            },
        ]

        self.assertFalse(validate_order_lines(order_lines))
        
    
    def test_validate_order_lines_rejects_zero_quantity(self):
        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 0,
            }
        ]

        self.assertFalse(validate_order_lines(order_lines))
    
    
    def test_validate_order_lines_rejects_negative_quantity(self):
        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": -2,
            }
        ]

        self.assertFalse(validate_order_lines(order_lines))
        
    
    def test_validate_order_lines_rejects_fractional_quantity(self):
        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 2.5,
            }
        ]

        self.assertFalse(validate_order_lines(order_lines))

    
    def test_validate_order_lines_rejects_text_quantity(self):
        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": "3",
            }
        ]

        self.assertFalse(validate_order_lines(order_lines))

    
    def test_validate_order_lines_rejects_boolean_quantity(self):
        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": True,
            }
        ]

        self.assertFalse(validate_order_lines(order_lines))

    
    def test_validate_order_lines_accepts_single_valid_line(self):
        order_lines = [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 1,
            }
        ]

        self.assertTrue(validate_order_lines(order_lines))














if __name__ == "__main__":
    unittest.main()
