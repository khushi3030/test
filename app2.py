import streamlit as st
import psycopg2
import pandas as pd
from datetime import date

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Donation Report", layout="wide")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Arial, sans-serif;
        background-color: #ffffff;
        color: #000000;
    }
    .report-title {
        text-align: center;
        font-size: 2.6rem;
        font-weight: 700;
        margin-bottom: 1.8rem;
        color: #000000;
    }
    .criteria-bar {
        font-size: 1rem;
        margin-bottom: 1rem;
        padding: 4px 0;
    }
    .comment-block {
        font-size: 0.97rem;
        margin-bottom: 1.2rem;
        line-height: 1.5;
    }
    .outcome-heading {
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
        margin-bottom: 1rem;
    }
    .styled-table thead tr {
        background-color: #4472C4; /* deep blue header */
        color: #ffffff;
        font-weight: 700;
    }
    .styled-table thead th {
        padding: 10px 14px;
        text-align: left;
        border: 1px solid #3a5fa0;
    }
    .styled-table tbody tr:nth-child(even) { background-color: #dce6f1; } /* light blue */
    .styled-table tbody tr:nth-child(odd)  { background-color: #eaf0f9; } /* lighter blue */
    .styled-table tbody td {
        padding: 9px 14px;
        border: 1px solid #b8cce4;
        color: #000000;
    }
    .bottom-bar {
        height: 6px;
        background-color: #4472C4; /* same blue accent */
        margin-top: 2.5rem;
        border-radius: 2px;
    }
    #MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)



# ── DB connection ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="mydatabase",
        user="postgres",
        password="Khushi@30"   # <-- change this
    )


def run_query(from_date: date, to_date: date) -> pd.DataFrame:
    
    query = """
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY d.created_date, dn."donorid"
            )                                       AS s_no,
            d.created_date                          AS date,
            dn."donationid"                         AS donation_id,
            d.first_name || ' ' || d.last_name      AS donor_full_name,
            dn."donationamount"                   AS donation_amount
        FROM donation dn
        JOIN donor_table d
          ON d.donor_id = dn."donorid"
        WHERE
            d.created_date
                BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY d.created_date, dn."donationid";
    """
    conn = get_connection()
    df = pd.read_sql_query(
        query, conn,
        params={"from_date": from_date, "to_date": to_date}
    )
    return df


def build_table_html(df: pd.DataFrame) -> str:
    """Renders the outcome table as styled HTML."""
    if df.empty:
        body = (
            "<tr><td colspan='5' style='text-align:center;color:red;'>""No donations exist for the selected period""</td></tr>"
        )   
    else:
        rows = ""
        for _, row in df.iterrows():
            rows += (
                f"<tr>"
                f"<td>{int(row['s_no'])}</td>"
                f"<td>{pd.to_datetime(row['date']).strftime('%d-%b-%Y')}</td>"
                f"<td>{row['donation_id']}</td>"
                f"<td>{row['donor_full_name']}</td>"
                f"<td>{float(row['donation_amount']):,.2f}</td>"
                f"</tr>"
            )
        body = rows

    return (
        '<table class="styled-table">'
        "<thead><tr>"
        "<th>S.No</th><th>Date</th><th>Donation ID</th>"
        "<th>Donor Full Name</th><th>Donation Amount</th>"
        "</tr></thead>"
        f"<tbody>{body}</tbody>"
        "</table>"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  REPORT LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="report-title">Donation Report</div>', unsafe_allow_html=True)

col_label, col_from, col_to, col_btn = st.columns([2, 1.5, 1.5, 1])
with col_label:
    st.markdown(
        "<div style='padding-top:8px'><b>Input Criteria –&nbsp;&nbsp;Period</b></div>",
        unsafe_allow_html=True,
    )
with col_from:
    from_date = st.date_input("From Date", value=date(2026, 4, 1))
with col_to:
    to_date = st.date_input("To Date", value=date.today())
with col_btn:
    st.markdown("<div style='padding-top:4px'></div>", unsafe_allow_html=True)
    generate = st.button("Generate Report", type="primary", use_container_width=True)

st.markdown(
    f'<div class="criteria-bar">'
    f"<b>Input Criteria –</b>&nbsp;&nbsp;<b>Period</b>"
    f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    f"{from_date.strftime('%d-%b-%Y')}"
    f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    f"{to_date.strftime('%d-%b-%Y')}"
    f"</div>",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="comment-block">'
    "<b>Comment:</b> How many distinct donation exist in the system between these "
    "two dates if the record is not deleted already"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown('<div class="outcome-heading">Outcome:</div>', unsafe_allow_html=True)

if generate:
    if from_date > to_date:
        st.error("'From Date' must be on or before 'To Date'.")
        st.markdown(build_table_html(pd.DataFrame()), unsafe_allow_html=True)
    else:
        try:
            with st.spinner("Fetching donations…"):
                df = run_query(from_date, to_date)
            st.markdown(build_table_html(df), unsafe_allow_html=True)
            if not df.empty:
                st.caption(
                    f"Total distinct donations found: **{len(df)}**  |  "
                    f"Period: {from_date.strftime('%d-%b-%Y')} → {to_date.strftime('%d-%b-%Y')}"
                )
            else:
                st.info("No donation records found for the selected period.")
        except Exception as e:
            st.error(f"Database error: {e}")
            st.markdown(build_table_html(pd.DataFrame()), unsafe_allow_html=True)
else:
    st.markdown(build_table_html(pd.DataFrame()), unsafe_allow_html=True)

st.markdown('<div class="bottom-bar"></div>', unsafe_allow_html=True)