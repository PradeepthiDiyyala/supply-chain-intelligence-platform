import pytest
from src.inventory import recommend_replenishment
from src.advanced_analytics import seller_scorecard

def test_inventory_replenishment_rounds_to_pack():
    r=recommend_replenishment(10,20,14,1,6)
    assert r["reorder_point"]==60
    assert r["recommended_order_qty"]==54
    assert r["stockout_risk"]=="High"

def test_inventory_rejects_negative():
    with pytest.raises(ValueError):
        recommend_replenishment(-1,20,14)
