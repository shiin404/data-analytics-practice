"""День 4: интерактивное приложение. python -m streamlit run dashboard.py"""
import streamlit as st
import plotly.express as px
from analytics_core import load_sales, filter_sales, metrics, csv_bytes

st.set_page_config(page_title="Аналитика магазина", page_icon="📊", layout="wide")
st.title("Аналитика интернет-магазина")
st.caption("Учебные продажи · SQLite → Pandas → Plotly · суммы в тенге")

try:
    # Без кэша: каждый перезапуск интерфейса читает актуальные данные SQLite.
    df = load_sales()
except (FileNotFoundError, ValueError) as error:
    st.error(str(error))
    st.stop()

with st.sidebar:
    st.header("Фильтры продаж")
    st.button("Обновить данные")
    categories = sorted(df["category"].unique().tolist())
    selected_categories = st.multiselect("Категории", categories, default=categories)
    products = sorted(df["product"].unique().tolist())
    selected_products = st.multiselect("Товары", products, default=products)
    st.caption("Очистите выбор, чтобы проверить пустой результат. Фильтры применяются совместно.")

filtered = filter_sales(df, selected_categories, selected_products)
m = metrics(filtered)
cols = st.columns(4)
cols[0].metric("Общая выручка", f"{m['revenue']:,.0f} ₸")
cols[1].metric("Продано товаров", f"{m['quantity']} шт.")
cols[2].metric("Записей о продажах", str(m['records']))
cols[3].metric("Средняя цена", f"{m['mean_price']:,.2f} ₸" if m['records'] else "—")
st.caption("Средняя цена — среднее по записям о продажах, без взвешивания по количеству.")

if filtered.empty:
    st.info("Нет данных для выбранных категорий и товаров. Измените фильтры слева.")
else:
    left, right = st.columns([3, 2])
    products_data = filtered.groupby("product", as_index=False)["revenue"].sum().sort_values("revenue", ascending=False)
    categories_data = filtered.groupby("category", as_index=False)["revenue"].sum()
    with left:
        st.subheader("Выручка по товарам")
        fig = px.bar(products_data, x="product", y="revenue", labels={"product": "Товар", "revenue": "Выручка, ₸"}, color_discrete_sequence=["#2563eb"])
        st.plotly_chart(fig, width="stretch")
    with right:
        st.subheader("Доля категорий")
        fig = px.pie(categories_data, names="category", values="revenue", hole=.4, labels={"category": "Категория", "revenue": "Выручка, ₸"})
        st.plotly_chart(fig, width="stretch")
    st.subheader("Динамика выручки")
    daily = filtered.groupby("sale_date", as_index=False)["revenue"].sum().sort_values("sale_date")
    fig = px.line(daily, x="sale_date", y="revenue", markers=True, labels={"sale_date": "Дата", "revenue": "Выручка, ₸"})
    st.plotly_chart(fig, width="stretch")

st.subheader("Данные выбранных продаж")
st.dataframe(filtered, hide_index=True, width="stretch")
st.download_button("Скачать CSV", csv_bytes(filtered), file_name="sales_report.csv", mime="text/csv")
st.caption("CSV содержит только выбранные продажи. Кодировка UTF-8 с BOM поддерживает кириллицу в Excel.")

