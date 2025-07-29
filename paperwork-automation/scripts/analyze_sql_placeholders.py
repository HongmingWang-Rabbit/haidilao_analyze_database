#!/usr/bin/env python3
"""
Analyze the SQL placeholders character by character
"""

def analyze_sql():
    """Analyze the SQL from the method"""
    
    sql = """
    SELECT 
        s.id as store_id,
        s.name as store_name,
        COALESCE(cr.current_revenue, 0) as current_revenue,
        COALESCE(cc.current_cost, 0) as current_cost,
        COALESCE(pr.previous_revenue, 0) as previous_revenue,
        COALESCE(pc.previous_cost, 0) as previous_cost
    FROM store s
    LEFT JOIN (
        SELECT 
            store_id,
            SUM(sale_amount) as current_revenue
        FROM dish_monthly_sale
        WHERE year = %s AND month = %s
        GROUP BY store_id
    ) cr ON s.id = cr.store_id
    LEFT JOIN (
        SELECT 
            mmu.store_id,
            SUM(mmu.material_used * COALESCE(mph.price, 0)) as current_cost
        FROM material_monthly_usage mmu
        LEFT JOIN LATERAL (
            SELECT price 
            FROM material_price_history 
            WHERE material_id = mmu.material_id 
                AND store_id = mmu.store_id 
                AND is_active = true
                AND effective_date <= (date_trunc('month', make_date(%s, %s, 1)) + interval '1 month - 1 day')::date
            ORDER BY effective_date DESC
            LIMIT 1
        ) mph ON true
        WHERE mmu.year = %s AND mmu.month = %s
        GROUP BY mmu.store_id
    ) cc ON s.id = cc.store_id
    LEFT JOIN (
        SELECT 
            store_id,
            SUM(revenue_tax_not_included) as previous_revenue
        FROM daily_report
        WHERE EXTRACT(YEAR FROM date) = %s 
            AND EXTRACT(MONTH FROM date) = %s
        GROUP BY store_id
    ) pr ON s.id = pr.store_id
    LEFT JOIN (
        SELECT 
            store_id,
            -- Estimate previous month cost using previous month revenue * 65% (typical restaurant cost ratio)
            ROUND(SUM(revenue_tax_not_included) * 0.65, 2) as previous_cost
        FROM daily_report
        WHERE EXTRACT(YEAR FROM date) = %s 
            AND EXTRACT(MONTH FROM date) = %s
        GROUP BY store_id
    ) pc ON s.id = pc.store_id
    WHERE s.id BETWEEN 1 AND 7
    ORDER BY s.id
    """
    
    # Count placeholders and find their positions
    placeholder_count = sql.count('%s')
    print(f"Total %s placeholders found: {placeholder_count}")
    
    # Find each placeholder position
    placeholders = []
    pos = 0
    while True:
        pos = sql.find('%s', pos)
        if pos == -1:
            break
        placeholders.append(pos)
        pos += 2
    
    print(f"Placeholder positions: {placeholders}")
    
    # Show context around each placeholder
    print("\\nPlaceholder contexts:")
    for i, pos in enumerate(placeholders):
        start = max(0, pos - 20)
        end = min(len(sql), pos + 22)
        context = sql[start:end].replace('\\n', ' ').replace('  ', ' ')
        print(f"  {i+1}: ...{context}...")
    
    # Try to identify lines with placeholders
    lines = sql.split('\\n')
    print("\\nLines with placeholders:")
    for i, line in enumerate(lines):
        if '%s' in line:
            count_in_line = line.count('%s')
            print(f"  Line {i+1} ({count_in_line} placeholders): {line.strip()}")

if __name__ == "__main__":
    analyze_sql()