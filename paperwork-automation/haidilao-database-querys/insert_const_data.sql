-- Insert store data with fixed seats_total values
-- Based on the data from the Excel file, each store has a fixed number of seats

INSERT INTO store (id, name, country, manager, opened_at, seats_total) VALUES
  (1, '加拿大一店', '加拿大', '蒋冰遇', '2018-12-18', 53),
  (2, '加拿大二店', '加拿大', '蒋冰遇', '2020-07-27', 36),
  (3, '加拿大三店', '加拿大', '蒋冰遇', '2020-08-17', 48),
  (4, '加拿大四店', '加拿大', '蒋冰遇', '2020-10-30', 70),
  (5, '加拿大五店', '加拿大', '蒋冰遇', '2022-10-03', 55),
  (6, '加拿大六店', '加拿大', '蒋冰遇', '2024-01-09', 56),
  (7, '加拿大七店', '加拿大', '蒋冰遇', '2024-05-01', 57)
  ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name,
  country = EXCLUDED.country,
  manager = EXCLUDED.manager,
  opened_at = EXCLUDED.opened_at,
  seats_total = EXCLUDED.seats_total;


-- Insert time segment data
-- Based on the time segments found in the 分时段基础表 sheet

INSERT INTO time_segment (id, label, start_time, end_time, description) VALUES
  (1, '08:00-13:59', '08:00:00', '13:59:59', 'Morning to early afternoon'),
  (2, '14:00-16:59', '14:00:00', '16:59:59', 'Afternoon'),
  (3, '17:00-21:59', '17:00:00', '21:59:59', 'Evening'),
  (4, '22:00-(次)07:59', '22:00:00', '07:59:59', 'Late night to early morning (next day)')
  ON CONFLICT (id) DO UPDATE SET
  label = EXCLUDED.label,
  start_time = EXCLUDED.start_time,
  end_time = EXCLUDED.end_time,
  description = EXCLUDED.description;
-- Note: seats_total values are based on the "所有餐位数" column from the Excel data
-- These are fixed capacities for each store and should not change daily 