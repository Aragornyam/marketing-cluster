import os
import pandas as pd
import requests
import streamlit as st
from sqlalchemy import create_engine, text

from ui_components import (
    apply_styles,
    build_cpa_chart,
    build_profit_chart,
    render_sidebar,
    render_status_bar,
)

st.set_page_config(
    page_title="MarketingOps | Аналитическая платформа",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = os.getenv("API_URL", "http://backend_service:8000")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

if "operation_status" not in st.session_state:
    st.session_state["operation_status"] = None


@st.cache_resource(show_spinner=False)
def get_db_engine():
    return create_engine(
        DB_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args={"connect_timeout": 3},
    )


@st.cache_data(ttl=15, show_spinner=False)
def fetch_raw_stats():
    try:
        res = requests.get(f"{API_URL}/stats", timeout=3)
        if res.status_code == 200:
            return res.json().get("total_records", 0), True
    except Exception:
        pass
    return 0, False


@st.cache_data(ttl=15, show_spinner=False)
def fetch_datamart():
    try:
        engine = get_db_engine()
        query = text("SELECT * FROM campaign_roi_mart ORDER BY net_profit DESC")
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df, True
    except Exception:
        return pd.DataFrame(), False


def clear_data_cache():
    fetch_raw_stats.clear()
    fetch_datamart.clear()


render_sidebar(on_refresh_callback=clear_data_cache)
apply_styles()

total_records, api_ok = fetch_raw_stats()
df_mart, db_mart_ok = fetch_datamart()

header_left, header_right = st.columns([2, 1])
with header_left:
    st.title("Панель управления маркетинговыми данными")
    st.caption(
        "Контроль потоков данных рекламных кабинетов, управление регламентными ETL-процессами "
        "и анализ коммерческой эффективности кампаний."
    )
with header_right:
    render_status_bar(api_ok=api_ok, db_ok=db_mart_ok)


st.markdown("#### Управление потоками данных")

col_import, col_etl = st.columns(2)

with col_import:
    with st.container(border=True):
        st.markdown("**Импорт первичной статистики (`marketing_metrics`)**")
        st.caption(
            "Загрузка пакета сырых событий по активным рекламным кампаниям (показы, клики, затраты, конверсии)."
        )
        if st.button("Загрузить новые метрики", use_container_width=True):
            with st.spinner("Выполняется приём данных от источника..."):
                try:
                    res = requests.post(f"{API_URL}/load_data", timeout=10)
                    if res.status_code == 200:
                        clear_data_cache()
                        msg = res.json().get("message", "Пакет сырых данных успешно записан в хранилище.")
                        st.session_state["operation_status"] = ("success", f"Импорт завершён: {msg}")
                        st.rerun()
                    else:
                        st.session_state["operation_status"] = (
                            "error",
                            f"Сбой при загрузке метрик (HTTP {res.status_code}).",
                        )
                except Exception as err:
                    st.session_state["operation_status"] = (
                        "error",
                        f"Не удалось установить соединение с Backend API: {err}",
                    )

with col_etl:
    with st.container(border=True):
        st.markdown("**Агрегация аналитической витрины (`campaign_roi_mart`)**")
        st.caption(
            "Запуск ETL-трансформации: сведение затрат и выручки, пересчёт коэффициентов CPA, ROAS и чистой прибыли."
        )
        if st.button("Пересчитать витрину данных (ETL)", type="primary", use_container_width=True):
            with st.spinner("Расчёт агрегированных показателей..."):
                try:
                    res = requests.post(f"{API_URL}/build_datamart", timeout=15)
                    if res.status_code == 200:
                        clear_data_cache()
                        msg = res.json().get("message", "Витрина campaign_roi_mart успешно обновлена.")
                        st.session_state["operation_status"] = ("success", f"ETL-процесс выполнен: {msg}")
                        st.rerun()
                    else:
                        st.session_state["operation_status"] = (
                            "error",
                            f"Ошибка построения витрины данных (HTTP {res.status_code}).",
                        )
                except Exception as err:
                    st.session_state["operation_status"] = (
                        "error",
                        f"Ошибка обращения к API при запуске ETL: {err}",
                    )

if st.session_state["operation_status"]:
    status_type, status_text = st.session_state["operation_status"]
    if status_type == "success":
        st.success(status_text)
    else:
        st.error(status_text)


st.markdown("#### Сводные показатели")
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        label="Записей в сыром слое (Raw)",
        value=f"{total_records:,}".replace(",", " ") if api_ok else "Нет связи",
        delta="Таблица marketing_metrics",
        delta_color="off",
    )

has_mart_data = (
    not df_mart.empty
    and {"net_profit", "roas", "cpa", "campaign_name"}.issubset(df_mart.columns)
)

if has_mart_data:
    total_profit = df_mart["net_profit"].sum()
    avg_roas = df_mart["roas"].mean()
    avg_cpa = df_mart["cpa"].mean()
    top_campaign = str(df_mart.iloc[0]["campaign_name"])

    with m2:
        st.metric(
            label="Суммарная чистая прибыль",
            value=f"${total_profit:,.2f}".replace(",", " "),
            delta=f"Активных кампаний: {len(df_mart)}",
            delta_color="off",
        )
    with m3:
        st.metric(
            label="Средний ROAS по портфелю",
            value=f"{avg_roas:.2f}x",
            delta="Рентабельно" if avg_roas >= 1.0 else "Ниже окупаемости",
            delta_color="normal" if avg_roas >= 1.0 else "inverse",
        )
    with m4:
        st.metric(
            label="Средний CPA / Лидер прибыли",
            value=f"${avg_cpa:,.2f}".replace(",", " "),
            delta=f"Лидер: {top_campaign}",
            delta_color="off",
        )
else:
    with m2:
        st.metric("Суммарная чистая прибыль", "—", "Нет данных витрины", delta_color="off")
    with m3:
        st.metric("Средний ROAS по портфелю", "—", "Требуется расчёт ETL", delta_color="off")
    with m4:
        st.metric("Средний CPA / Лидер прибыли", "—", "Требуется расчёт ETL", delta_color="off")

st.divider()


st.markdown("#### Эффективность рекламных кампаний (A/B-анализ площадок)")

if not db_mart_ok:
    st.info(
        "Витрина `campaign_roi_mart` ещё не инициализирована в базе данных. "
        "Загрузите первичные метрики и запустите пересчёт витрины данных (ETL)."
    )
elif df_mart.empty:
    st.warning(
        "Таблица витрины `campaign_roi_mart` не содержит записей. "
        "Выполните импорт метрик и запустите расчёт ETL."
    )
else:
    f_col1, f_col2 = st.columns([2, 1])
    with f_col1:
        campaigns_list = df_mart["campaign_name"].unique().tolist()
        selected = st.multiselect(
            "Рекламные кампании",
            options=campaigns_list,
            default=campaigns_list,
            placeholder="Выберите кампании для отображения...",
        )
    with f_col2:
        sort_by = st.selectbox(
            "Сортировка данных",
            options=[
                "Чистая прибыль (по убыванию)",
                "Рентабельность ROAS (по убыванию)",
                "Стоимость привлечения CPA (по возрастанию)",
            ],
        )

    df_filtered = df_mart[df_mart["campaign_name"].isin(selected)].copy()
    if sort_by == "Чистая прибыль (по убыванию)":
        df_filtered = df_filtered.sort_values("net_profit", ascending=False)
    elif sort_by == "Рентабельность ROAS (по убыванию)":
        df_filtered = df_filtered.sort_values("roas", ascending=False)
    else:
        df_filtered = df_filtered.sort_values("cpa", ascending=True)

    if df_filtered.empty:
        st.warning("Не выбрано ни одной кампании в фильтре.")
    else:
        chart_left, chart_right = st.columns([3, 2])
        with chart_left:
            with st.container(border=True):
                fig_profit = build_profit_chart(df_filtered)
                st.plotly_chart(
                    fig_profit,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
        with chart_right:
            with st.container(border=True):
                fig_cpa = build_cpa_chart(df_filtered)
                st.plotly_chart(
                    fig_cpa,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

        st.markdown("##### Детализированная ведомость по кампаниям")
        col_config = {
            "campaign_name": st.column_config.TextColumn("Рекламная кампания"),
            "net_profit": st.column_config.NumberColumn("Чистая прибыль ($)", format="$%.2f"),
            "roas": st.column_config.NumberColumn("ROAS (коэфф.)", format="%.2fx"),
            "cpa": st.column_config.NumberColumn("CPA ($)", format="$%.2f"),
            "total_spend": st.column_config.NumberColumn("Затраты ($)", format="$%.2f"),
            "total_revenue": st.column_config.NumberColumn("Выручка ($)", format="$%.2f"),
            "total_conversions": st.column_config.NumberColumn("Конверсии", format="%d"),
            "total_clicks": st.column_config.NumberColumn("Клики", format="%d"),
            "total_impressions": st.column_config.NumberColumn("Показы", format="%d"),
        }

        st.dataframe(
            df_filtered,
            column_config=col_config,
            hide_index=True,
            use_container_width=True,
        )

        csv_data = df_filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="Экспортировать таблицу в CSV",
            data=csv_data,
            file_name="campaign_roi_mart.csv",
            mime="text/csv",
        )