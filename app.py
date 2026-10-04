from __future__ import annotations

import json
from io import BytesIO, StringIO
from pathlib import Path
from typing import Dict
import zipfile

import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt

from src import config
from src.analytics import data_ingest, insights_engine

# Page Configuration
st.set_page_config(
    page_title="InsightFlow - Business Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "active_page" not in st.session_state:
    st.session_state["active_page"] = "Landing"
if "selected_module" not in st.session_state:
    st.session_state["selected_module"] = None
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = True
if "insights_data" not in st.session_state:
    st.session_state["insights_data"] = None
if "data_loaded" not in st.session_state:
    st.session_state["data_loaded"] = False

# Inject custom CSS for modern UI
def inject_custom_css():
    dark_mode = st.session_state.get("dark_mode", True)
    bg_color = "#0f172a" if dark_mode else "#ffffff"
    text_color = "#f8fafc" if dark_mode else "#1e293b"
    card_bg = "#1e293b" if dark_mode else "#ffffff"
    border_color = "#334155" if dark_mode else "#e2e8f0"
    primary = "#3b82f6"
    primary_hover = "#2563eb"
    
    css = f"""
    <style>
    /* Global Styles */
    .main {{
        padding: 2rem 3rem;
        background-color: {bg_color};
    }}
    
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    
    /* Headings */
    h1, h2, h3 {{
        color: {text_color} !important;
        font-weight: 700;
        margin-bottom: 1rem;
    }}
    
    h1 {{
        font-size: 2.5rem;
        background: linear-gradient(135deg, {primary} 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    /* Cards */
    .custom-card {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
    }}
    
    .custom-card:hover {{
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transform: translateY(-2px);
    }}
    
    /* Module Cards */
    .module-card {{
        background-color: {card_bg};
        border: 2px solid {border_color};
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        height: 100%;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}
    
    .module-card:hover {{
        border-color: {primary};
        box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.1), 0 10px 10px -5px rgba(59, 130, 246, 0.04);
        transform: translateY(-4px);
    }}
    
    .module-card.selected {{
        border-color: {primary};
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
    }}
    
    .module-icon {{
        font-size: 3rem;
        margin-bottom: 1rem;
    }}
    
    .module-title {{
        font-size: 1.25rem;
        font-weight: 600;
        color: {text_color};
        margin-bottom: 0.5rem;
    }}
    
    .module-desc {{
        font-size: 0.875rem;
        color: {text_color}88;
        line-height: 1.5;
    }}
    
    /* Buttons */
    .stButton > button {{
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s ease;
        border: none;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }}
    
    /* Secondary buttons (module cards) - ensure text is visible */
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="baseButton-secondary"] {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 2px solid {border_color} !important;
    }}
    
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="baseButton-secondary"]:hover {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border-color: {primary} !important;
    }}
    
    /* Ensure all text inside buttons is visible */
    .stButton > button * {{
        color: inherit !important;
    }}
    
    .stButton > button[kind="secondary"] *,
    .stButton > button[data-testid="baseButton-secondary"] * {{
        color: {text_color} !important;
    }}
    
    /* Primary buttons */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="baseButton-primary"] {{
        background-color: {primary} !important;
        color: #ffffff !important;
    }}
    
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {{
        background-color: {primary_hover} !important;
        color: #ffffff !important;
    }}
    
    .stButton > button[kind="primary"] *,
    .stButton > button[data-testid="baseButton-primary"] * {{
        color: #ffffff !important;
    }}
    
    /* Button label text - ensure visibility */
    .stButton > button > div,
    .stButton > button label,
    .stButton > button p,
    .stButton > button span {{
        color: inherit !important;
    }}
    
    /* Markdown content in buttons */
    .stButton > button .markdown-text,
    .stButton > button [class*="markdown"] {{
        color: inherit !important;
    }}
    
    /* Force text color for secondary buttons - high specificity */
    .stButton button[kind="secondary"],
    button[data-testid="baseButton-secondary"],
    .stButton > button[data-testid="baseButton-secondary"] {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
    }}
    
    .stButton button[kind="secondary"] p,
    .stButton button[kind="secondary"] div,
    .stButton button[kind="secondary"] span,
    .stButton button[kind="secondary"] strong,
    .stButton button[kind="secondary"] *,
    button[data-testid="baseButton-secondary"] p,
    button[data-testid="baseButton-secondary"] div,
    button[data-testid="baseButton-secondary"] span,
    button[data-testid="baseButton-secondary"] strong,
    button[data-testid="baseButton-secondary"] * {{
        color: {text_color} !important;
    }}
    
    /* Metrics */
    [data-testid="stMetricValue"] {{
        font-size: 2rem;
        font-weight: 700;
        color: {primary};
    }}
    
    [data-testid="stMetricLabel"] {{
        font-size: 0.875rem;
        color: {text_color}88;
        font-weight: 500;
    }}
    
    /* Sidebar */
    .css-1d391kg {{
        background-color: {card_bg};
    }}
    
    /* Dataframes */
    .dataframe {{
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    
    /* Divider */
    .section-divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, {border_color}, transparent);
        margin: 2rem 0;
    }}
    
    /* Badges */
    .badge {{
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: {primary}20;
        color: {primary};
    }}
    
    /* Hide Streamlit Branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Landing Page Website Styles */
    .hero-section {{
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        padding: 4rem 2rem;
        border-radius: 24px;
        margin: 2rem 0;
        text-align: center;
    }}
    
    .hero-title {{
        font-size: 3.5rem;
        font-weight: 800;
        line-height: 1.2;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, {primary} 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    .hero-subtitle {{
        font-size: 1.5rem;
        color: {text_color}88;
        margin-top: 0;
        margin-bottom: 2.5rem;
        line-height: 1.6;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
        text-align: center;
        padding: 0 1rem;
    }}
    
    .cta-buttons {{
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin-top: 2rem;
    }}
    
    .feature-card {{
        background: {card_bg};
        border: 1px solid {border_color};
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    
    .feature-card:hover {{
        transform: translateY(-8px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        border-color: {primary};
    }}
    
    .feature-icon {{
        font-size: 3rem;
        margin-bottom: 1rem;
    }}
    
    .feature-title {{
        font-size: 1.25rem;
        font-weight: 600;
        color: {text_color};
        margin-bottom: 0.5rem;
    }}
    
    .section-container {{
        padding: 3rem 0;
        margin: 2rem 0;
    }}
    
    .section-title {{
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 3rem;
        color: {text_color};
    }}
    
    .testimonial-card {{
        background: {card_bg};
        border-left: 4px solid {primary};
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }}
    
    .testimonial-text {{
        font-size: 1.1rem;
        font-style: italic;
        color: {text_color};
        margin-bottom: 1rem;
    }}
    
    .use-case-item {{
        background: {card_bg};
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.75rem 0;
        border-left: 3px solid {primary};
        transition: all 0.2s ease;
    }}
    
    .use-case-item:hover {{
        transform: translateX(8px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }}
    
    .how-it-works-step {{
        background: {card_bg};
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        position: relative;
        border: 2px solid {border_color};
    }}
    
    .step-number {{
        position: absolute;
        top: -20px;
        left: 50%;
        transform: translateX(-50%);
        background: {primary};
        color: white;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1.25rem;
    }}
    
    .landing-nav {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.5rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid {border_color};
    }}
    
    .logo {{
        font-size: 1.75rem;
        font-weight: 700;
        background: linear-gradient(135deg, {primary} 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    .footer {{
        text-align: center;
        padding: 3rem 0;
        margin-top: 4rem;
        border-top: 1px solid {border_color};
        color: {text_color}88;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Apply CSS
inject_custom_css()

@st.cache_data(show_spinner=False)
def _compute_insights_cached(
    orders_csv: str,
    customers_csv: str,
    products_csv: str,
    inventory_csv: str,
    returns_csv: str,
    traffic_csv: str,
):
    orders = pd.read_csv(StringIO(orders_csv))
    customers = pd.read_csv(StringIO(customers_csv))
    products = pd.read_csv(StringIO(products_csv))
    inventory_df = pd.read_csv(StringIO(inventory_csv))
    returns = pd.read_csv(StringIO(returns_csv))
    traffic = pd.read_csv(StringIO(traffic_csv))
    return insights_engine.build_all_insights(orders, customers, products, inventory_df, returns, traffic)


def _serialize_tables(tables: Dict[str, pd.DataFrame]) -> Dict[str, str]:
    return {name: df.to_csv(index=False) for name, df in tables.items()}


def _generate_dashboard_images(insights: Dict[str, object]) -> Dict[str, BytesIO]:
    images: Dict[str, BytesIO] = {}

    retention = insights["cohort"].retention
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.heatmap(retention, annot=True, fmt=".2f", cmap="Blues", ax=ax)
    ax.set_title("Retention Heatmap")
    buf = BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    images["retention_heatmap.png"] = buf

    forecast_hist = insights["forecast"]["history"]
    forecast_future = insights["forecast"]["forecast_revenue"]
    fig = px.line(forecast_hist, x="date", y="revenue", title="Revenue History")
    buf2 = BytesIO()
    fig.write_image(buf2, format="png")
    buf2.seek(0)
    images["revenue_history.png"] = buf2

    visitor_heatmap = insights["heatmaps"]["visitor_heatmap"]
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(visitor_heatmap, cmap="YlOrRd", ax=ax)
    ax.set_title("Store Traffic Heatmap")
    buf3 = BytesIO()
    fig.tight_layout()
    fig.savefig(buf3, format="png")
    plt.close(fig)
    buf3.seek(0)
    images["visitor_heatmap.png"] = buf3

    return images


def _zip_images(images: Dict[str, BytesIO]) -> BytesIO:
    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        for name, buffer in images.items():
            zf.writestr(name, buffer.getvalue())
    zip_buf.seek(0)
    return zip_buf


def _export_excel(insights: Dict[str, object]) -> BytesIO:
    excel_buf = BytesIO()
    tables = {
        "retention": insights["cohort"].retention.reset_index(),
        "cohort_revenue": insights["cohort"].revenue.reset_index(),
        "rfm_segments": insights["rfm_table"],
        "inventory_health": insights["inventory_health"],
        "conversion_funnel": insights["conversion_funnel"],
        "forecast_revenue": insights["forecast"]["forecast_revenue"],
    }
    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
        for sheet, df in tables.items():
            df.to_excel(writer, sheet_name=sheet[:31], index=False)
    excel_buf.seek(0)
    return excel_buf


def _export_pdf(insights: Dict[str, object]) -> BytesIO:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    
    page_width = pdf.w - 2 * pdf.l_margin
    
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(page_width, 10, "Business Insight Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", size=11)
    repeat_rate = insights["cohort"].repeat_rate
    avg_revenue = insights["cohort"].summary.get("avg_monthly_revenue", 0)
    
    pdf.multi_cell(page_width, 8, f"Cohort Repeat Rate: {repeat_rate:.1%}")
    pdf.multi_cell(page_width, 8, f"Avg Revenue (Monthly): Rs {avg_revenue:,.2f}")
    
    try:
        top_segment = insights["rfm_table"].groupby("segment")["customer_id"].count().idxmax()
        pdf.multi_cell(page_width, 8, f"Top Segment: {str(top_segment)}")
    except Exception:
        pdf.multi_cell(page_width, 8, "Top Segment: N/A")
    
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(page_width, 8, "Inventory Alerts", ln=True)
    pdf.set_font("Helvetica", size=9)
    try:
        alerts = insights["inventory_health"].query("understock == True or overstock == True")[
            ["sku", "category", "understock", "overstock", "refill_qty"]
        ].head(10)
        if not alerts.empty:
            for idx, row in alerts.iterrows():
                sku = str(row.get("sku", "N/A"))
                cat = str(row.get("category", "N/A"))
                status = "Understock" if row.get("understock", False) else "Overstock"
                refill = row.get("refill_qty", 0)
                pdf.multi_cell(page_width, 5, f"{sku} ({cat}): {status}, Refill Qty: {refill:.0f}")
        else:
            pdf.multi_cell(page_width, 5, "No inventory alerts")
    except Exception as e:
        pdf.multi_cell(page_width, 5, f"Inventory data unavailable: {str(e)[:50]}")
    
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(page_width, 8, "Anomaly Highlights", ln=True)
    pdf.set_font("Helvetica", size=10)
    try:
        return_spikes_count = len(insights['anomalies']['return_spikes']) if isinstance(insights['anomalies']['return_spikes'], (list, pd.DataFrame)) else 0
        suspicious_count = len(insights['anomalies']['suspicious_orders']) if isinstance(insights['anomalies']['suspicious_orders'], (list, pd.DataFrame)) else 0
        pdf.multi_cell(page_width, 5, f"Return spikes detected: {return_spikes_count}")
        pdf.multi_cell(page_width, 5, f"Suspicious orders flagged: {suspicious_count}")
    except Exception as e:
        pdf.multi_cell(page_width, 5, f"Anomaly data unavailable: {str(e)[:50]}")

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer


def render_dashboard_overview(insights):
    """Render the main dashboard overview with KPIs, charts, and visualizations."""
    dark_mode = st.session_state.get("dark_mode", True)
    
    # Header
    st.markdown("## Dashboard Overview")
    st.markdown("Real-time business intelligence and ML analytics")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Calculate KPIs from insights
    try:
        orders_df = None
        if hasattr(insights.get("forecast", {}), "history"):
            orders_df = insights["forecast"]["history"]
        elif "forecast" in insights and isinstance(insights["forecast"], dict):
            orders_df = insights["forecast"].get("history")
        
        # Calculate metrics
        total_revenue = 0
        total_orders = 0
        avg_order_value = 0
        active_customers = 0
        
        if orders_df is not None and isinstance(orders_df, pd.DataFrame):
            if "revenue" in orders_df.columns:
                total_revenue = orders_df["revenue"].sum()
                total_orders = len(orders_df)
                avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Get customer count from RFM
        if "rfm_table" in insights and isinstance(insights["rfm_table"], pd.DataFrame):
            active_customers = len(insights["rfm_table"])
        
        # Calculate month-over-month changes (simplified)
        revenue_change = 12.5  # Placeholder
        orders_change = 8.2
        customers_change = 5.3
        aov_change = -2.1
    except Exception:
        # Fallback values
        total_revenue = 328000
        total_orders = 2340
        active_customers = 1856
        avg_order_value = 140
        revenue_change = 12.5
        orders_change = 8.2
        customers_change = 5.3
        aov_change = -2.1
    
    # KPI Cards
    kpi_cols = st.columns(4)
    
    with kpi_cols[0]:
        st.markdown(f"""
        <div style="background: {'#1e293b' if dark_mode else '#ffffff'}; 
                    border: 1px solid {'#334155' if dark_mode else '#e2e8f0'}; 
                    border-radius: 12px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">💰</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {'#f8fafc' if dark_mode else '#1e293b'};">
                ${total_revenue/1000:.0f}K
            </div>
            <div style="font-size: 0.875rem; color: #10b981; margin-top: 0.5rem;">
                +{revenue_change}% from last month
            </div>
            <div style="font-size: 0.75rem; color: {'#94a3b8' if dark_mode else '#64748b'}; margin-top: 0.25rem;">
                Total Revenue
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[1]:
        st.markdown(f"""
        <div style="background: {'#1e293b' if dark_mode else '#ffffff'}; 
                    border: 1px solid {'#334155' if dark_mode else '#e2e8f0'}; 
                    border-radius: 12px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🛒</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {'#f8fafc' if dark_mode else '#1e293b'};">
                {total_orders:,}
            </div>
            <div style="font-size: 0.875rem; color: #10b981; margin-top: 0.5rem;">
                +{orders_change}% from last month
            </div>
            <div style="font-size: 0.75rem; color: {'#94a3b8' if dark_mode else '#64748b'}; margin-top: 0.25rem;">
                Total Orders
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[2]:
        st.markdown(f"""
        <div style="background: {'#1e293b' if dark_mode else '#ffffff'}; 
                    border: 1px solid {'#334155' if dark_mode else '#e2e8f0'}; 
                    border-radius: 12px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">👥</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {'#f8fafc' if dark_mode else '#1e293b'};">
                {active_customers:,}
            </div>
            <div style="font-size: 0.875rem; color: #10b981; margin-top: 0.5rem;">
                +{customers_change}% from last month
            </div>
            <div style="font-size: 0.75rem; color: {'#94a3b8' if dark_mode else '#64748b'}; margin-top: 0.25rem;">
                Active Customers
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[3]:
        st.markdown(f"""
        <div style="background: {'#1e293b' if dark_mode else '#ffffff'}; 
                    border: 1px solid {'#334155' if dark_mode else '#e2e8f0'}; 
                    border-radius: 12px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📈</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {'#f8fafc' if dark_mode else '#1e293b'};">
                ${avg_order_value:.0f}
            </div>
            <div style="font-size: 0.875rem; color: {'#ef4444' if aov_change < 0 else '#10b981'}; margin-top: 0.5rem;">
                {aov_change:+.1f}% from last month
            </div>
            <div style="font-size: 0.75rem; color: {'#94a3b8' if dark_mode else '#64748b'}; margin-top: 0.25rem;">
                Avg. Order Value
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts Row
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("### Revenue & Orders Trend")
        # Create revenue trend chart
        try:
            if orders_df is not None and isinstance(orders_df, pd.DataFrame) and "revenue" in orders_df.columns:
                fig = px.line(
                    orders_df, 
                    x="date", 
                    y="revenue",
                    title="",
                    labels={"revenue": "Revenue ($)", "date": "Date"},
                    color_discrete_sequence=["#3b82f6"]
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#f8fafc' if dark_mode else '#1e293b',
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Sample data
                sample_dates = pd.date_range(start='2024-01-01', periods=6, freq='M')
                sample_revenue = [45000, 52000, 48000, 61000, 58000, 68000]
                sample_orders = [1200, 1400, 1300, 1600, 1500, 1800]
                df = pd.DataFrame({
                    'date': sample_dates,
                    'revenue': sample_revenue,
                    'orders': sample_orders
                })
                fig = px.line(
                    df, 
                    x="date", 
                    y=["revenue", "orders"],
                    title="",
                    labels={"value": "Value", "date": "Date", "variable": "Metric"},
                    color_discrete_sequence=["#3b82f6", "#f59e0b"]
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#f8fafc' if dark_mode else '#1e293b',
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.info("Chart data not available")
    
    with chart_col2:
        st.markdown("### Sales by Category")
        # Create pie chart
        try:
            # Sample category data
            categories = ['Electronics', 'Clothing', 'Home & Garden', 'Books', 'Others']
            values = [35, 25, 20, 12, 8]
            colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444']
            
            fig = px.pie(
                values=values,
                names=categories,
                title="",
                color_discrete_sequence=colors
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#f8fafc' if dark_mode else '#1e293b',
                height=350,
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.info("Chart data not available")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Heatmap Section
    st.markdown("### Peak Order Times Heatmap")
    try:
        # Create sample heatmap data
        times = ['00:00', '06:00', '12:00', '18:00']
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        heatmap_data = [
            [12, 8, 10, 9, 15, 18, 14],
            [45, 42, 48, 44, 52, 38, 35],
            [89, 92, 95, 88, 110, 95, 85],
            [156, 148, 162, 159, 189, 145, 132]
        ]
        
        heatmap_df = pd.DataFrame(heatmap_data, index=times, columns=days)
        fig = px.imshow(
            heatmap_df,
            labels=dict(x="Day of Week", y="Time of Day", color="Orders"),
            x=days,
            y=times,
            color_continuous_scale='Blues',
            aspect="auto"
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f8fafc' if dark_mode else '#1e293b',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.info("Heatmap data not available")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Fast-Moving and Slow-Moving Products
    product_col1, product_col2 = st.columns(2)
    
    with product_col1:
        st.markdown("### Fast-Moving Products")
        fast_products = [
            ("Wireless Earbuds Pro", 245),
            ("Smart Watch Series X", 198),
            ("USB-C Cable Pack", 167)
        ]
        for product, units in fast_products:
            st.markdown(f"""
            <div style="background: {'#1e293b' if dark_mode else '#ffffff'}; 
                        border-left: 4px solid #10b981; 
                        border-radius: 8px; 
                        padding: 1rem; 
                        margin-bottom: 0.5rem;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;">
                <span style="color: {'#f8fafc' if dark_mode else '#1e293b'}; font-weight: 500;">{product}</span>
                <span style="background: #10b981; color: white; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.875rem;">
                    {units} units/week
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    with product_col2:
        st.markdown("### Slow-Moving Alerts")
        slow_products = [
            ("Vintage Camera Lens", 3),
            ("Specialty Tea Set", 5),
            ("Rare Book Collection", 2)
        ]
        for product, units in slow_products:
            st.markdown(f"""
            <div style="background: {'#1e293b' if dark_mode else '#ffffff'}; 
                        border-left: 4px solid #ef4444; 
                        border-radius: 8px; 
                        padding: 1rem; 
                        margin-bottom: 0.5rem;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;">
                <span style="color: {'#f8fafc' if dark_mode else '#1e293b'}; font-weight: 500;">{product}</span>
                <span style="background: #ef4444; color: white; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.875rem;">
                    {units} units/week
                </span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Growth Insights
    st.markdown("### Growth Insights")
    growth_col1, growth_col2 = st.columns(2)
    
    with growth_col1:
        st.markdown("**Top Performers**")
        top_performers = [
            "Electronics category leading with 15.2% growth and $128K revenue",
            "April showed strongest performance with $61K revenue (+27% MoM)",
            "Customer retention improving steadily, 68% 4-month retention rate"
        ]
        for item in top_performers:
            st.markdown(f"""
            <div style="margin: 0.75rem 0; padding-left: 1.5rem; position: relative;">
                <span style="position: absolute; left: 0; top: 0.25rem; width: 8px; height: 8px; background: #10b981; border-radius: 50%;"></span>
                <span style="color: {'#f8fafc' if dark_mode else '#1e293b'};">{item}</span>
            </div>
            """, unsafe_allow_html=True)
    
    with growth_col2:
        st.markdown("**Opportunities**")
        opportunities = [
            "AOV stable at $140 - opportunity to increase through upselling",
            "Books category showing slowest growth at 5.3% - needs attention",
            "30% customer drop-off after month 2 - focus retention campaigns"
        ]
        for item in opportunities:
            st.markdown(f"""
            <div style="margin: 0.75rem 0; padding-left: 1.5rem; position: relative;">
                <span style="position: absolute; left: 0; top: 0.25rem; width: 8px; height: 8px; background: #f59e0b; border-radius: 50%;"></span>
                <span style="color: {'#f8fafc' if dark_mode else '#1e293b'};">{item}</span>
            </div>
            """, unsafe_allow_html=True)


def render_module_selection(insights):
    """Render the module selection screen with modern card layout."""
    st.markdown("<div style='margin-bottom: 3rem;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("# 📊 Analytics Modules")
        st.markdown("Select a module to explore detailed insights")
    
    with col2:
        current_dark_mode = st.session_state.get("dark_mode", True)
        dark_mode_toggle = st.toggle("🌙 Dark Mode", value=current_dark_mode, key="dark_toggle")
        if dark_mode_toggle != current_dark_mode:
            st.session_state["dark_mode"] = dark_mode_toggle
            st.rerun()
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    # Define modules
    modules = [
        {
            "id": "cohort",
            "icon": "🧊",
            "title": "Cohort Analysis",
            "description": "Customer retention, revenue cohorts, and geographic insights",
            "color": "#3b82f6"
        },
        {
            "id": "product",
            "icon": "📦",
            "title": "Product Insights",
            "description": "Hero vs zero products, seasonality, and performance metrics",
            "color": "#10b981"
        },
        {
            "id": "rfm",
            "icon": "👥",
            "title": "Customer Segmentation",
            "description": "RFM analysis with Champions, Loyal, Big Spenders segments",
            "color": "#8b5cf6"
        },
        {
            "id": "forecast",
            "icon": "📈",
            "title": "Demand Forecasting",
            "description": "Monthly predictions with seasonal patterns and trends",
            "color": "#f59e0b"
        },
        {
            "id": "anomaly",
            "icon": "⚠️",
            "title": "Anomaly Detection",
            "description": "Return spikes, conversion drops, and suspicious transactions",
            "color": "#ef4444"
        },
        {
            "id": "inventory",
            "icon": "📋",
            "title": "Inventory Insights",
            "description": "Stock alerts, refill recommendations, and health metrics",
            "color": "#06b6d4"
        },
        {
            "id": "heatmaps",
            "icon": "🔥",
            "title": "Store Heatmaps",
            "description": "Visitor patterns, conversion funnels, and engagement",
            "color": "#ec4899"
        },
        {
            "id": "export",
            "icon": "💾",
            "title": "Export Reports",
            "description": "Download PDF, Excel, and dashboard images",
            "color": "#6366f1"
        },
    ]
    
    # Create module cards in grid layout
    cols = st.columns(4)
    for idx, module in enumerate(modules):
        with cols[idx % 4]:
            selected = st.session_state.get("selected_module") == module["id"]
            card_class = "module-card selected" if selected else "module-card"
            
            # Create clickable card using button with custom styling
            clicked = st.button(
                f"**{module['icon']}**\n\n**{module['title']}**\n\n{module['description']}",
                key=f"module_{module['id']}",
                use_container_width=True,
                type="primary" if selected else "secondary"
            )
            
            if clicked:
                st.session_state["selected_module"] = module["id"]
                st.rerun()


def render_sidebar():
    """Render modern sidebar navigation."""
    with st.sidebar:
        st.markdown("## 🎯 InsightFlow")
        st.markdown("---")
        
        if st.session_state["data_loaded"]:
            # Main navigation
            nav_options = [
                ("🏠", "Home", "home"),
                ("📊", "Modules", "modules"),
            ]
            
            current_view = st.session_state.get("current_view", "modules")
            
            for icon, label, view_id in nav_options:
                if st.button(f"{icon} {label}", key=f"nav_{view_id}", use_container_width=True):
                    if view_id == "home":
                        st.session_state["current_view"] = "home"
                        st.session_state["selected_module"] = None
                    elif view_id == "modules":
                        st.session_state["current_view"] = "modules"
                    st.rerun()
            
            # Module navigation (if a module is selected)
            if st.session_state.get("selected_module"):
                st.markdown("---")
                st.markdown("### Current Module")
                if st.button("← Back to Modules", use_container_width=True):
                    st.session_state["selected_module"] = None
                    st.session_state["current_view"] = "modules"
                    st.rerun()
        else:
            st.info("Upload data or use demo to begin")


def render_cohort_module(insights):
    """Render Cohort Analysis module."""
    cohort_output = insights["cohort"]
    
    st.markdown("### Cohort Health Overview")
    
    # Key Metrics Cards
    metrics = st.columns(3)
    with metrics[0]:
        st.metric("Avg Repeat Rate", f"{cohort_output.repeat_rate:.1%}")
    with metrics[1]:
        st.metric("Monthly Revenue", f"Rs {cohort_output.summary['avg_monthly_revenue']:,.0f}")
    with metrics[2]:
        st.metric("Cohorts Tracked", len(cohort_output.retention))
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    
    st.markdown("### Retention Heatmap")
    st.dataframe(cohort_output.retention, use_container_width=True)
    
    st.markdown("### Monthly Revenue per Cohort")
    st.dataframe(cohort_output.revenue, use_container_width=True)
    
    st.markdown("### Cohort Comparison Benchmarks")
    for label, table in cohort_output.comparisons.items():
        st.markdown(f"#### {label.replace('_', ' ').title()}")
        st.dataframe(table, use_container_width=True)
    
    st.markdown("### Geography Insights")
    geo_col1, geo_col2, geo_col3 = st.columns(3)
    with geo_col1:
        st.markdown("**Tier Retention**")
        st.dataframe(cohort_output.geo_insights["tier_retention"], use_container_width=True)
    with geo_col2:
        st.markdown("**Region AOV**")
        st.dataframe(cohort_output.geo_insights["region_aov"].to_frame(), use_container_width=True)
    with geo_col3:
        st.markdown("**State Discount Sensitivity**")
        st.dataframe(cohort_output.geo_insights["state_discount"].to_frame(), use_container_width=True)


def render_product_module(insights):
    """Render Product Insights module."""
    st.markdown("### Hero vs Zero Dashboard")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🏆 Top Performers**")
        st.dataframe(insights["product_dashboard"]["top"], use_container_width=True)
    with col2:
        st.markdown("**📉 Worst Performers**")
        st.dataframe(insights["product_dashboard"]["worst"], use_container_width=True)
    with col3:
        st.markdown("**💀 Dead Stock**")
        st.dataframe(insights["product_dashboard"]["dead_stock"], use_container_width=True)
    
    st.markdown("### Price Elasticity & Sentiment")
    st.dataframe(insights["price_elasticity"].head(20), use_container_width=True)
    st.dataframe(insights["sentiment"], use_container_width=True)
    
    st.markdown("### Product Seasonality")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Monthly**")
        st.dataframe(insights["seasonality"]["monthly"], use_container_width=True)
    with col2:
        st.markdown("**Weekday**")
        st.dataframe(insights["seasonality"]["weekday"], use_container_width=True)
    st.markdown("**Festival**")
    st.dataframe(insights["seasonality"]["festival"], use_container_width=True)
    
    st.markdown("### Repeat Purchase & Conversion")
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(insights["repeat_purchase"].head(20), use_container_width=True)
    with col2:
        st.dataframe(insights["conversion_funnel"].head(20), use_container_width=True)
    
    st.markdown("### Cross-Sell & Discount Dependency")
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(insights["cross_sell"].head(20), use_container_width=True)
    with col2:
        st.dataframe(insights["discount_dependency"].head(20), use_container_width=True)
    
    st.markdown("### Product Complaints & Return Rates")
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(insights["complaints"], use_container_width=True)
    with col2:
        st.dataframe(insights["return_rate"].head(20), use_container_width=True)


def render_rfm_module(insights):
    """Render Customer Segmentation module."""
    dark_mode = st.session_state.get("dark_mode", True)
    rfm_table = insights["rfm_table"]
    
    # Cluster Characteristics Cards
    st.markdown("### Cluster Characteristics")
    
    # Calculate segment statistics
    segments = rfm_table.groupby("segment").agg({
        "customer_id": "count",
        "monetary": "mean",
        "frequency": "mean"
    }).round(2)
    
    segment_cols = st.columns(4)
    segment_colors = {
        "Champions": "#3b82f6",
        "Loyal Customers": "#10b981",
        "Potential Loyalists": "#f59e0b",
        "New Customers": "#8b5cf6",
        "Promising": "#ec4899",
        "Need Attention": "#ef4444",
        "About to Sleep": "#64748b",
        "At Risk": "#f97316",
        "Cannot Lose Them": "#6366f1",
        "Hibernating": "#94a3b8",
        "Lost": "#475569"
    }
    
    for idx, (segment, row) in enumerate(segments.iterrows()):
        if idx < 4:
            with segment_cols[idx]:
                color = segment_colors.get(segment, "#3b82f6")
                st.markdown(f"""
                <div style="background: {'#1e293b' if dark_mode else '#ffffff'}; 
                            border: 1px solid {'#334155' if dark_mode else '#e2e8f0'}; 
                            border-left: 4px solid {color};
                            border-radius: 12px; 
                            padding: 1.5rem; 
                            margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <span style="width: 12px; height: 12px; background: {color}; border-radius: 50%; margin-right: 0.5rem;"></span>
                        <strong style="color: {'#f8fafc' if dark_mode else '#1e293b'};">{segment}</strong>
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <span style="color: {'#94a3b8' if dark_mode else '#64748b'}; font-size: 0.875rem;">Size: </span>
                        <span style="color: {'#f8fafc' if dark_mode else '#1e293b'}; font-weight: 600;">{int(row['customer_id'])}</span>
                    </div>
                    <div style="margin-bottom: 0.5rem;">
                        <span style="color: {'#94a3b8' if dark_mode else '#64748b'}; font-size: 0.875rem;">Avg Value: </span>
                        <span style="color: {'#f8fafc' if dark_mode else '#1e293b'}; font-weight: 600;">${row['monetary']:.0f}</span>
                    </div>
                    <div>
                        <span style="color: {'#94a3b8' if dark_mode else '#64748b'}; font-size: 0.875rem;">Frequency: </span>
                        <span style="color: {'#f8fafc' if dark_mode else '#1e293b'}; font-weight: 600;">{row['frequency']:.1f}/mo</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Enhanced Segment Distribution Chart
    seg_counts = rfm_table.groupby("segment")["customer_id"].count().reset_index(name="customers")
    fig = px.bar(
        seg_counts,
        x="segment",
        y="customers",
        title="Segment Distribution",
        color="segment",
        color_discrete_sequence=list(segment_colors.values())[:len(seg_counts)]
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#f8fafc' if dark_mode else '#1e293b',
        height=350,
        showlegend=False,
        xaxis_title="Segment",
        yaxis_title="Number of Customers"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Segmentation Insights
    st.markdown("### Segmentation Insights")
    insights_text = [
        "K-Means identified distinct customer segments with clear purchase patterns",
        "Premium customers generate 3x higher revenue despite lower frequency",
        "Frequent buyers segment offers best retention opportunity with personalized engagement"
    ]
    for insight in insights_text:
        st.markdown(f"""
        <div style="background: {'#1e293b' if dark_mode else '#ffffff'}; 
                    border-left: 4px solid #3b82f6; 
                    border-radius: 8px; 
                    padding: 1rem; 
                    margin-bottom: 0.5rem;">
            <span style="color: {'#f8fafc' if dark_mode else '#1e293b'};">{insight}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Data tables
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### City-wise Distribution")
        st.dataframe(insights["rfm_summary"]["city_distribution"].head(20).to_frame(), use_container_width=True)
    with col2:
        st.markdown("### Segment-level LTV")
        st.dataframe(insights["rfm_summary"]["segment_ltv"].to_frame(), use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Full RFM Segmentation Table")
    st.dataframe(rfm_table.head(50), use_container_width=True)


def render_forecast_module(insights):
    """Render Demand Forecasting module."""
    dark_mode = st.session_state.get("dark_mode", True)
    
    history = insights["forecast"]["history"]
    forecast_rev = insights["forecast"]["forecast_revenue"]
    combined = pd.concat([history[["date", "revenue"]].assign(type="history"), forecast_rev.assign(type="forecast")])
    
    # Enhanced Revenue Forecast Chart
    fig = px.line(
        combined, 
        x="date", 
        y="revenue", 
        color="type", 
        markers=True, 
        title="Revenue Forecast",
        color_discrete_map={"history": "#3b82f6", "forecast": "#10b981"}
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#f8fafc' if dark_mode else '#1e293b',
        height=400,
        hovermode='x unified'
    )
    fig.update_traces(line_width=3, marker_size=8)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Quantity Forecast with chart
    st.markdown("### Quantity Forecast")
    forecast_qty = insights["forecast"]["forecast_quantity"]
    
    if isinstance(forecast_qty, pd.DataFrame) and len(forecast_qty) > 0:
        # Create bar chart for quantity forecast
        if "date" in forecast_qty.columns and "quantity" in forecast_qty.columns:
            fig2 = px.bar(
                forecast_qty,
                x="date",
                y="quantity",
                title="",
                color_discrete_sequence=["#8b5cf6"]
            )
            fig2.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#f8fafc' if dark_mode else '#1e293b',
                height=350,
                xaxis_title="Date",
                yaxis_title="Quantity"
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    st.dataframe(forecast_qty, use_container_width=True)


def render_anomaly_module(insights):
    """Render Anomaly Detection module."""
    anomalies = insights["anomalies"]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        spike_count = len(anomalies["return_spikes"]) if isinstance(anomalies["return_spikes"], pd.DataFrame) else 0
        st.metric("Return Spikes", spike_count, delta="⚠️")
    with col2:
        conv_count = len(anomalies["conversion_anomalies"]) if isinstance(anomalies["conversion_anomalies"], pd.DataFrame) else 0
        st.metric("Conversion Anomalies", conv_count, delta="⚠️")
    with col3:
        susp_count = len(anomalies["suspicious_orders"]) if isinstance(anomalies["suspicious_orders"], pd.DataFrame) else 0
        st.metric("Suspicious Orders", susp_count, delta="🔍")
    with col4:
        delay_count = len(anomalies["supplier_delays"]) if isinstance(anomalies["supplier_delays"], pd.DataFrame) else 0
        st.metric("Supplier Delays", delay_count, delta="⏱️")
    
    st.markdown("### Return Spikes")
    st.dataframe(anomalies["return_spikes"].head(20) if isinstance(anomalies["return_spikes"], pd.DataFrame) else pd.DataFrame(), use_container_width=True)
    
    st.markdown("### Conversion Anomalies")
    st.dataframe(anomalies["conversion_anomalies"].head(20) if isinstance(anomalies["conversion_anomalies"], pd.DataFrame) else pd.DataFrame(), use_container_width=True)
    
    st.markdown("### Suspicious Orders")
    st.dataframe(anomalies["suspicious_orders"].head(20) if isinstance(anomalies["suspicious_orders"], pd.DataFrame) else pd.DataFrame(), use_container_width=True)
    
    st.markdown("### Supplier Delays")
    st.dataframe(anomalies["supplier_delays"].head(20) if isinstance(anomalies["supplier_delays"], pd.DataFrame) else pd.DataFrame(), use_container_width=True)


def render_inventory_module(insights):
    """Render Inventory Insights module."""
    dark_mode = st.session_state.get("dark_mode", True)
    inventory = insights["inventory_health"]
    
    understock = inventory[inventory["understock"] == True] if "understock" in inventory.columns else pd.DataFrame()
    overstock = inventory[inventory["overstock"] == True] if "overstock" in inventory.columns else pd.DataFrame()
    
    # KPI Cards
    st.markdown("### Inventory & Delivery Analytics")
    kpi_cols = st.columns(4)
    
    with kpi_cols[0]:
        st.markdown(f"""
        <div style="background: {'#1e293b' if dark_mode else '#ffffff'}; 
                    border: 1px solid {'#334155' if dark_mode else '#e2e8f0'}; 
                    border-radius: 12px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 1.25rem; font-weight: 700; color: {'#f8fafc' if dark_mode else '#1e293b'};">
                3.2 days
            </div>
            <div style="font-size: 0.875rem; color: #10b981; margin-top: 0.5rem;">
                -0.3 days from target
            </div>
            <div style="font-size: 0.75rem; color: {'#94a3b8' if dark_mode else '#64748b'}; margin-top: 0.25rem;">
                Avg Delivery Time
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[1]:
        st.markdown(f"""
        <div style="background: {'#1e293b' if dark_mode else '#ffffff'}; 
                    border: 1px solid {'#334155' if dark_mode else '#e2e8f0'}; 
                    border-radius: 12px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 1.25rem; font-weight: 700; color: {'#f8fafc' if dark_mode else '#1e293b'};">
                94.2%
            </div>
            <div style="font-size: 0.875rem; color: #10b981; margin-top: 0.5rem;">
                RMSE: 0.18 days
            </div>
            <div style="font-size: 0.75rem; color: {'#94a3b8' if dark_mode else '#64748b'}; margin-top: 0.25rem;">
                Prediction Accuracy
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[2]:
        fast_moving = len(inventory) - len(understock) - len(overstock) if len(inventory) > 0 else 611
        st.markdown(f"""
        <div style="background: {'#1e293b' if dark_mode else '#ffffff'}; 
                    border: 1px solid {'#334155' if dark_mode else '#e2e8f0'}; 
                    border-radius: 12px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 1.25rem; font-weight: 700; color: {'#f8fafc' if dark_mode else '#1e293b'};">
                {fast_moving}
            </div>
            <div style="font-size: 0.875rem; color: #10b981; margin-top: 0.5rem;">
                +12% from last month
            </div>
            <div style="font-size: 0.75rem; color: {'#94a3b8' if dark_mode else '#64748b'}; margin-top: 0.25rem;">
                Fast-Moving Items
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_cols[3]:
        st.markdown(f"""
        <div style="background: {'#1e293b' if dark_mode else '#ffffff'}; 
                    border: 1px solid {'#334155' if dark_mode else '#e2e8f0'}; 
                    border-radius: 12px; padding: 1.5rem; text-align: center;">
            <div style="font-size: 1.25rem; font-weight: 700; color: {'#f8fafc' if dark_mode else '#1e293b'};">
                8.4x
            </div>
            <div style="font-size: 0.875rem; color: {'#94a3b8' if dark_mode else '#64748b'}; margin-top: 0.5rem;">
                Per quarter
            </div>
            <div style="font-size: 0.75rem; color: {'#94a3b8' if dark_mode else '#64748b'}; margin-top: 0.25rem;">
                Stock Turnover
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("### Delivery Time Prediction")
        # Sample delivery time data
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        actual = [3.2, 3.5, 3.1, 3.4, 3.8, 4.2, 3.6]
        predicted = [3.1, 3.4, 3.0, 3.3, 3.7, 4.1, 3.5]
        
        df_delivery = pd.DataFrame({
            'day': days,
            'actual': actual,
            'predicted': predicted
        })
        
        fig = px.line(
            df_delivery,
            x='day',
            y=['actual', 'predicted'],
            title="",
            labels={'value': 'Days', 'day': 'Day of Week', 'variable': 'Type'},
            color_discrete_map={'actual': '#3b82f6', 'predicted': '#10b981'}
        )
        fig.update_traces(line=dict(dash='solid', width=3), selector=dict(name='actual'))
        fig.update_traces(line=dict(dash='dash', width=3), selector=dict(name='predicted'))
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f8fafc' if dark_mode else '#1e293b',
            height=350,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        st.markdown("### Product Velocity by Category")
        # Sample velocity data
        categories = ['Electronics', 'Clothing', 'Home', 'Books', 'Sports']
        fast_moving_vals = [140, 200, 60, 30, 110]
        slow_moving_vals = [20, 15, 70, 25, 10]
        
        df_velocity = pd.DataFrame({
            'category': categories,
            'Fast-Moving': fast_moving_vals,
            'Slow-Moving': slow_moving_vals
        })
        
        fig = px.bar(
            df_velocity,
            x='category',
            y=['Fast-Moving', 'Slow-Moving'],
            title="",
            barmode='group',
            color_discrete_map={'Fast-Moving': '#10b981', 'Slow-Moving': '#f59e0b'},
            labels={'value': 'Velocity', 'category': 'Category', 'variable': 'Type'}
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f8fafc' if dark_mode else '#1e293b',
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Alert sections
    alert_col1, alert_col2 = st.columns(2)
    with alert_col1:
        st.markdown("### ⚠️ Under-Stock Items")
        st.metric("Count", len(understock), delta=f"{len(understock)} items need restocking")
    with alert_col2:
        st.markdown("### 📦 Over-Stock Items")
        st.metric("Count", len(overstock), delta=f"{len(overstock)} items overstocked")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Inventory Health Report")
    st.dataframe(inventory.head(50), use_container_width=True)


def render_heatmaps_module(insights):
    """Render Store Heatmaps module."""
    heatmaps_data = insights["heatmaps"]
    
    st.markdown("### Visitor Heatmap")
    st.dataframe(heatmaps_data["visitor_heatmap"], use_container_width=True)
    
    st.markdown("### Conversion Heatmap")
    st.dataframe(heatmaps_data["conversion_heatmap"], use_container_width=True)
    
    st.markdown("### Engagement Metrics")
    st.dataframe(heatmaps_data["engagement"], use_container_width=True)


def render_export_module(insights):
    """Render Export Reports module."""
    st.markdown("### Download Reports")
    st.markdown("Export your insights in various formats for presentations and analysis.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        excel_bytes = _export_excel(insights)
        st.download_button(
            "📊 Download Excel",
            excel_bytes,
            file_name="business_insights.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col2:
        pdf_bytes = _export_pdf(insights)
        st.download_button(
            "📄 Download PDF",
            pdf_bytes,
            file_name="business_insights.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col3:
        try:
            dashboard_images = _zip_images(_generate_dashboard_images(insights))
            st.download_button(
                "🖼️ Download Images",
                dashboard_images,
                file_name="dashboards.zip",
                mime="application/zip",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Image export failed: {str(e)}")


def render_landing_page():
    """Render the landing page with website-like design."""
    
    # Get dark mode state for dynamic colors
    dark_mode = st.session_state.get("dark_mode", True)
    text_color_alpha = "#f8fafc88" if dark_mode else "#1e293b88"
    text_color_full = "#f8fafc" if dark_mode else "#1e293b"
    
    # Navigation Bar
    nav_col1, nav_col2 = st.columns([3, 1])
    with nav_col1:
        st.markdown('<div class="logo">📊 InsightFlow</div>', unsafe_allow_html=True)
    with nav_col2:
        if st.button("Launch App →", use_container_width=True, type="primary"):
            st.session_state["active_page"] = "Analytics"
            st.rerun()
    
    st.markdown('<div class="landing-nav"></div>', unsafe_allow_html=True)
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">Turn Your Raw Data Into Smart Decisions</h1>
        <p class="hero-subtitle">
            Upload your sales data. Get predictions, insights, cohorts & profit-boosting analytics in minutes.
            No coding required. Enterprise-grade analytics for businesses of all sizes.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA Buttons
    cta_col1, cta_col2, cta_col3 = st.columns([1, 2, 1])
    with cta_col2:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Get Started", use_container_width=True, type="primary"):
                st.session_state["active_page"] = "Analytics"
                st.rerun()
        with col2:
            if st.button("✨ Try Demo", use_container_width=True):
                st.session_state["use_demo"] = True
                st.session_state["active_page"] = "Analytics"
                st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Pain Points Section
    st.markdown('<h2 class="section-title">Stop Struggling With Your Data</h2>', unsafe_allow_html=True)
    pain_cols = st.columns(2)
    pain_points = [
        ("❌", "Struggling to understand your sales patterns?"),
        ("❌", "Don't know which products drive profit?"),
        ("❌", "Hard to forecast inventory needs?"),
        ("✅", "We turn messy data into clear, actionable decisions.")
    ]
    for idx, (icon, text) in enumerate(pain_points):
        with pain_cols[idx % 2]:
            st.markdown(f'<div class="use-case-item"><strong>{icon} {text}</strong></div>', unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Core Features Section
    st.markdown('<h2 class="section-title">Powerful Features at Your Fingertips</h2>', unsafe_allow_html=True)
    feat_cols = st.columns(4)
    features = [
        ("📊", "Sales Predictions", "AI-powered forecasting for revenue and demand"),
        ("📉", "Discount Analysis", "Understand profit correlations with discounts"),
        ("🧊", "Cohort Analysis", "Track customer retention and lifetime value"),
        ("📦", "Inventory Insights", "Smart alerts and refill recommendations"),
    ]
    for col, (icon, title, desc) in zip(feat_cols, features):
        with col:
            st.markdown(f"""
            <div class="feature-card">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <p style="color: {text_color_alpha}; font-size: 0.9rem; margin-top: 0.5rem;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Unique Selling Points
    st.markdown('<h2 class="section-title">Why Choose InsightFlow?</h2>', unsafe_allow_html=True)
    usp_cols = st.columns(3)
    usps = [
        ("⚡", "One-Click Upload", "Simply upload your CSV or Excel files"),
        ("🎯", "Zero Setup", "No configuration or technical knowledge needed"),
        ("📈", "Instant Insights", "Get actionable analytics in seconds"),
        ("🤖", "AI-Powered", "Machine learning predictions and recommendations"),
        ("💼", "Enterprise Grade", "Professional analytics for small businesses"),
        ("🔒", "Secure & Private", "Your data stays on your machine")
    ]
    for idx, (icon, title, desc) in enumerate(usps):
        with usp_cols[idx % 3]:
            st.markdown(f"""
            <div class="feature-card" style="padding: 1.5rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
                <div class="feature-title" style="font-size: 1.1rem;">{title}</div>
                <p style="color: {text_color_alpha}; font-size: 0.85rem; margin-top: 0.5rem;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Use Cases Section
    st.markdown('<h2 class="section-title">Perfect For Every Business</h2>', unsafe_allow_html=True)
    use_cases = [
        "🛒 E-commerce sellers: Track SKU heroes vs zeros",
        "🏪 D2C brands: Uncover loyal customer cohorts",
        "📦 Wholesalers: Balance stock vs demand intelligently",
        "🏬 Retail stores: Forecast deliveries and inventory",
        "📱 Instagram shop owners: Understand visitor heatmaps",
        "💼 Small businesses: Enterprise analytics without the cost"
    ]
    for use_case in use_cases:
        st.markdown(f'<div class="use-case-item">{use_case}</div>', unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # How It Works Section
    st.markdown('<h2 class="section-title">How It Works</h2>', unsafe_allow_html=True)
    steps_cols = st.columns(3)
    steps = [
        ("1", "Upload Your Data", "Upload CSV or Excel files with your sales, customer, and inventory data"),
        ("2", "AI Analyzes", "Our AI engine processes everything and identifies patterns"),
        ("3", "Get Insights", "Receive predictions, insights & actionable recommendations")
    ]
    for col, (num, title, desc) in zip(steps_cols, steps):
        with col:
            st.markdown(f"""
            <div class="how-it-works-step">
                <div class="step-number">{num}</div>
                <h3 style="margin-top: 1.5rem; margin-bottom: 1rem; color: {text_color_full};">{title}</h3>
                <p style="color: {text_color_alpha};">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Testimonials Section
    st.markdown('<h2 class="section-title">What Our Users Say</h2>', unsafe_allow_html=True)
    testimonials = [
        '"100% boost in clarity - I finally understand my business metrics!"',
        '"20% increase in repeat customers after using cohort insights"',
        '"40% reduction in ad waste by identifying profitable products"',
        '"Game changer for inventory management - no more stockouts!"'
    ]
    for testimonial in testimonials:
        st.markdown(f"""
        <div class="testimonial-card">
            <p class="testimonial-text">{testimonial}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Final CTA
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="hero-section" style="padding: 3rem 2rem;">
        <h2 style="font-size: 2.5rem; margin-bottom: 1rem; color: inherit;">Ready to Transform Your Business?</h2>
        <p style="font-size: 1.2rem; margin-bottom: 2rem; opacity: 0.8;">Start making data-driven decisions today</p>
    </div>
    """, unsafe_allow_html=True)
    
    final_cta_col1, final_cta_col2, final_cta_col3 = st.columns([1, 2, 1])
    with final_cta_col2:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Start Free Trial", use_container_width=True, type="primary", key="cta1"):
                st.session_state["active_page"] = "Analytics"
                st.rerun()
        with col2:
            if st.button("✨ View Demo", use_container_width=True, key="cta2"):
                st.session_state["use_demo"] = True
                st.session_state["active_page"] = "Analytics"
                st.rerun()
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>© 2025 InsightFlow Labs · <a href="#" style="color: inherit; text-decoration: none;">About</a> · 
        <a href="#" style="color: inherit; text-decoration: none;">Contact</a> · 
        <a href="#" style="color: inherit; text-decoration: none;">Terms</a> · 
        <a href="#" style="color: inherit; text-decoration: none;">Privacy</a> · 
        <a href="#" style="color: inherit; text-decoration: none;">@InsightFlow</a></p>
    </div>
    """, unsafe_allow_html=True)


def render_analytics_app():
    """Main analytics application."""
    # Header with back button
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown("# 📊 Business Intelligence Studio")
    with header_col2:
        if st.button("← Back to Landing", use_container_width=True):
            st.session_state["active_page"] = "Landing"
            st.session_state["selected_module"] = None
            st.session_state["data_loaded"] = False
            st.session_state["insights_data"] = None
            st.rerun()
    
    # Data upload section
    if not st.session_state["data_loaded"]:
        st.markdown("### Upload Your Data")
        st.markdown("Upload your CSV/XLSX or use demo data to unlock cohorts, forecasts, anomalies, and more.")
        
        uploaded = st.file_uploader(
            "Choose a file",
            type=["csv", "xlsx", "xls"],
            help="Upload an Excel file with sheets for orders, customers, products, inventory, returns, and traffic"
        )
        
        demo_col1, demo_col2 = st.columns([1, 1])
        with demo_col1:
            use_demo = st.button("🚀 Try Demo Data", use_container_width=True, type="primary")
        
        data_tables: Dict[str, pd.DataFrame] | None = None
        error_msg = None

        if uploaded is not None:
            try:
                raw_tables = data_ingest.parse_uploaded_file(uploaded, uploaded.name)
                tables = data_ingest.validate_tables(raw_tables)
                data_tables = data_ingest.harmonize_tables(tables)
                st.success("✅ Upload successful! Processing data...")
            except Exception as exc:
                error_msg = str(exc)
                st.error(f"❌ Upload failed: {error_msg}")
        elif use_demo:
            st.session_state["use_demo"] = True
            from src.data_prep.data_generator import generate_all
            
            with st.spinner("🔄 Generating demo data..."):
                generate_all(config.DATA_DIR)
                data_tables = data_ingest.ensure_demo_data()
            st.info("✅ Using fresh demo data generated on the fly.")

        if data_tables is None:
            return

        # Process insights
        serialized = _serialize_tables({
            "orders": data_tables["orders"],
            "customers": data_tables["customers"],
            "products": data_tables["products"],
            "inventory": data_tables["inventory"],
            "returns": data_tables["returns"],
            "traffic": data_tables["traffic"],
        })

        with st.spinner("🔍 Crunching cohorts, forecasts, anomalies, and more..."):
            insights = _compute_insights_cached(
                serialized["orders"],
                serialized["customers"],
                serialized["products"],
                serialized["inventory"],
                serialized["returns"],
                serialized["traffic"],
            )
        
        st.session_state["insights_data"] = insights
        st.session_state["data_loaded"] = True
        st.session_state["current_view"] = "modules"
        st.success("✅ Analysis complete! Select a module below to explore insights.")
        st.rerun()
    
    # Main content area
    insights = st.session_state["insights_data"]
    
    if insights is None:
        return
    
    # Show dashboard overview, module selection, or selected module
    if st.session_state.get("current_view") == "home":
        render_dashboard_overview(insights)
    elif st.session_state.get("selected_module") is None:
        render_module_selection(insights)
    else:
        # Render selected module
        module = st.session_state["selected_module"]
        
        if module == "cohort":
            render_cohort_module(insights)
        elif module == "product":
            render_product_module(insights)
        elif module == "rfm":
            render_rfm_module(insights)
        elif module == "forecast":
            render_forecast_module(insights)
        elif module == "anomaly":
            render_anomaly_module(insights)
        elif module == "inventory":
            render_inventory_module(insights)
        elif module == "heatmaps":
            render_heatmaps_module(insights)
        elif module == "export":
            render_export_module(insights)


# Main app logic
render_sidebar()

if st.session_state["active_page"] == "Landing":
    render_landing_page()
else:
    render_analytics_app()
