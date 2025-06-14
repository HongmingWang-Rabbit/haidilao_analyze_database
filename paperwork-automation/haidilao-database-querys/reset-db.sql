-- WARNING: This will delete all your reporting data. Use with caution.

-- Drop tables if they exist
DROP TABLE IF EXISTS store_monthly_target;
DROP TABLE IF EXISTS store_time_report;
DROP TABLE IF EXISTS daily_report;
DROP TABLE IF EXISTS time_segment;
DROP TABLE IF EXISTS store;


CREATE TABLE store (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE, -- 门店名称
    country VARCHAR,              -- 国家
    manager VARCHAR,              -- 国家负责人
    opened_at DATE,               -- 开业日期
    seats_total INTEGER           -- 所有餐位数 (fixed capacity)
);

CREATE TABLE daily_report (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES store(id), -- 外键：门店
    date DATE,                             -- 日期
    month INTEGER,                         -- 月份
    is_holiday BOOLEAN,                    -- 是否节假日
    tables_served INTEGER,                -- 营业桌数
    tables_served_validated INTEGER,      -- 营业桌数(考核)
    turnover_rate NUMERIC(6, 3),          -- 翻台率(考核)
    revenue_tax_included NUMERIC(10, 2),  -- 营业收入(含税)
    takeout_tables INTEGER,               -- 营业桌数(考核)(外卖)
    customers INTEGER,                    -- 就餐人数
    discount_total NUMERIC(10, 2),        -- 优惠总金额(含税)
    UNIQUE(store_id, date)                -- Unique constraint for UPSERT
);

CREATE TABLE time_segment (
    id SERIAL PRIMARY KEY,
    label VARCHAR NOT NULL UNIQUE,        -- 分时段标签，例如 "08:00-13:59"
    start_time TIME,                      -- 开始时间
    end_time TIME,                        -- 结束时间
    description VARCHAR                   -- 描述（可选）
);

CREATE TABLE store_time_report (
    id SERIAL PRIMARY KEY,
    store_id INTEGER REFERENCES store(id),             -- 外键：门店
    date DATE,                                          -- 日期
    time_segment_id INTEGER REFERENCES time_segment(id), -- 外键：分时段
    is_holiday BOOLEAN,                                -- 是否节假日
    tables_served_validated INTEGER,                   -- 营业桌数(考核)
    turnover_rate NUMERIC(6, 3),                       -- 翻台率(考核)
    UNIQUE(store_id, date, time_segment_id)            -- Unique constraint for UPSERT
);

CREATE TABLE store_monthly_target (
  id SERIAL PRIMARY KEY,                     -- 主键，自增
  store_id INT REFERENCES store(id),         -- 外键：门店 ID
  month DATE NOT NULL,                       -- 目标月份（建议使用每月第一天作为标识）

  turnover_rate NUMERIC(6, 3),               -- 目标翻台率
  table_avg_spending NUMERIC(10, 2),         -- 目标每桌消费金额
  revenue NUMERIC(14, 2),                    -- 营业收入目标（含税）
  labor_percentage NUMERIC(5, 2),            -- 人工成本占比（百分比形式：如 28.5）
  gross_revenue NUMERIC(14, 2),              -- 毛收入目标
  monthly_CAD_USD_rate NUMERIC(8, 4)         -- 本月 CAD/USD 汇率
);
