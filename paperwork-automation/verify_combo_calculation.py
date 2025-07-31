#!/usr/bin/env python3
"""
Verify Combo Calculation

This script verifies what the combo usage value should be.
"""

# Example calculation
# If combo dishes sold 10 units with:
# - standard_quantity: 0.1
# - loss_rate: 1.0
# - unit_conversion_rate: 0.34

combo_sales = 10
standard_quantity = 0.1
loss_rate = 1.0
unit_conversion_rate = 0.34

# With multiplication (wrong)
combo_multiply = combo_sales * standard_quantity * loss_rate * unit_conversion_rate
print(f"Combo with multiplication: {combo_multiply:.4f}")

# With division (correct)
combo_divide = combo_sales * standard_quantity * loss_rate / unit_conversion_rate
print(f"Combo with division: {combo_divide:.4f}")

# The value 0.8824 from user's example
# Let's work backwards to see what sales would give 0.8824
# 0.8824 = sales * 0.1 * 1.0 / 0.34
# sales = 0.8824 * 0.34 / 0.1 = 3.0

print(f"\nTo get combo usage of 0.8824:")
print(f"Required sales: {0.8824 * 0.34 / 0.1:.1f}")
print(f"Verification: {3 * 0.1 * 1.0 / 0.34:.4f}")