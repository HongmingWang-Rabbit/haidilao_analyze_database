INSERT INTO daily_report (store_id, date, is_holiday, tables_served, tables_served_validated, turnover_rate, revenue_tax_not_included, takeout_tables, customers, discount_total) VALUES
  (1, '2025-06-10', False, 52.0, 50.0, 2.8, 18500.0, 8.0, 140.0, 850.0),
  (2, '2025-06-10', False, 48.0, 46.0, 3.1, 21000.0, 12.0, 165.0, 1200.0),
  (3, '2025-06-10', False, 45.0, 43.0, 2.5, 16800.0, 6.0, 125.0, 650.0),
  (4, '2025-06-10', False, 50.0, 48.0, 2.9, 19200.0, 9.0, 148.0, 950.0),
  (5, '2025-06-10', False, 46.0, 44.0, 3.2, 22500.0, 14.0, 172.0, 1350.0),
  (6, '2025-06-10', False, 44.0, 42.0, 2.7, 17300.0, 7.0, 130.0, 720.0),
  (7, '2025-06-10', False, 49.0, 47.0, 3.0, 20100.0, 11.0, 158.0, 1100.0)
ON CONFLICT (store_id, date) DO UPDATE SET
  is_holiday = EXCLUDED.is_holiday, tables_served = EXCLUDED.tables_served, tables_served_validated = EXCLUDED.tables_served_validated, turnover_rate = EXCLUDED.turnover_rate, revenue_tax_not_included = EXCLUDED.revenue_tax_not_included, takeout_tables = EXCLUDED.takeout_tables, customers = EXCLUDED.customers, discount_total = EXCLUDED.discount_total;