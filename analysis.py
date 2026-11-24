"""Дни 2–3: показатели, пять PNG диаграмм, качество и эксперимент с выбросом."""
import json
import sqlite3
from contextlib import closing
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from analytics_core import SALE_COLUMNS, load_sales, metrics
from setup_db import BASE, DB_PATH

def outlier_experiment(db_path=DB_PATH):
    backup_path = db_path.with_name("shop_backup.db")
    with closing(sqlite3.connect(db_path)) as conn, conn:
        with closing(sqlite3.connect(backup_path)) as backup, backup:
            conn.backup(backup)
        original = pd.read_sql_query("SELECT * FROM sales ORDER BY id", conn)
        before = {"mean": float(original.price.mean()), "median": float(original.price.median())}
        # Тест находится в транзакции: rollback восстановит БД даже при ошибке.
        conn.execute("BEGIN")
        try:
            test_id = conn.execute("""INSERT INTO sales
                (product, category, price, quantity, sale_date)
                VALUES (?, ?, ?, ?, ?)""",
                ("Тестовый выброс", "Тест", 15000000, 1, "2026-11-12")).lastrowid
            changed = pd.read_sql_query("SELECT price FROM sales", conn)
            after = {"mean": float(changed.price.mean()), "median": float(changed.price.median())}
            conn.execute("DELETE FROM sales WHERE id = ?", (test_id,))
        finally:
            conn.rollback()
        restored = pd.read_sql_query("SELECT * FROM sales ORDER BY id", conn)
        assert restored.equals(original), "Данные после эксперимента изменились"
    return {"before": before, "with_outlier": after, "restored": True}

def main():
    df = load_sales()
    if df.empty:
        raise SystemExit("В базе нет продаж для анализа")
    charts = BASE / "charts"
    charts.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    products = df.groupby("product")["revenue"].sum().sort_values(ascending=False)
    categories = df.groupby("category")["revenue"].sum().sort_values(ascending=False)
    quantities = df.groupby("product")["quantity"].sum().sort_values(ascending=False)
    daily = df.groupby("sale_date")["revenue"].sum().sort_index()
    daily_qty = df.groupby("sale_date")["quantity"].sum().sort_index()

    def save(series, filename, title, ylabel, kind="bar"):
        fig, ax = plt.subplots(figsize=(11, 5))
        if kind == "pie":
            series.plot.pie(ax=ax, autopct="%1.1f%%", startangle=90, pctdistance=.8)
            ax.set_ylabel("")
        elif kind == "line":
            ax.plot(series.index, series.values, marker="o", color="#2563eb", linewidth=2)
            ax.set_xlabel("Дата продажи")
            ax.set_ylabel(ylabel)
            ax.tick_params(axis="x", labelrotation=35)
            ax.grid(axis="y", alpha=.2)
        else:
            series.plot.bar(ax=ax, color="#2563eb", rot=45)
            ax.set_xlabel("Товар")
            ax.set_ylabel(ylabel)
            plt.setp(ax.get_xticklabels(), ha="right")
            ax.grid(axis="y", alpha=.2)
            ax.set_axisbelow(True)
        ax.set_title(title, fontsize=15, pad=15)
        fig.tight_layout()
        fig.savefig(charts / filename, dpi=150)
        plt.close(fig)

    save(products, "products.png", "Выручка по товарам", "Выручка, тенге")
    save(categories, "categories.png", "Доля выручки по категориям", "", "pie")
    save(quantities, "quantities.png", "Количество проданных товаров", "Количество, шт.")
    save(daily, "daily.png", "Выручка по дням", "Выручка, тенге", "line")
    save(daily_qty, "daily_quantity.png", "Количество проданных товаров по дням", "Количество, шт.", "line")

    quality = {"missing": df.isna().sum().astype(int).to_dict(),
               "duplicates_without_id": int(df.duplicated(subset=SALE_COLUMNS).sum()),
               "invalid_prices": int((df.price <= 0).sum()),
               "invalid_quantities": int((df.quantity <= 0).sum())}
    experiment = outlier_experiment()
    result = {**metrics(df), "categories": len(categories),
              "mean_price": float(df.price.mean()), "median_price": float(df.price.median()),
              "top3": {str(k): int(v) for k, v in products.head(3).items()},
              "category_revenue": {str(k): int(v) for k, v in categories.items()},
              "best_day": daily.idxmax().strftime("%Y-%m-%d"), "best_revenue": int(daily.max()),
              "worst_day": daily.idxmin().strftime("%Y-%m-%d"), "worst_revenue": int(daily.min()),
              "quality": quality, "outlier_experiment": experiment}
    (BASE / "analysis_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    conclusions = [
        f"Общая выручка составляет {result['revenue']:,} тенге; продано {result['quantity']} единиц в {len(df)} записях.",
        f"Лидер по выручке — {products.index[0]}: {int(products.iloc[0]):,} тенге.",
        f"Категория {categories.index[0]} приносит {categories.iloc[0] / products.sum():.1%} всей выручки.",
        f"Максимальная дневная выручка {result['best_revenue']:,} тенге получена {result['best_day']}.",
        f"Минимальная дневная выручка {result['worst_revenue']:,} тенге получена {result['worst_day']}.",
        f"Средняя цена {df.price.mean():,.2f} тенге выше медианы {df.price.median():,.2f}; дорогая техника смещает среднее вверх.",
        f"Тестовая цена 15 000 000 тенге повышает среднее с {experiment['before']['mean']:,.2f} до {experiment['with_outlier']['mean']:,.2f}, медиану — с {experiment['before']['median']:,.2f} до {experiment['with_outlier']['median']:,.2f} тенге.",
        "Выводы описывают учебные данные за наблюдаемые даты; они не доказывают сезонность или причины изменения спроса.",
    ]
    report = "# День 3 Проверка качества и исследование продаж\n\n"
    report += "Источник — shop.db. Данные синтетические, предназначены для практики.\n\n"
    report += "## Качество данных\n\n```json\n" + json.dumps(quality, ensure_ascii=False, indent=2) + "\n```\n\n"
    report += "Совпадения проверяются по полям продажи без ID. Автоматическое удаление совпадений не применяется. Даты проверяются при загрузке.\n\n"
    report += "## Эксперимент с выбросом\n\nПеред вставкой создана shop_backup.db через SQLite backup API. В транзакцию добавлена ровно одна тестовая продажа; после расчёта удалена по её ID. rollback гарантирует полное восстановление, включая счётчик ID. Равенство таблицы до и после проверено.\n\n"
    report += "## Аналитические выводы\n\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(conclusions, 1)) + "\n"
    report += "\n![Выручка по дням](charts/daily.png)\n\n![Количество по дням](charts/daily_quantity.png)\n"
    (BASE / "day3_report.md").write_text(report, encoding="utf-8")
    (BASE / "day2_report.md").write_text("# День 2 Анализ продаж\n\n" + "\n".join(conclusions[:3]) + "\n\nТоп 3 по выручке:\n" + "\n".join(f"- {k}: {v:,} тенге" for k, v in result['top3'].items()) + "\n\n![Товары](charts/products.png)\n\n![Категории](charts/categories.png)\n\n![Количество](charts/quantities.png)\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
