"""День 1: все требуемые SQL запросы. Запуск: python check_db.py."""
import sqlite3
from contextlib import closing
from setup_db import DB_PATH

QUERIES = {
    "Все продажи": ("SELECT * FROM sales ORDER BY id", ()),
    "Товары дороже 20 000 тенге": ("SELECT * FROM sales WHERE price > ?", (20000,)),
    "Категория Техника": ("SELECT * FROM sales WHERE category = ?", ("Техника",)),
    "Цена по убыванию": ("SELECT * FROM sales ORDER BY price DESC, id", ()),
    "Количество записей": ("SELECT COUNT(*) FROM sales", ()),
    "Категории": ("SELECT DISTINCT category FROM sales ORDER BY category", ()),
}

def main():
    if not DB_PATH.exists():
        raise SystemExit("Сначала запустите python setup_db.py")
    with closing(sqlite3.connect(DB_PATH)) as conn, conn:
        for title, (query, parameters) in QUERIES.items():
            print(f"\n{title}\nSQL: {query}; параметры: {parameters}")
            for row in conn.execute(query, parameters):
                print(row)

if __name__ == "__main__":
    main()
