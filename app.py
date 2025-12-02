import base64
import json
import pathlib
from datetime import datetime, timedelta, date
from typing import Dict, List
import hashlib

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 👉 Supabase helper (reads the live leads table)
from supabase_client import get_leads_df


# =========================================================
#                 PAGE CONFIG & GLOBAL THEME
# =========================================================

st.set_page_config(
    page_title="Red Panda Leads – Stats Dashboard",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root {
        --rpl-bg-main: #0B0B0E;
        --rpl-bg-card: #111118;
        --rpl-bg-card-soft: #181820;
        --rpl-bg-sidebar: #202028;
        --rpl-border-subtle: #26262E;
        --rpl-text-main: #FFFFFF;
        --rpl-text-muted: #CCCCCC;
    }

    [data-testid="stAppViewContainer"] {
        background-color: var(--rpl-bg-main) !important;
    }

    [data-testid="stHeader"] {
        background-color: var(--rpl-bg-main) !important;
        border-bottom: 1px solid #000000;
    }

    [data-testid="stSidebar"] {
        background-color: var(--rpl-bg-sidebar) !important;
        padding-top: 18px !important;
    }

    .block-container {
        padding-top: 1.2rem !important;
    }

    .rpl-card {
        background-color: var(--rpl-bg-card-soft);
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.35);
    }

    .sidebar-logo-container {
        display: flex;
        align-items: center;
        padding: 6px 18px 18px 18px;
    }
    .sidebar-logo-img {
        height: 48px;
    }

    [data-testid="stDataFrame"],
    [data-testid="stDataEditor"] {
        background-color: transparent !important;
    }

    [data-testid="stDataFrame"] thead tr th,
    [data-testid="stDataEditor"] thead tr th {
        background-color: #181820 !important;
        color: var(--rpl-text-main) !important;
        border-color: var(--rpl-border-subtle) !important;
    }

    [data-testid="stDataFrame"] tbody tr td,
    [data-testid="stDataEditor"] tbody tr td {
        background-color: #0C0C11 !important;
        color: var(--rpl-text-main) !important;
        border-color: var(--rpl-border-subtle) !important;
    }

    [data-testid="stDataFrame"] tbody tr:nth-child(even) td,
    [data-testid="stDataEditor"] tbody tr:nth-child(even) td {
        background-color: #0F0F15 !important;
    }

    [data-testid="stDataFrame"] tbody tr:hover td,
    [data-testid="stDataEditor"] tbody tr:hover td {
        background-color: #1C1C24 !important;
    }

    .stButton>button {
        border-radius: 999px;
        padding: 0.30rem 1.10rem;
        font-size: 0.85rem;
    }

    #add-graph-container button {
        width: 40px !important;
        height: 40px !important;
        background-color: #3a3a3a !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.35) !important;
        padding: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
#                          PATHS & CONSTANTS
# =========================================================

BASE_DIR = pathlib.Path(__file__).parent
DATA_FILE = BASE_DIR / "stats_data.csv"
COLOR_FILE = BASE_DIR / "stats_colors.json"
LOGO_FILE = BASE_DIR / "red_panda_logo.png"
VIEWS_FILE = BASE_DIR / "saved_views.json"
CONDITIONS_FILE = BASE_DIR / "weekly_conditions.json"

DEFAULT_PALETTE = [
    "#FF4B4B", "#FF9F1C", "#FFEA00", "#4ECDC4", "#1E90FF",
    "#2ECC71", "#9B59B6", "#E67E22", "#F1C40F", "#16A085"
]

PRESET_NAMES = [
    "Staff meeting", "James stats", "Nick stats",
    "Alex stats", "Shiloh's stats", "Jake's stats",
]

CONDITION_LEVELS = ["Non-Existence", "Danger", "Emergency", "Normal", "Affluence", "Power"]

STAFF_MEMBERS = ["James", "Nick", "Alex", "Shiloh", "Jake"]


# =========================================================
#                MASTER LIST OF ALL RPL STAT COLUMNS
# =========================================================

MASTER_STATS = [
    # Jake
    "New Div 4 Content", "New Div 6 Content",
    "Div 4 - CTR", "Div 6 - CTR",

    # Shiloh
    "Weighted Digital Assets", "Innovation Counts",
    "Automation Breaks", "Software Development Expansion Index",

    # Alex
    "Google – Simple Close – Adspend",
    "FB – Simple Close – Adspend",
    "FB – True Blue Homes – Adspend",
    "Leadzolo Supplement", "Property Leads Supplement",
    "Total Adspend",
    "Fallback (Listed)", "Fallback (Unsold)", "Fallback (Rejected)",
    "Total Leads", "Sellable Leads",
    "Leads Delivered (Provisional)",
    "Leads Delivered (Refunded)",
    "Leads Delivered (Corrected)",
    "VLD (Provisional)", "VLD (Refunded)", "VLD (Corrected)",

    # Nick
    "New Identities To CRM", "Total # of Identities",
    "Outflow", "# Leads Bought", "New Clients",
    "Active Clients", "Finished Packages", "Resigns",
    "Churn %", "Gross Income",

    # James
    "CAC", "Total Profit", "Profit Margin %",
]

STATS_BY_OWNER = {
    "Jake": [
        "New Div 4 Content", "New Div 6 Content",
        "Div 4 - CTR", "Div 6 - CTR",
    ],
    "Shiloh": [
        "Weighted Digital Assets", "Innovation Counts",
        "Automation Breaks", "Software Development Expansion Index",
    ],
    "Alex": [
        "Google – Simple Close – Adspend",
        "FB – Simple Close – Adspend",
        "FB – True Blue Homes – Adspend",
        "Leadzolo Supplement", "Property Leads Supplement",
        "Total Adspend",
        "Fallback (Listed)", "Fallback (Unsold)", "Fallback (Rejected)",
        "Total Leads", "Sellable Leads",
        "Leads Delivered (Provisional)", "Leads Delivered (Refunded)",
        "Leads Delivered (Corrected)",
        "VLD (Provisional)", "VLD (Refunded)", "VLD (Corrected)",
    ],
    "Nick": [
        "New Identities To CRM", "Total # of Identities",
        "Outflow", "# Leads Bought", "New Clients",
        "Active Clients", "Finished Packages", "Resigns",
        "Churn %", "Gross Income",
    ],
    "James": [
        "CAC", "Total Profit", "Profit Margin %",
        "VLD (Corrected)",
    ],
}


# =========================================================
#                        LOGO LOADER
# =========================================================

def get_logo_base64() -> str | None:
    try:
        if LOGO_FILE.exists():
            with open(LOGO_FILE, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass
    return None


LOGO_B64 = get_logo_base64()


# =========================================================
#                FORMULA CALCULATIONS (NEW)
# =========================================================

def apply_formulas(df: pd.DataFrame) -> pd.DataFrame:
    """Applies all derived-column formulas safely."""

    def g(col):
        return pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0)

    # Software Development Expansion Index
    df["Software Development Expansion Index"] = (
        g("Weighted Digital Assets")
        + g("Innovation Counts")
        - g("Automation Breaks")
    )

    # TOTAL AD SPEND
    df["Total Adspend"] = (
        g("Google – Simple Close – Adspend")
        + g("FB – Simple Close – Adspend")
        + g("FB – True Blue Homes – Adspend")
        + g("Leadzolo Supplement")
        + g("Property Leads Supplement")
    )

    # TOTAL LEADS
    df["Total Leads"] = (
        g("Fallback (Listed)")
        + g("Fallback (Unsold)")
        + g("Fallback (Rejected)")
        + g("Leads Delivered (Provisional)")
    )

    # SELLABLE LEADS
    df["Sellable Leads"] = (
        g("Fallback (Unsold)")
        + g("Fallback (Rejected)")
        + g("Leads Delivered (Provisional)")
    )

    # LEADS DELIVERED CORRECTED
    df["Leads Delivered (Corrected)"] = (
        g("Leads Delivered (Provisional)")
        - g("Leads Delivered (Refunded)")
    )

    # VLD CORRECTED
    df["VLD (Corrected)"] = (
        g("VLD (Provisional)") - g("VLD (Refunded)")
    )

    # TOTAL # OF IDENTITIES — cumulative
    df = df.sort_values("Date")
    if "New Identities To CRM" in df.columns:
        df["Total # of Identities"] = g("New Identities To CRM").cumsum()
    else:
        df["Total # of Identities"] = None

    # CHURN %
    finished = g("Finished Packages")
    resigns = g("Resigns")
    df["Churn %"] = None
    valid = finished > 0
    df.loc[valid, "Churn %"] = ((finished - resigns) / finished) * 100

    # TOTAL PROFIT
    df["Total Profit"] = (
        g("VLD (Corrected)") - g("Total Adspend")
    )

    # PROFIT MARGIN %
    df["Profit Margin %"] = None
    vld = g("VLD (Corrected)")
    profit = df["Total Profit"]
    mask = vld != 0
    df.loc[mask, "Profit Margin %"] = (profit[mask] / vld[mask]) * 100

    return df
# =========================================================
#                DATA LOAD / SAVE FUNCTIONS
# =========================================================

def ensure_daily_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Ensures all dates from min → today exist in the dataframe."""
    if "Date" not in df.columns:
        return df

    if df.empty:
        today = datetime.today().date()
        return pd.DataFrame({"Date": [pd.to_datetime(today)]})

    df = df.sort_values("Date")
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    today = datetime.today().date()
    end = max(max_date, today)

    full_range = pd.date_range(start=min_date, end=end, freq="D")
    base = pd.DataFrame({"Date": full_range})

    return base.merge(df, on="Date", how="left")


def load_data() -> pd.DataFrame:
    """Loads local CSV → ensures structure → applies formulas."""
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame({"Date": pd.to_datetime([], utc=False)})

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = ensure_daily_rows(df)

    # Ensure every master stat exists
    for col in MASTER_STATS:
        if col not in df.columns:
            df[col] = None

    # 🔥 APPLY FORMULAS
    df = apply_formulas(df)

    return df


def save_data(df: pd.DataFrame) -> None:
    """Save updated stats to CSV (dates properly formatted)."""
    out = df.copy()
    out["Date"] = out["Date"].dt.strftime("%Y-%m-%d")
    out.to_csv(DATA_FILE, index=False)


def load_colors(columns: List[str]) -> Dict[str, str]:
    """Loads chart color assignments."""
    if COLOR_FILE.exists():
        try:
            c = json.loads(COLOR_FILE.read_text())
        except Exception:
            c = {}
    else:
        c = {}

    idx = 0
    for col in columns:
        if col == "Date":
            continue
        if col not in c:
            c[col] = DEFAULT_PALETTE[idx % len(DEFAULT_PALETTE)]
            idx += 1
    return c


def save_colors(colors: Dict[str, str]) -> None:
    COLOR_FILE.write_text(json.dumps(colors, indent=2))


# =========================================================
#        DATE FILTERING / RESAMPLING / WEEK HELPERS
# =========================================================

def filter_by_date(df: pd.DataFrame, range_label: str, custom_range):
    """Filters by preset or custom date range."""
    if df.empty or "Date" not in df.columns:
        return df

    df = df.sort_values("Date")
    end = df["Date"].max()

    if range_label == "All time":
        return df

    if range_label == "Last 7 days":
        start = end - timedelta(days=7)
    elif range_label == "Last 30 days":
        start = end - timedelta(days=30)
    elif range_label == "Last 90 days":
        start = end - timedelta(days=90)
    elif range_label == "Custom" and custom_range:
        start, end = custom_range
        start = pd.to_datetime(start)
        end = pd.to_datetime(end)
    else:
        return df

    return df[(df["Date"] >= start) & (df["Date"] <= end)]


def resample_df(df: pd.DataFrame, granularity: str):
    """Resamples dataframe into daily or weekly data."""
    if granularity == "Daily":
        return df

    if granularity == "Weekly":
        df = df.set_index("Date")
        weekly = df.resample("W-THU").mean(numeric_only=True)
        weekly["Date"] = weekly.index
        return weekly.reset_index(drop=True)

    return df


def week_date_to_str(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def week_str_to_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def get_latest_completed_week_end() -> date:
    """Returns most recent Thursday (week end)."""
    today = datetime.today().date()
    weekday = today.weekday()
    days_back = (weekday - 3) % 7  # Thursday = 3
    return today - timedelta(days=days_back)


def save_saved_views():
    VIEWS_FILE.write_text(json.dumps(st.session_state.saved_views, indent=2))


def save_weekly_conditions():
    CONDITIONS_FILE.write_text(json.dumps(st.session_state.weekly_conditions, indent=2))


# =========================================================
#                      LOGIN SYSTEM
# =========================================================

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


RAW_PASSWORD = "ARCKRC88008"
PASSWORD_HASH = hash_password(RAW_PASSWORD)

ALLOWED_USERS = {
    "james@redpandaleads.com": PASSWORD_HASH,
    "nick@redpandaleads.com": PASSWORD_HASH,
    "alex@redpandaleads.com": PASSWORD_HASH,
    "shiloh@redpandaleads.com": PASSWORD_HASH,
    "jake@redpandaleads.com": PASSWORD_HASH,
}


# =========================================================
#          INITIALIZE SESSION STATE (ALL KEYS)
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "df" not in st.session_state:
    st.session_state.df = load_data()

if "colors" not in st.session_state:
    st.session_state.colors = load_colors(st.session_state.df.columns)

if "graphs" not in st.session_state:
    st.session_state.graphs = [{"id": 1, "metrics": [], "overrides": {}}]

if "saved_views" not in st.session_state:
    if VIEWS_FILE.exists():
        try:
            st.session_state.saved_views = json.loads(VIEWS_FILE.read_text())
        except Exception:
            st.session_state.saved_views = {}
    else:
        st.session_state.saved_views = {}

if "current_view" not in st.session_state:
    st.session_state.current_view = "None (custom)"

if "weekly_conditions" not in st.session_state:
    if CONDITIONS_FILE.exists():
        try:
            st.session_state.weekly_conditions = json.loads(CONDITIONS_FILE.read_text())
        except Exception:
            st.session_state.weekly_conditions = {}
    else:
        st.session_state.weekly_conditions = {}


# =========================================================
#                    LOGIN / LOGOUT UI
# =========================================================

def login_screen():
    st.markdown(
        """
        <style>
        .login-container {
            max-width: 360px;
            margin: 0 auto;
            padding-top: 14vh;
            padding-bottom: 5vh;
            text-align: center;
        }

        .login-title {
            font-size: 28px;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 25px;
        }

        .stTextInput>div>div>input {
            background-color: #181820 !important;
            border: 1px solid #333 !important;
            color: #fff !important;
        }

        .stButton>button {
            width: 100%;
            background-color: #D32F2F !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 0.55rem 0 !important;
            font-size: 0.95rem !important;
            border: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='login-container'>", unsafe_allow_html=True)

    if LOGO_B64:
        st.markdown(
            f"""
            <img src="data:image/png;base64,{LOGO_B64}" 
                 style="height:80px; margin-bottom:10px;"/>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div class='login-title'>RPL-Stats</div>", unsafe_allow_html=True)

    username = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in ALLOWED_USERS and ALLOWED_USERS[username] == hash_password(password):
            st.session_state.logged_in = True
            st.session_state.current_user = username
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
#                 FLOATING TOP-RIGHT LOGOUT
# =========================================================

def top_right_logout():
    st.markdown(
        """
        <style>
            .logout-floating {
                position: fixed;
                top: 12px;
                right: 95px;
                z-index: 9999;
            }
            .logout-floating button {
                background-color: #D32F2F !important;
                color: white !important;
                padding: 4px 14px !important;
                font-size: 14px !important;
                border-radius: 6px !important;
                border: none !important;
            }
        </style>
        <div class="logout-floating">
        """,
        unsafe_allow_html=True
    )

    if st.button("Logout", key="top_logout_btn"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
#                  LOGIN GATE (PROTECT APP)
# =========================================================

if not st.session_state.logged_in:
    login_screen()
    st.stop()

top_right_logout()


# =========================================================
#                      HEADER / TITLE
# =========================================================

def centered_logo_and_title():
    st.markdown(
        """
        <h1 style='text-align:center; margin-top:8px; margin-bottom:24px;'>
            Red Panda Leads – Stats Dashboard
        </h1>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
#                      DATA TABLE PAGE
# =========================================================

def page_data_table():
    centered_logo_and_title()

    st.markdown(
        """
        <div class="rpl-card">
            <h3 style="color:#ff4b4b; margin:0;">🔴 Live Leads (Supabase → CRM)</h3>
            <p style="color:#ccc;">Automatically updated from CRM → not editable.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    try:
        leads_df = get_leads_df()
    except Exception:
        leads_df = pd.DataFrame()

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    if not leads_df.empty:
        if "created" in leads_df.columns:
            leads_df["created"] = pd.to_datetime(
                leads_df["created"], errors="coerce"
            )
        st.dataframe(leads_df, use_container_width=True, height=260)
    else:
        st.info("No leads found yet.")

    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

    st.markdown(
        "<h2 style='margin:0 0 10px 0; font-size:22px;'>RPL Stats Table</h2>",
        unsafe_allow_html=True,
    )

    owner_view = st.selectbox(
        "Stats owner view",
        ["All stats"] + STAFF_MEMBERS,
        index=0,
        help="Filter visible columns by stat owner."
    )

    df = st.session_state.df.copy()

    if owner_view == "All stats":
        visible_cols = ["Date"] + MASTER_STATS
        visible_cols = [c for c in visible_cols if c in df.columns]
    else:
        owned = STATS_BY_OWNER.get(owner_view, [])
        visible_cols = ["Date"] + [c for c in owned if c in df.columns]

    table_df = df[visible_cols].copy()

    edited = st.data_editor(
        table_df,
        key="rpl_editor",
        num_rows="dynamic",
        use_container_width=True,
        height=650,
        column_config={
            "Date": st.column_config.DatetimeColumn(
                "Date", disabled=True, format="YYYY-MM-DD"
            )
        }
    )

    if "Date" in edited.columns:
        edited["Date"] = pd.to_datetime(edited["Date"], errors="coerce")

    if not edited.equals(table_df):
        updated_df = df.copy()
        for col in visible_cols:
            updated_df[col] = edited[col]

        # 🔥 Reapply formulas and save
        updated_df = apply_formulas(updated_df)

        st.session_state.df = updated_df
        st.session_state.colors = load_colors(updated_df.columns)
        save_data(updated_df)
        save_colors(st.session_state.colors)

        st.toast("Stats saved", icon="✅")
# =========================================================
#                        GRAPHS PAGE
# =========================================================

def add_graph():
    graphs = st.session_state.graphs
    new_id = max(g["id"] for g in graphs) + 1 if graphs else 1
    graphs.append({"id": new_id, "metrics": [], "overrides": {}})
    st.session_state.graphs = graphs


def page_graphs(granularity: str, date_range_label: str, custom_range):
    centered_logo_and_title()

    df = st.session_state.df.copy()

    # Owner filter
    owner = st.selectbox(
        "Stats owner view",
        ["All"] + STAFF_MEMBERS
    )

    if owner != "All":
        visible_cols = ["Date"] + [
            c for c in STATS_BY_OWNER.get(owner, []) if c in df.columns
        ]
        df = df[visible_cols]

    if df.empty or "Date" not in df.columns:
        st.warning("No data available.")
        return

    df = df.dropna(subset=["Date"])
    df = df.sort_values("Date")

    # Apply date filter & granularity
    df = filter_by_date(df, date_range_label, custom_range)
    df = resample_df(df, granularity)

    if df.empty:
        st.info("No data in this range.")
        return

    # 🔥 ALWAYS use every stat in df
    all_stat_cols = [c for c in df.columns if c != "Date"]

    if not all_stat_cols:
        st.info("No statistics to graph.")
        return

    # -----------------------------------------------------
    # Saved views
    # -----------------------------------------------------
    st.markdown("---")

    view_options = ["None (custom)"] + PRESET_NAMES

    current_view_choice = st.radio(
        "Saved views",
        view_options,
        index=view_options.index(
            st.session_state.current_view
            if st.session_state.current_view in view_options
            else 0
        ),
        horizontal=True,
    )

    if current_view_choice != st.session_state.current_view:
        st.session_state.current_view = current_view_choice

        if current_view_choice == "None (custom)":
            st.session_state.graphs = [{"id": 1, "metrics": [], "overrides": {}}]
        else:
            view_conf = st.session_state.saved_views.get(
                current_view_choice, {"graphs": []}
            )
            graphs_conf = view_conf.get("graphs", [])

            new_graphs = []
            for idx, g in enumerate(graphs_conf, start=1):
                metrics = [m for m in g.get("metrics", []) if m in all_stat_cols]
                new_graphs.append({"id": idx, "metrics": metrics, "overrides": {}})

            if not new_graphs:
                new_graphs = [{"id": 1, "metrics": [], "overrides": {}}]

            st.session_state.graphs = new_graphs

    col_sv1, col_sv2 = st.columns([1, 3])
    with col_sv1:
        if current_view_choice != "None (custom)":
            if st.button("Save current graphs to this view"):
                graphs = st.session_state.graphs
                st.session_state.saved_views[current_view_choice] = {
                    "graphs": [{"metrics": g["metrics"]} for g in graphs]
                }
                save_saved_views()
                st.success(f"Saved current graphs to '{current_view_choice}'.")

    graphs = st.session_state.graphs

    # -----------------------------------------------------
    # Render all graph blocks
    # -----------------------------------------------------
    for idx, graph in enumerate(graphs):
        if idx > 0:
            st.markdown("---")

        st.markdown(f"### Graph {idx + 1}")

        selected = st.multiselect(
            "Choose statistics",
            all_stat_cols,
            default=[m for m in graph["metrics"] if m in all_stat_cols],
            key=f"metrics_{graph['id']}",
        )

        graph["metrics"] = selected

        if selected:
            # Make sure every metric is numeric where possible
            for metric in selected:
                df[metric] = pd.to_numeric(df[metric], errors="coerce")

            fig = go.Figure()

            for metric in selected:
                fig.add_trace(
                    go.Scatter(
                        x=df["Date"],
                        y=df[metric],
                        mode="lines",
                        name=metric,
                        line=dict(color=st.session_state.colors.get(metric)),
                    )
                )

            fig.update_layout(
                height=600,
                margin=dict(l=40, r=40, t=10, b=40),
                dragmode="pan",
                xaxis=dict(type="date", rangeslider=dict(visible=True)),
                yaxis=dict(title="Value"),
                legend=dict(orientation="v", xanchor="right", x=1.02, y=0.95),
                modebar=dict(orientation="h"),
            )

            st.plotly_chart(fig, use_container_width=True)

    # Add graph button
    st.markdown('<div id="add-graph-container">', unsafe_allow_html=True)
    if st.button("+", key="add_graph"):
        add_graph()
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
#             CONDITIONS → TABLE PAGE
# =========================================================

def page_conditions_table():
    centered_logo_and_title()

    conditions = st.session_state.weekly_conditions
    if not conditions:
        st.info("No conditions or battle plans exist yet.")
        return

    weeks = []
    for metric_data in conditions.values():
        for wk in metric_data.keys():
            try:
                weeks.append(week_str_to_date(wk))
            except Exception:
                pass

    if not weeks:
        st.info("No weekly condition entries found.")
        return

    weeks = sorted(set(weeks))
    week_labels = [week_date_to_str(w) for w in weeks]

    selected_week_str = st.selectbox(
        "Week ending (Thursday)", week_labels, index=len(week_labels) - 1
    )

    rows = []
    for stat_name, metric_data in conditions.items():
        entry = metric_data.get(selected_week_str)
        if entry:
            rows.append({
                "Statistic": stat_name,
                "Condition": entry.get("condition", ""),
                "Assigned to": entry.get("assigned_to", ""),
                "Battle plan preview": "Click ▾ to view"
            })

    if not rows:
        st.info("No conditions recorded for this week.")
        return

    df_rows = pd.DataFrame(rows)
    st.dataframe(df_rows, use_container_width=True)

    st.markdown("---")
    st.markdown("### Battle plan details")

    metric_names = [r["Statistic"] for r in rows]
    selected_metric = st.selectbox("Select a statistic", metric_names)
    entry = conditions[selected_metric][selected_week_str]
    steps = entry.get("battle_plan", [])

    if not steps:
        st.info("No battle plan steps for this metric.")
        return

    st.markdown(f"#### Battle plan for {selected_metric}")
    for i, step in enumerate(steps, start=1):
        st.markdown(f"- **{i}.** {step}")


# =========================================================
#      CONDITIONS → BATTLE PLANS + PERFORMANCE PAGE
# =========================================================

def page_conditions_battle_plans():
    centered_logo_and_title()

    conditions = st.session_state.weekly_conditions
    if not conditions:
        st.info("No battle plans exist yet.")
        return

    weeks = []
    for metric_data in conditions.values():
        for wk in metric_data.keys():
            try:
                weeks.append(week_str_to_date(wk))
            except Exception:
                pass

    if not weeks:
        st.info("No battle plan data found.")
        return

    weeks = sorted(set(weeks))
    week_labels = [week_date_to_str(w) for w in weeks]

    selected_week_str = st.selectbox(
        "Week ending (Thursday)", week_labels, index=len(week_labels) - 1
    )

    per_person = {name: [] for name in STAFF_MEMBERS}

    for stat_name, metric_data in conditions.items():
        entry = metric_data.get(selected_week_str)
        if not entry:
            continue

        assigned = entry.get("assigned_to")
        steps = entry.get("battle_plan", [])
        checks = entry.get("checks", [])

        if len(checks) < len(steps):
            checks = checks + [False] * (len(steps) - len(checks))
            entry["checks"] = checks
            metric_data[selected_week_str] = entry

        for idx_step, step_text in enumerate(steps):
            per_person[assigned].append(
                (stat_name, idx_step, step_text, checks[idx_step])
            )

    st.markdown("## Battle Plans")

    if not any(len(v) > 0 for v in per_person.values()):
        st.info("No battle plans recorded this week.")
        return

    for person in STAFF_MEMBERS:
        tasks = per_person[person]
        if not tasks:
            continue

        st.markdown(f"### {person}")

        for stat_name, idx_step, step_text, checked in tasks:
            key = f"bp_{selected_week_str}_{person}_{stat_name}_{idx_step}"

            new_val = st.checkbox(
                f"{step_text} _(stat: {stat_name})_",
                value=checked,
                key=key
            )

            if new_val != checked:
                entry = conditions[stat_name][selected_week_str]
                entry["checks"][idx_step] = new_val
                conditions[stat_name][selected_week_str] = entry
                st.session_state.weekly_conditions = conditions
                save_weekly_conditions()

        st.markdown("---")

    # PERFORMANCE TABLE
    st.markdown("## Performance Summary")

    perf_rows = []
    for person in STAFF_MEMBERS:
        tasks = per_person[person]
        if not tasks:
            continue

        total = len(tasks)
        completed = sum(
            1
            for stat_name, i, _, _ in tasks
            if conditions[stat_name][selected_week_str]["checks"][i]
        )
        pct = round((completed / total) * 100, 1) if total > 0 else 0

        perf_rows.append({
            "Person": person,
            "Completed": completed,
            "Total": total,
            "Performance %": pct,
        })

    if perf_rows:
        st.dataframe(pd.DataFrame(perf_rows), use_container_width=True)
    else:
        st.info("No performance data for this week.")


# =========================================================
#                       SIDEBAR & NAVIGATION
# =========================================================

with st.sidebar:

    if LOGO_B64:
        st.markdown(
            f"""
            <div style="text-align:center; margin-top:-10px; margin-bottom:20px;">
                <img src="data:image/png;base64,{LOGO_B64}" style="height:60px;">
            </div>
            """,
            unsafe_allow_html=True
        )

    st.header("Navigation")
    page = st.radio("Page", ["Data table", "Graphs"], index=0)

    st.header("Filters")
    granularity = st.radio("Granularity", ["Daily", "Weekly"], index=0)

    date_range_label = st.selectbox(
        "Date range",
        ["All time", "Last 7 days", "Last 30 days", "Last 90 days", "Custom"],
    )

    df_dates = st.session_state.df
    if "Date" in df_dates.columns and not df_dates.empty:
        dmin = df_dates["Date"].min().date()
        dmax = df_dates["Date"].max().date()
    else:
        dmin = dmax = datetime.today().date()

    custom_range = None
    if date_range_label == "Custom":
        custom_range = st.date_input("Custom range", (dmin, dmax))

    st.header("Conditions")
    conditions_view = st.radio(
        "View", ["Off", "Table", "Battle Plans"],
        index=0,
        key="conditions_view_radio"
    )


# =========================================================
#                           ROUTER
# =========================================================

if conditions_view == "Table":
    page_conditions_table()
elif conditions_view == "Battle Plans":
    page_conditions_battle_plans()
else:
    if page == "Data table":
        page_data_table()
    else:
        page_graphs(granularity, date_range_label, custom_range)
