INSERT INTO store_time_report (store_id, date, time_segment_id, is_holiday, tables_served_validated, turnover_rate) VALUES
  (1, '2025-06-10', 1, False, 25.0, 1.5)
ON CONFLICT (store_id, date, time_segment_id) DO UPDATE SET
  is_holiday = EXCLUDED.is_holiday, tables_served_validated = EXCLUDED.tables_served_validated, turnover_rate = EXCLUDED.turnover_rate;