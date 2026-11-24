# Аналитика интернет-магазина

Практика по Python и SQL. Данные хранятся в SQLite, анализ и графики — на Pandas, Matplotlib и Plotly. Интерфейс сделан на Streamlit.

## Запуск

Нужен Python 3.12+.

```bash
python -m pip install -r requirements.txt
python setup_db.py
python add_day5_sales.py
python analysis.py
python -m streamlit run dashboard.py
```

В готовой базе 25 продаж и 5 категорий. Повторный запуск не добавляет записи заново.

## Что есть

Фильтры по категориям и товарам, 4 показателя, 3 интерактивных графика, таблица и выгрузка CSV. Пустой выбор тоже обрабатывается.

Выручка — 3 139 000 ₸, продано 160 товаров. Данные учебные.

- `check_db.py` — SQL-запросы.
- `analysis.py` — расчёты и 5 графиков в `charts/`.
- `day2_report.md`, `day3_report.md` — выводы.
- `add_day5_sales.py` — 5 новых продаж и категория «Спорт».
- `report/practice_report.docx` — итоговый отчёт.

Проверка: `python test_project.py`. Дополнительно: `python test_dashboard.py`.

![Приложение](screenshots/dashboard.png)
