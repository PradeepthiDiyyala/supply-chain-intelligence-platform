"""Transparent what-if inventory calculations; inventory is user-supplied, not in Olist."""
import math

def recommend_replenishment(current_stock, average_weekly_demand, lead_time_days,
                            service_buffer_weeks=1.0, pack_size=1):
    values=[current_stock,average_weekly_demand,lead_time_days,service_buffer_weeks,pack_size]
    if any(v<0 for v in values) or pack_size<1:
        raise ValueError("Inputs must be non-negative and pack_size must be at least 1.")
    lead_weeks=lead_time_days/7
    reorder_point=average_weekly_demand*(lead_weeks+service_buffer_weeks)
    gap=max(0.0,reorder_point-current_stock)
    qty=int(math.ceil(gap/pack_size)*pack_size)
    return {"reorder_point":round(reorder_point,2),"recommended_order_qty":qty,
            "stockout_risk":"High" if current_stock<average_weekly_demand*lead_weeks else
                            "Medium" if current_stock<reorder_point else "Low"}
