INSERT INTO store_time_report (store_id, date, time_segment_id, is_holiday, tables_served_validated, turnover_rate) VALUES
  (1, '2025-06-10', 1, False, 15.0, 1.8),
  (1, '2025-06-10', 2, False, 12.0, 2.2),
  (1, '2025-06-10', 3, False, 20.0, 3.5),
  (1, '2025-06-10', 4, False, 8.0, 1.2),
  (2, '2025-06-10', 1, False, 15.0, 1.8),
  (2, '2025-06-10', 2, False, 12.0, 2.2),
  (2, '2025-06-10', 3, False, 20.0, 3.5),
  (2, '2025-06-10', 4, False, 8.0, 1.2),
  (3, '2025-06-10', 1, False, 15.0, 1.8),
  (3, '2025-06-10', 2, False, 12.0, 2.2),
  (3, '2025-06-10', 3, False, 20.0, 3.5),
  (3, '2025-06-10', 4, False, 8.0, 1.2)
ON CONFLICT (store_id, date, time_segment_id) DO UPDATE SET
  is_holiday = EXCLUDED.is_holiday, tables_served_validated = EXCLUDED.tables_served_validated, turnover_rate = EXCLUDED.turnover_rate;