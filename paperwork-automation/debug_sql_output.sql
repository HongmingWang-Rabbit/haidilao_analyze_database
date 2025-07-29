
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
        