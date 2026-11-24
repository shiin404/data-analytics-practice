"""Общая загрузка, фильтрация и показатели для анализа и дашборда."""
import sqlite3
from contextlib import closing
import pandas as pd
from setup_db import DB_PATH

SALE_COLUMNS = ["product", "category", "price", "quantity", "sale_date"]

def load_sales(db_path=DB_PATH):
    if not db_path.exists():
        raise FileNotFoundError("База shop.db не найдена. Запустите python setup_db.py")
    with closing(sqlite3.connect(db_path)) as conn, conn:
        df = pd.read_sql_query("SELECT * FROM sales ORDER BY id", conn)
    df["sale_date"] = pd.to_datetime(df["sale_date"], format="%Y-%m-%d", errors="raise")
    df["revenue"] = df["price"] * df["quantity"]
    return df

def filter_sales(df, categories, products):
    return df.loc[df["category"].isin(categories) & df["product"].isin(products)].copy()

def metrics(df):
    return {
        "revenue": int(df["revenue"].sum()),
        "quantity": int(df["quantity"].sum()),
        "records": len(df),
        "mean_price": float(df["price"].mean()) if not df.empty else 0.0,
    }

def csv_bytes(df):
    exported = df.copy()
    exported["sale_date"] = exported["sale_date"].dt.strftime("%Y-%m-%d")
    return exported.to_csv(index=False).encode("utf-8-sig")
