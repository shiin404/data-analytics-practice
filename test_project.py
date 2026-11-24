"""Проверки БД, расчётов, обновления, фильтров и экспорта. python test_project.py"""
import io
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from setup_db import setup_database
from add_day5_sales import add_sales
from analytics_core import load_sales, metrics, filter_sales, csv_bytes
from analysis import outlier_experiment

class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "shop.db"
        setup_database(self.db)

    def test_seed_is_idempotent_and_sql(self):
        self.assertEqual(setup_database(self.db), 20)
        with closing(sqlite3.connect(self.db)) as conn, conn:
            self.assertEqual(conn.execute("SELECT COUNT(DISTINCT category) FROM sales").fetchone()[0], 4)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM sales WHERE price > 20000").fetchone()[0], 8)
            self.assertEqual(conn.execute("SELECT SUM(price * quantity) FROM sales").fetchone()[0], 2635500)
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO sales (product,category,price,quantity,sale_date) VALUES ('Ошибка','Тест',-1,1,'2026-11-01')")

    def test_day5_update_and_repeated_run(self):
        result = add_sales(self.db)
        self.assertEqual(result["added_records"], 5)
        self.assertEqual(result["added_revenue"], 503500)
        self.assertIsNone(add_sales(self.db))
        self.assertEqual(setup_database(self.db), 25)
        final = load_sales(self.db)
        self.assertEqual(metrics(final)["quantity"], 160)
        self.assertEqual(final.category.nunique(), 5)

    def test_filters_and_csv(self):
        df = load_sales(self.db)
        selected = filter_sales(df, ["Техника"], ["Ноутбук"])
        self.assertEqual(metrics(selected)["revenue"], 960000)
        self.assertEqual(metrics(selected)["quantity"], 3)
        empty = filter_sales(df, [], [])
        self.assertEqual(metrics(empty)["records"], 0)
        for subset in (selected, empty):
            data = csv_bytes(subset)
            self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
            recovered = pd.read_csv(io.BytesIO(data))
            self.assertEqual(len(recovered), len(subset))
        self.assertTrue(filter_sales(df, ["Дом"], ["Ноутбук"]).empty)

    def test_outlier_changes_mean_and_restores_database(self):
        before = load_sales(self.db)
        result = outlier_experiment(self.db)
        self.assertGreater(result["with_outlier"]["mean"], 10 * result["before"]["mean"])
        pd.testing.assert_frame_equal(before, load_sales(self.db))
        self.assertTrue((self.db.parent / "shop_backup.db").exists())

if __name__ == "__main__":
    unittest.main(verbosity=2)
