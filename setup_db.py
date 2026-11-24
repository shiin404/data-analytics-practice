"""День 1: создание учебной SQLite БД без повторной вставки начальных данных."""
import sqlite3
from contextlib import closing
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "shop.db"
SALES = [
    ("Ноутбук", "Техника", 320000, 2, "2026-11-01"),
    ("Мышь", "Аксессуары", 6500, 8, "2026-11-01"),
    ("Монитор", "Техника", 95000, 3, "2026-11-02"),
    ("Клавиатура", "Аксессуары", 14000, 5, "2026-11-02"),
    ("Наушники", "Аксессуары", 23000, 4, "2026-11-03"),
    ("Смартфон", "Техника", 210000, 2, "2026-11-03"),
    ("USB кабель", "Аксессуары", 2500, 12, "2026-11-04"),
    ("Веб камера", "Техника", 28000, 3, "2026-11-04"),
    ("Настольная лампа", "Дом", 18000, 4, "2026-11-05"),
    ("Термос", "Дом", 9500, 6, "2026-11-05"),
    ("Блокнот", "Канцтовары", 1800, 20, "2026-11-06"),
    ("Ручка", "Канцтовары", 600, 30, "2026-11-06"),
    ("Ноутбук", "Техника", 320000, 1, "2026-11-07"),
    ("Мышь", "Аксессуары", 6500, 6, "2026-11-07"),
    ("Монитор", "Техника", 95000, 2, "2026-11-08"),
    ("Органайзер", "Дом", 7500, 5, "2026-11-08"),
    ("Бумага А4", "Канцтовары", 3200, 10, "2026-11-09"),
    ("Наушники", "Аксессуары", 23000, 3, "2026-11-09"),
    ("Клавиатура", "Аксессуары", 14000, 4, "2026-11-10"),
    ("Настольная лампа", "Дом", 18000, 2, "2026-11-10"),
]

def setup_database(db_path=DB_PATH):
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL CHECK(length(trim(product)) > 0),
            category TEXT NOT NULL CHECK(length(trim(category)) > 0),
            price INTEGER NOT NULL CHECK(price > 0),
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            sale_date TEXT NOT NULL CHECK(length(sale_date) = 10)
        )""")
        conn.execute("CREATE TABLE IF NOT EXISTS project_steps (name TEXT PRIMARY KEY)")
        if not conn.execute("SELECT 1 FROM project_steps WHERE name='day1'").fetchone():
            conn.executemany("""INSERT INTO sales
                (product, category, price, quantity, sale_date) VALUES (?, ?, ?, ?, ?)""", SALES)
            conn.execute("INSERT INTO project_steps VALUES ('day1')")
        return conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]

if __name__ == "__main__":
    print(f"База данных готова: {DB_PATH}; записей: {setup_database()}")
