"""День 5: пять новых продаж и новая категория. Повторный запуск безопасен."""
import json
import sqlite3
from contextlib import closing
from setup_db import BASE, DB_PATH, setup_database
from analytics_core import load_sales, metrics

NEW_SALES = [
    ("Фитнес браслет", "Спорт", 22000, 4, "2026-11-11"),
    ("Коврик для йоги", "Спорт", 12000, 3, "2026-11-11"),
    ("Ноутбук", "Техника", 320000, 1, "2026-11-12"),
    ("Мышь", "Аксессуары", 6500, 5, "2026-11-12"),
    ("Блокнот", "Канцтовары", 1800, 15, "2026-11-12"),
]

def add_sales(db_path=DB_PATH):
    setup_database(db_path)
    before = metrics(load_sales(db_path))
    with closing(sqlite3.connect(db_path)) as conn, conn:
        if conn.execute("SELECT 1 FROM project_steps WHERE name='day5'").fetchone():
            return None
        conn.executemany("""INSERT INTO sales
            (product, category, price, quantity, sale_date) VALUES (?, ?, ?, ?, ?)""", NEW_SALES)
        conn.execute("INSERT INTO project_steps VALUES ('day5')")
    after = metrics(load_sales(db_path))
    return {"before": before, "after": after,
            "added_records": after["records"] - before["records"],
            "added_revenue": after["revenue"] - before["revenue"]}

if __name__ == "__main__":
    result = add_sales()
    if result:
        (BASE / "day5_update.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Пять продаж дня 5 уже добавлены; повторной вставки нет.")
