import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from streamlit.testing.v1 import AppTest
from analytics_core import load_sales, metrics
from add_day5_sales import add_sales
from setup_db import setup_database
import tempfile

def check_metrics(app, expected):
    assert len(app.exception) == 0, app.exception
    values = [x.value for x in app.metric]
    assert values[0] == f"{expected['revenue']:,.0f} ₸", values
    assert values[1] == f"{expected['quantity']} шт.", values
    assert values[2] == str(expected['records']), values

app = AppTest.from_file(str(ROOT / "dashboard.py"), default_timeout=30).run()
check_metrics(app, metrics(load_sales()))
assert len(app.get("plotly_chart")) == 3
app.multiselect[0].set_value(["Техника"]).run()
app.multiselect[1].set_value(["Ноутбук"]).run()
check_metrics(app, {"revenue":1280000, "quantity":4, "records":3})
assert len(app.get("plotly_chart")) == 3
app.multiselect[0].set_value([]).run()
check_metrics(app, {"revenue":0, "quantity":0, "records":0})
assert len(app.info) == 1
assert len(app.get("plotly_chart")) == 0
assert len(app.get("download_button")) == 1
print("PASS: dashboard, 4 metrics, 3 charts, category/product filters, empty result, export control")

# Отдельная копия БД: реальный перезапуск интерфейса после 5 новых продаж.
import analytics_core
with tempfile.TemporaryDirectory() as tmp:
    db = Path(tmp) / "shop.db"
    setup_database(db)
    original_loader = analytics_core.load_sales
    analytics_core.load_sales = lambda: original_loader(db)
    try:
        before = AppTest.from_file(str(ROOT / "dashboard.py"), default_timeout=30).run()
        check_metrics(before, {"revenue":2635500, "quantity":132, "records":20})
        add_sales(db)
        before.run()
        check_metrics(before, {"revenue":3139000, "quantity":160, "records":25})
        assert "Спорт" in before.multiselect[0].options
    finally:
        analytics_core.load_sales = original_loader
print("PASS: dashboard refresh after 5 new sales: 20 → 25; 2 635 500 → 3 139 000 тенге")

