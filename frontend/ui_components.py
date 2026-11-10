from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ASSETS_DIR = Path(__file__).parent / "assets"


def load_asset(filename: str) -> str:
    """Читает содержимое CSS или SVG файла из папки assets."""
    file_path = ASSETS_DIR / filename
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return ""


def apply_styles() -> None:
    """Подключает базовый CSS и файл тёмной темы."""
    base_css = load_asset("base.css")
    theme_css = load_asset("dark.css")
    st.markdown(f"<style>{base_css}\n{theme_css}</style>", unsafe_allow_html=True)


def render_sidebar(on_refresh_callback) -> None:
    """Отрисовывает боковую панель навигации."""
    jupyter_svg = load_asset("jupyter.svg")
    metabase_svg = load_asset("metabase.svg")

    with st.sidebar:
        st.markdown(
            """
            <div class="brand-header">
                <div>
                    <div class="brand-title">MarketingOps</div>
                    <div class="brand-subtitle">Платформа сквозной аналитики</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="nav-section-label">Инфраструктура</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
            <a href="http://127.0.0.1:82" target="_blank" class="service-link">
                <div class="service-icon-box">{jupyter_svg}</div>
                <div>
                    <div class="service-name">Jupyter Lab</div>
                    <div class="service-caption">Разработка ETL-пайплайнов</div>
                </div>
            </a>
            <a href="http://127.0.0.1:81" target="_blank" class="service-link">
                <div class="service-icon-box">{metabase_svg}</div>
                <div>
                    <div class="service-name">Metabase BI</div>
                    <div class="service-caption">Витрины и дашборды отчётности</div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Синхронизировать данные", use_container_width=True):
            on_refresh_callback()
            st.rerun()

        st.markdown('<div class="nav-section-label">Документация</div>', unsafe_allow_html=True)
        with st.expander("Справка"):
            st.markdown(
                """
                **Методология расчёта показателей:**
                
                **CPA (Cost Per Action)** — отношение рекламного бюджета к числу целевых конверсий. Отражает фактическую стоимость привлечения клиента.
                
                **ROAS (Return on Ad Spend)** — рентабельность инвестиций в рекламу (отношение выручки к затратам). Значение выше `1.0` подтверждает окупаемость канала.
                
                **Чистая прибыль (Net Profit)** — разница между валовой выручкой от кампании и расходами на закупку трафика.
                """
            )


def render_status_bar(api_ok: bool, db_ok: bool) -> None:
    """Отображает компактный индикатор состояния сервисов в правой части шапки."""
    api_dot = "dot-online" if api_ok else "dot-offline"
    api_text = "Активен" if api_ok else "Недоступен"

    db_dot = "dot-online" if db_ok else "dot-wait"
    db_text = "Синхронизирована" if db_ok else "Ожидает расчёта"

    st.markdown(
        f"""
        <div class="status-bar">
            <div class="status-item">
                <span class="status-dot {api_dot}"></span>
                <span>API-шлюз: <b>{api_text}</b></span>
            </div>
            <div class="status-item">
                <span class="status-dot {db_dot}"></span>
                <span>Витрина DWH: <b>{db_text}</b></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_profit_chart(df: "pd.DataFrame"):
    """Строит высококонтрастный график чистой прибыли и ROAS."""
    text_color = "#F8FAFC"
    grid_color = "#334155"
    bg_color = "#1E293B"
    color_scale = "Tealgrn"

    fig = px.bar(
        df,
        x="campaign_name",
        y="net_profit",
        color="roas",
        text_auto=",.0f",
        color_continuous_scale=color_scale,
        title="Финансовый результат и рентабельность (ROAS) по кампаниям",
        labels={
            "campaign_name": "Рекламная кампания",
            "net_profit": "Чистая прибыль ($)",
            "roas": "ROAS",
        },
    )
    fig.update_traces(
        textfont=dict(color=text_color, size=12),
        textposition="outside",
        cliponaxis=False,
        marker_line_color=grid_color,
        marker_line_width=1,
    )
    fig.update_layout(
        font=dict(color=text_color, family="sans-serif"),
        title_font=dict(size=15, color=text_color),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        xaxis=dict(
            title="Кампания / Рекламная площадка",
            title_font=dict(color=text_color),
            tickfont=dict(color=text_color),
            showgrid=False,
            linecolor=grid_color,
        ),
        yaxis=dict(
            title="Чистая прибыль ($)",
            title_font=dict(color=text_color),
            tickfont=dict(color=text_color),
            gridcolor=grid_color,
            zerolinecolor=grid_color,
        ),
        coloraxis_colorbar=dict(
            title=dict(text="ROAS", font=dict(color=text_color)),
            tickfont=dict(color=text_color),
        ),
        margin=dict(l=20, r=20, t=55, b=20),
    )
    return fig


def build_cpa_chart(df: "pd.DataFrame"):
    """Строит горизонтальный график стоимости целевого действия (CPA)."""
    text_color = "#F8FAFC"
    grid_color = "#334155"
    bg_color = "#1E293B"
    bar_color = "#3B82F6"

    fig = px.bar(
        df,
        x="cpa",
        y="campaign_name",
        orientation="h",
        text_auto=",.2f",
        title="Стоимость привлечения конверсии (CPA, $)",
        labels={
            "campaign_name": "Кампания",
            "cpa": "CPA ($)",
        },
    )
    fig.update_traces(
        marker_color=bar_color,
        textfont=dict(color=text_color, size=12),
        textposition="outside",
        cliponaxis=False,
    )
    fig.update_layout(
        font=dict(color=text_color, family="sans-serif"),
        title_font=dict(size=15, color=text_color),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        xaxis=dict(
            title="CPA ($)",
            title_font=dict(color=text_color),
            tickfont=dict(color=text_color),
            gridcolor=grid_color,
            linecolor=grid_color,
        ),
        yaxis=dict(
            title="",
            tickfont=dict(color=text_color),
            showgrid=False,
        ),
        margin=dict(l=20, r=40, t=55, b=20),
    )
    return fig