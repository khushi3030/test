import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import date, datetime
import io

 
# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Allura CRM – Donor Report",
    page_icon="📋",
    layout="wide",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .report-header {
        background-color: #1a3c5e;
        color: white;
        padding: 18px 32px;
        border-radius: 6px 6px 0 0;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .criteria-box {
        background: #f5f8fc;
        border: 1px solid #d0dce8;
        border-top: none;
        padding: 20px 32px;
        border-radius: 0 0 6px 6px;
        margin-bottom: 20px;
    }
    .criteria-title {
        font-weight: 700;
        font-size: 15px;
        color: #1a3c5e;
        margin-bottom: 6px;
    }
    .comment-box {
        background: #fff8e1;
        border-left: 4px solid #f0a500;
        padding: 10px 16px;
        border-radius: 4px;
        margin-top: 10px;
        font-size: 14px;
        color: #444;
    }
    .comment-box b { color: #b07800; }
    .outcome-title {
        font-size: 16px;
        font-weight: 700;
        color: #1a3c5e;
        margin: 18px 0 8px 0;
        border-bottom: 2px solid #1a3c5e;
        padding-bottom: 4px;
    }
    .metric-card {
        background: white;
        border: 1px solid #d0dce8;
        border-radius: 8px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .metric-value { font-size: 28px; font-weight: 700; color: #1a3c5e; }
    .metric-label { font-size: 12px; color: #888; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)


# ─── DB Connection ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="mydatabase",
        user="postgres",
        password="Khushi@30",
    )


# ─── Query – By Created Date Range ────────────────────────────────────────────
def fetch_donors(from_date: date, to_date: date) -> pd.DataFrame:
    sql = """
        SELECT
            ROW_NUMBER() OVER (ORDER BY donor_id ASC) AS "S.No",
            donor_id                                   AS "Donor ID",
            CONCAT(first_name, ' ', last_name)         AS "Full Name",
            created_date                               AS "Created Date",
            email                                      AS "Email",
            modified_date                              AS "Modified Date",
            created_by                                 AS "Created By",
            modified_by                                AS "Modified By"
        FROM donor_table
        WHERE created_date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY donor_id ASC;
    """
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, {"from_date": from_date, "to_date": to_date})
            rows = cur.fetchall()
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        return pd.DataFrame()


# ─── Query – All Donors ────────────────────────────────────────────────────────
def fetch_all_donors() -> pd.DataFrame:
    sql = """
        SELECT
            ROW_NUMBER() OVER (ORDER BY donor_id ASC) AS "S.No",
            donor_id                                   AS "Donor ID",
            CONCAT(first_name, ' ', last_name)         AS "Full Name",
            created_date                               AS "Created Date",
            email                                      AS "Email",
            modified_date                              AS "Modified Date",
            created_by                                 AS "Created By",
            modified_by                                AS "Modified By"
        FROM donor_table
        ORDER BY donor_id ASC;
    """
    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        return pd.DataFrame()


# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🗄️ Connected Database")
    st.success("PostgreSQL — localhost")
    st.code("""host   = localhost
port   = 5050
table  = donor_table
cols   = donor_id, first_name,
         last_name, email,
         birth_date, created_date,
         modified_date, created_by,
         modified_by""")
    st.markdown("---")
    filter_mode = st.radio(
        "Filter Mode",
        ["By Created Date Range", "Show All Donors"],
        index=0
    )


# ─── Report Header ─────────────────────────────────────────────────────────────
st.markdown('<div class="report-header">📋 Donor Report</div>', unsafe_allow_html=True)

# ─── Input Criteria ────────────────────────────────────────────────────────────
st.markdown('<div class="criteria-box">', unsafe_allow_html=True)
st.markdown('<div class="criteria-title">Input Criteria – Period</div>', unsafe_allow_html=True)

if filter_mode == "By Created Date Range":
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        from_date = st.date_input("From Date", value=date(2020, 1, 1))
    with col2:
        to_date = st.date_input("To Date", value=date.today())
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("🔍 Generate Report", use_container_width=True)
else:
    from_date, to_date = None, None
    st.button("🔍 Load All Donors", use_container_width=True)

st.markdown(
    '<div class="comment-box"><b>Comment:</b> '
    'How many donors exist in the system between these two dates if the record is not deleted already.</div>',
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# ─── Fetch Data ────────────────────────────────────────────────────────────────
if filter_mode == "By Created Date Range":
    if from_date > to_date:
        st.warning("⚠️ 'From Date' cannot be after 'To Date'.")
        st.stop()
    df = fetch_donors(from_date, to_date)
else:
    df = fetch_all_donors()

# ─── Metrics ───────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{len(df)}</div>
        <div class="metric-label">Total Donors Found</div>
    </div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{from_date.strftime('%d %b %Y') if from_date else '—'}</div>
        <div class="metric-label">From Date</div>
    </div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-value">{to_date.strftime('%d %b %Y') if to_date else '—'}</div>
        <div class="metric-label">To Date</div>
    </div>""", unsafe_allow_html=True)

# ─── Outcome Table ─────────────────────────────────────────────────────────────
st.markdown('<div class="outcome-title">Outcome</div>', unsafe_allow_html=True)

if df.empty:
    st.info("No donor records found for the selected criteria.")
else:
    # All 9 columns shown in the table
    visible_cols = [
        "S.No",
        "Donor ID",
        "Full Name",
        "Created Date",
        "Email",
        "Modified Date",
        "Created By",
        "Modified By",
    ]

    # Safety guard — only show cols that exist in df
    visible_cols = [c for c in visible_cols if c in df.columns]

    st.dataframe(df[visible_cols], use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ Export as CSV",
        data=csv_buffer.getvalue(),
        file_name=f"donor_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"Allura CRM Reporting  •  Generated on {datetime.now().strftime('%d %b %Y, %H:%M')}")

