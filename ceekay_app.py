import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date
import io
import matplotlib.pyplot as plt
import base64
from pathlib import Path

APP_TITLE = "CEEKAY Tours Manager"
WORKBOOK_NAME = "CEEKAY_Driver_Reports"

st.set_page_config(page_title=APP_TITLE, page_icon="🚗", layout="wide")

st.markdown(
    """
    <style>
    :root { --navy:#0f172a; --blue:#2563eb; --teal:#0f766e; --ink:#111827; }
    .stApp {background:linear-gradient(135deg,#f7f9fc 0%,#edf3f9 100%);color:var(--ink);}
    header[data-testid="stHeader"] {height:3.5rem;background:rgba(255,255,255,.94);}
    .block-container {padding-top:5.4rem !important;padding-bottom:3rem;max-width:1500px;}
    [data-testid="stSidebar"] {background:linear-gradient(180deg,#111827 0%,#0b1220 100%);}
    [data-testid="stSidebar"] * {color:#f8fafc !important;}
    h1,h2,h3,h4,h5,h6,.finance-title {line-height:1.25 !important;overflow:visible !important;padding-top:.12em !important;}
    .finance-title {font-size:2.1rem;font-weight:760;color:#0f172a;margin:0 0 .2rem;}
    .finance-subtitle {color:#64748b;margin:0 0 1.35rem;font-size:1.02rem;}
    [data-testid="stMetric"] {background:#fff;padding:20px 18px;min-height:142px;border-radius:20px;border:1px solid #e2e8f0;box-shadow:0 10px 28px rgba(15,23,42,.06);overflow:visible !important;min-width:0;}
    [data-testid="stMetricLabel"] {font-size:.95rem;}
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] > div {font-size:clamp(1.05rem,1.55vw,1.65rem) !important;line-height:1.28 !important;white-space:nowrap !important;overflow:visible !important;text-overflow:clip !important;word-break:normal !important;max-width:none !important;width:auto !important;}
    div[data-testid="stForm"] {background:rgba(255,255,255,.98);padding:24px;border-radius:20px;border:1px solid #e2e8f0;box-shadow:0 10px 30px rgba(15,23,42,.05);}
    .section-card {background:#fff;border:1px solid #e2e8f0;border-radius:20px;padding:20px;margin-bottom:16px;box-shadow:0 8px 24px rgba(15,23,42,.05)}
    .small-note {font-size:.85rem;color:#64748b;}
    div.stButton > button, div[data-testid="stFormSubmitButton"] button {border-radius:12px;min-height:44px;font-weight:650;}
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, textarea {border-radius:12px !important;}
    .login-logo {width:86px;height:86px;border-radius:24px;margin:0 auto 18px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:2.25rem;background:linear-gradient(135deg,#2563eb,#0f766e);}
    .ck-logo-center [data-testid="stImage"] {display:flex !important;justify-content:center !important;align-items:center !important;width:100% !important;}
    .ck-logo-center [data-testid="stImage"] img {display:block !important;margin:0 auto !important;object-fit:contain !important;}
    [data-testid="stSidebar"] .ck-logo-center + div {text-align:center;}
    .login-name {font-size:2rem;font-weight:780;line-height:1.25;color:#0f172a;}
    .login-sub {color:#64748b;margin:.35rem 0 1.1rem;}
    .login-note {background:#f1f5f9;border-radius:13px;padding:12px;color:#475569;font-size:.88rem;}
    @media(max-width:900px){.block-container{padding-top:4.8rem !important;}[data-testid="stMetric"]{min-height:120px;padding:16px;}[data-testid="stMetricValue"]{font-size:1.35rem !important;}}
    </style>
    """,
    unsafe_allow_html=True,
)

# Tours-specific UI extensions
st.markdown("""<style>
.ck-page-kicker{display:inline-block;background:#ecfdf5;color:#0f766e!important;border:1px solid #ccfbf1;border-radius:999px;padding:.34rem .68rem;font-size:.76rem;font-weight:700;margin-bottom:.7rem;}
.ck-side-brand{text-align:center;margin:.2rem 0 .9rem}.ck-side-brand b{color:#fff!important}.ck-side-brand span{display:block;color:#94a3b8!important;font-size:.75rem;margin-top:.15rem}
[data-testid="stSidebar"] [role="radio"]{display:none;}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:.62rem .7rem;border-radius:11px;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:rgba(15,118,110,.35);}
.ck-login-note{background:#f1f5f9;border-radius:13px;padding:12px;color:#475569!important;font-size:.88rem;margin-top:.7rem;}
</style>""",unsafe_allow_html=True)


# Executive dashboard styling
st.markdown("""<style>
.ck-dashboard-gap{height:.45rem}
.ck-kpi-card{background:#fff;border:1px solid #e5eaf1;border-radius:16px;padding:18px 16px;min-height:138px;box-shadow:0 5px 16px rgba(15,23,42,.04);margin-bottom:8px}
.ck-kpi-top{display:flex;align-items:flex-start;gap:12px}.ck-kpi-icon{width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.25rem;font-weight:800;flex:0 0 48px}
.ck-kpi-copy{min-width:0}.ck-kpi-label{font-size:.68rem;font-weight:800;color:#334155;letter-spacing:.02em;margin:1px 0 7px}.ck-kpi-value{font-size:1.22rem;font-weight:800;line-height:1.22;white-space:nowrap}.ck-kpi-note{font-size:.72rem;color:#64748b;margin-top:8px}
.ck-panel-title{font-size:.92rem;font-weight:800;color:#0f172a;margin:0 0 .35rem;padding:.1rem .1rem .2rem}
[data-testid="stPlotlyChart"]{background:#fff;border:1px solid #e5eaf1;border-radius:16px;padding:6px 8px;box-shadow:0 5px 16px rgba(15,23,42,.04)}
.ck-rank-row{background:#fff;border-bottom:1px solid #edf1f5;padding:13px 7px;display:flex;align-items:center;gap:10px}.ck-rank-row:last-child{border-bottom:0}.ck-rank-no{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#f1f5f9;color:#334155;font-weight:800;font-size:.78rem}.ck-rank-main{display:flex;flex-direction:column;flex:1}.ck-rank-main b{font-size:.82rem;color:#0f172a}.ck-rank-main span{font-size:.68rem;color:#94a3b8;margin-top:2px}.ck-rank-value{font-size:.77rem;color:#079455;font-weight:800;text-align:right}
.ck-recent-row{background:#fff;border-bottom:1px solid #edf1f5;padding:12px 6px;display:flex;justify-content:space-between;align-items:center}.ck-recent-row div{display:flex;gap:15px;align-items:center}.ck-recent-row b{font-size:.76rem;color:#334155}.ck-recent-row span{font-size:.74rem;color:#64748b}.ck-recent-row strong{font-size:.77rem;color:#079455}
.ck-alert{border-radius:12px;padding:11px 12px;margin-bottom:8px;display:flex;gap:10px;align-items:flex-start;border:1px solid transparent}.ck-alert-danger{background:#fff1f1;border-color:#ffd6d6}.ck-alert-warning{background:#fff8e8;border-color:#ffe8b1}.ck-alert-success{background:#effaf2;border-color:#d3f0db}.ck-alert-symbol{width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.85);font-weight:900;font-size:.75rem}.ck-alert b{font-size:.73rem;color:#334155;display:block;line-height:1.25}.ck-alert small{display:block;color:#64748b;font-size:.66rem;margin-top:3px;line-height:1.25}
.ck-dashboard-footer{text-align:center;color:#94a3b8;font-size:.75rem;padding:26px 0 4px}
@media(max-width:1200px){.ck-kpi-value{font-size:1.02rem}.ck-kpi-icon{width:40px;height:40px;flex-basis:40px}}
</style>""", unsafe_allow_html=True)



def render_centered_logo(width=130):
    """Render logo with true HTML centering (works in login and sidebar)."""
    logo_path = Path("logo.png")
    if logo_path.exists():
        encoded = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
        st.markdown(
            f"""
            <div style="width:100%;display:flex;justify-content:center;align-items:center;text-align:center;margin:0 auto 18px auto;">
                <img src="data:image/png;base64,{encoded}" style="display:block;width:{width}px;max-width:100%;height:auto;margin:0 auto;object-fit:contain;">
            </div>
            """,
            unsafe_allow_html=True,
        )
        return True
    return False

# -------------------------------------------------------------------
# GOOGLE SHEET CONNECTION (SAFE VERSION)
# -------------------------------------------------------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# 🔒 Load credentials from Streamlit Secrets (not from file)
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"],
    scope
)

client = gspread.authorize(creds)




file = client.open("CEEKAY_Driver_Reports")
drivers_sheet = file.worksheet("drivers")
daily_sheet = file.worksheet("daily_reports")
vehicle_master_sheet = file.worksheet("vehicle_master")
vehicle_variable_sheet = file.worksheet("vehicle_variable_costs")
try:
    monthly_cash_flow_sheet = file.worksheet("monthly_cash_flow")
except gspread.WorksheetNotFound:
    monthly_cash_flow_sheet = file.add_worksheet(title="monthly_cash_flow", rows=200, cols=4)
    monthly_cash_flow_sheet.append_row(["month", "electricity_bill", "updated_at", "note"])

drivers_df = pd.DataFrame(drivers_sheet.get_all_records())

# -------------------------------------------------------------------
# CHECK DRIVER LAST STATUS
# -------------------------------------------------------------------
def check_driver_status(driver_name):
    df = pd.DataFrame(daily_sheet.get_all_records())
    df = df[df["driver_name"] == driver_name]
    if df.empty:
        return "No Reports"
    last = df.iloc[-1]["status"]
    return last



# -------------------------------------------------------------------
# LOGIN SYSTEM
# -------------------------------------------------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Mypa$$CEEKAY"

def driver_auth(username, password):
    row = drivers_df[
        (drivers_df["username"] == username) &
        (drivers_df["password"] == password)
    ]
    if not row.empty:
        return row.iloc[0].to_dict()
    return None

# -------------------------------------------------------------------
# SIDEBAR MENU
# -------------------------------------------------------------------
def sidebar_menu(user_type=None):
    with st.sidebar:
        render_centered_logo(145)
        st.markdown('<div class="ck-side-brand"><b>CEEKAY TOURS</b><span>Management Console</span></div>', unsafe_allow_html=True)
        st.divider()
        icons={"Dashboard":"▦","Daily Entry":"＋","Profit Reports":"↗","Monthly Cash Flow":"↕","Vehicle Entry":"⚙","Vehicle Report":"◉","Settings":"☷","Logout":"↪"}
        page=st.radio("Navigation",["Dashboard","Daily Entry","Profit Reports","Monthly Cash Flow","Vehicle Entry","Vehicle Report","Settings","Logout"],format_func=lambda x:f"{icons[x]}   {x}",label_visibility="collapsed")
        st.divider()
        st.caption("CEEKAY Tours • Admin Workspace")
        return page

def get_last_end_mileage(driver_name):
    df = pd.DataFrame(daily_sheet.get_all_records())

    if df.empty:
        return 0

    df = df[df["driver_name"] == driver_name]

    if df.empty:
        return 0

    df = df.sort_values("date", ascending=False)
    return int(df.iloc[0]["end_mileage"])

# -------------------------------------------------------------------
# DRIVER DAILY REPORT FORM
# -------------------------------------------------------------------
def page_driver_form(driver):

    # Get last end mileage automatically
    last_end_mileage = get_last_end_mileage(driver["driver_name"])

    # Default field values (EMPTY where needed)
    fields = {
        "report_date": date.today(),
        "start": last_end_mileage,
        "end": None,
        "uber": None,
        "fare": None,
        "tip": None,
        "toll": None,
        "other": None,
        "cash": None,
        "calc_done": False,
    }

    # Initialize session state safely
    for k, v in fields.items():
        if k not in st.session_state:
            st.session_state[k] = v

    with st.form("driver_daily_form", clear_on_submit=False):

        st.session_state.report_date = st.date_input(
            "Select Date",
            value=st.session_state.report_date
        )

        # Start & End mileage
        col1, col2 = st.columns(2)

        st.session_state.start = col1.number_input(
            "Start Mileage *",
            min_value=0,
            value=st.session_state.start
        )

        end_input = col2.text_input(
            "End Mileage *",
            value="" if st.session_state.end is None else str(st.session_state.end)
        )
        if end_input.strip() != "":
            try:
                st.session_state.end = float(end_input)
            except ValueError:
                st.error("Please enter a valid end mileage")

        # Uber mileage (decimal allowed)
        uber_input = st.text_input(
            "Uber Hire Mileage * (example: 100.52)",
            value="" if st.session_state.uber is None else str(st.session_state.uber)
        )
        if uber_input.strip() != "":
            try:
                st.session_state.uber = float(uber_input)
            except ValueError:
                st.error("Please enter a valid number like 100.52")

        # Fare
        fare_input = st.text_input(
            "Fare (Rs.) *",
            value="" if st.session_state.fare is None else str(st.session_state.fare)
        )
        if fare_input.strip() != "":
            try:
                st.session_state.fare = float(fare_input)
            except ValueError:
                st.error("Please enter a valid fare")

        # Tip
        tip_input = st.text_input(
            "Tip (Rs.)",
            value="" if st.session_state.tip is None else str(st.session_state.tip)
        )
        if tip_input.strip() != "":
            try:
                st.session_state.tip = float(tip_input)
            except ValueError:
                st.error("Please enter a valid tip")

        # Toll
        toll_input = st.text_input(
            "Toll Fee (Rs.)",
            value="" if st.session_state.toll is None else str(st.session_state.toll)
        )
        if toll_input.strip() != "":
            try:
                st.session_state.toll = float(toll_input)
            except ValueError:
                st.error("Please enter a valid toll amount")

        # Other expenses
        other_input = st.text_input(
            "Other Expenses (Rs.)",
            value="" if st.session_state.other is None else str(st.session_state.other)
        )
        if other_input.strip() != "":
            try:
                st.session_state.other = float(other_input)
            except ValueError:
                st.error("Please enter a valid amount")

        # Cash collected
        cash_input = st.text_input(
            "Cash Collected (Rs.) *",
            value="" if st.session_state.cash is None else str(st.session_state.cash)
        )
        if cash_input.strip() != "":
            try:
                st.session_state.cash = float(cash_input)
            except ValueError:
                st.error("Please enter a valid cash amount")


        calc_btn = st.form_submit_button("Refresh Calculations")
        submit_btn = st.form_submit_button("Submit Report")

    # ---------------- Calculations ----------------
    if calc_btn:
        st.session_state.calc_done = True

    if st.session_state.calc_done:

        if (
            st.session_state.end is None
            or st.session_state.uber is None
            or st.session_state.fare is None
            or st.session_state.cash is None
        ):
            st.warning("Please fill all required fields to calculate.")
        else:
            start = st.session_state.start
            end = st.session_state.end
            fare = st.session_state.fare
            tip = st.session_state.tip or 0
            toll = st.session_state.toll or 0
            uber = st.session_state.uber
            cash = st.session_state.cash

            daily = max(0, end - start)
            loss = daily - uber
            net_fare = max(0, fare - toll)
            salary = net_fare * 0.30
            total_salary = salary + toll + tip
            to_ceekay = cash - total_salary

            st.info(f"**Daily Mileage:** {daily} km")
            st.warning(f"**Loss Mileage:** {loss} km")
            st.success(f"**Driver Salary (30%): Rs. {salary:,.2f}**")
            st.success(f"**Total Driver Salary: Rs. {total_salary:,.2f}**")
            st.info(f"**Amount to Hand Over: Rs. {to_ceekay:,.2f}**")



    # ---------------- Submit ----------------
    if submit_btn:

        if st.session_state.end is None:
            st.error("End mileage is required.")
            return
        if st.session_state.uber is None:
            st.error("Uber mileage is required.")
            return
        if st.session_state.fare is None:
            st.error("Fare is required.")
            return
        if st.session_state.cash is None:
            st.error("Cash collected is required.")
            return


        daily = st.session_state.end - st.session_state.start
        loss = daily - st.session_state.uber
        fare = st.session_state.fare
        toll = st.session_state.toll or 0
        net_fare = max(0, fare - toll)
        salary = net_fare * 0.30
        total_salary = salary + toll + (st.session_state.tip or 0)
        to_ceekay = st.session_state.cash - total_salary

        # 🔹 Load vehicle cost per km
        master_df = pd.DataFrame(vehicle_master_sheet.get_all_records())

        master_df["vehicle_no"] = (
            master_df["vehicle_no"]
            .astype(str)
            .str.replace("-", "", regex=False)
            .str.strip()
        )

        vehicle_no_clean = (
            driver["vehicle_no"]
            .replace("-", "")
            .strip()
        )

        vehicle_row = master_df[
           master_df["vehicle_no"] == vehicle_no_clean
        ]

        if not vehicle_row.empty:
            cost_per_km = float(vehicle_row.iloc[0].get("cost_per_km", 0))
        else:
            cost_per_km = 0

        vehicle_running_cost = daily * cost_per_km

        new_row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            st.session_state.report_date.strftime("%Y-%m-%d"),
            driver["driver_name"],
            driver["vehicle_no"],
            st.session_state.start,
            st.session_state.end,
            daily,
            st.session_state.uber,
            loss,
            st.session_state.fare,
            st.session_state.tip or 0,
            st.session_state.toll or 0,
            st.session_state.other or 0,
            st.session_state.cash,
            0,
            salary,
            total_salary,
            to_ceekay,
            "Pending",
            "",
            "",
            0,
            0,
            cost_per_km,
            vehicle_running_cost
        ]

        daily_sheet.append_row(new_row)

        st.success("Submitted successfully! Please wait for management approval.")
        st.session_state.clear()
        st.rerun()

# -------------------------------------------------------------------
# DRIVER SUMMARY
# -------------------------------------------------------------------
def page_driver_summary(driver):
    st.markdown("<div class='title-text'>📄 My Summary</div>", unsafe_allow_html=True)

    df = pd.DataFrame(daily_sheet.get_all_records())
    df = df[df["driver_name"] == driver["driver_name"]]

    if df.empty:
        st.info("No reports submitted yet.")
        return

    df = df.sort_values("date", ascending=False)
    st.dataframe(df)

# -------------------------------------------------------------------
# DRIVER DASHBOARD
# -------------------------------------------------------------------
def page_driver_dashboard(driver):

    st.markdown("<div class='title-text'>📊 Driver Dashboard</div>", unsafe_allow_html=True)

    df = pd.DataFrame(daily_sheet.get_all_records())

    if df.empty:
        st.info("No data available")
        return

    df["date"] = pd.to_datetime(df["date"])

    # Driver filter
    df = df[
        (df["driver_name"] == driver["driver_name"]) &
        (df["status"] == "Correct")
    ]

    if df.empty:
        st.warning("No approved reports yet.")
        return

    # Convert numeric
    cols = [
        "daily_mileage",
        "uber_hire_mileage",
        "loss_mileage",
        "driver_salary",
        "tip"
    ]

    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # Date filter
    col1, col2 = st.columns(2)

    start_date = col1.date_input("From Date", df["date"].min())
    end_date = col2.date_input("To Date", df["date"].max())

    df = df[
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date))
    ]

    if df.empty:
        st.info("No records for selected dates")
        return

    # Earnings column
    df["earnings"] = df["driver_salary"] + df["tip"]

    # Attendance
    days_worked = df["date"].nunique()
    total_days = (end_date - start_date).days + 1
    days_absent = total_days - days_worked

    # Mileage
    total_mileage = df["daily_mileage"].sum()
    uber_mileage = df["uber_hire_mileage"].sum()
    loss_mileage = df["loss_mileage"].sum()

    # Convert numbers safely
    df["driver_salary"] = pd.to_numeric(df["driver_salary"], errors="coerce").fillna(0)
    df["tip"] = pd.to_numeric(df["tip"], errors="coerce").fillna(0)

    # Earnings totals
    total_salary = df["driver_salary"].sum()
    total_tips = df["tip"].sum()
    total_earnings = df["earnings"].sum()

    # Average per day
    avg_per_day = total_earnings / days_worked if days_worked > 0 else 0

    # Highest & lowest day
    highest = df.loc[df["earnings"].idxmax()]
    lowest = df.loc[df["earnings"].idxmin()]

    # Best week
    df["week"] = df["date"].dt.isocalendar().week
    weekly = df.groupby("week")["earnings"].sum().reset_index()
    best_week = weekly.loc[weekly["earnings"].idxmax()]

    # =====================================================
    # DRIVER DASHBOARD UI v2
    # =====================================================

    st.markdown("## Performance Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🟢 Days Worked", days_worked)
    col2.metric("🔴 Days Absent", days_absent)
    col3.metric("⭐ Avg Per Day", f"Rs {avg_per_day:,.0f}")
    col4.metric("🏆 Best Week", f"Week {int(best_week['week'])}")

    st.markdown("---")

    # =====================================================
    # MILEAGE SECTION
    # =====================================================

    st.markdown("## Mileage Summary")

    m1, m2, m3 = st.columns(3)

    m1.metric("Total Mileage", f"{total_mileage:,.0f} km")
    m2.metric("Uber Mileage", f"{uber_mileage:,.0f} km")
    m3.metric("Loss Mileage", f"{loss_mileage:,.0f} km")

    st.markdown("---")

    # =====================================================
    # EARNINGS SECTION
    # =====================================================

    st.markdown("## Earnings Summary")

    e1, e2, e3 = st.columns(3)

    e1.metric("Driver Salary", f"Rs {total_salary:,.0f}")
    e2.metric("Tips", f"Rs {total_tips:,.0f}")
    e3.metric("Total Earnings", f"Rs {total_earnings:,.0f}")

    st.markdown("---")

    # =====================================================
    # RECORDS
    # =====================================================

    st.markdown("## Personal Records")

    r1, r2 = st.columns(2)

    r1.metric(
        "🏆 Highest Earning Day",
        f"Rs {highest['earnings']:,.0f}",
        highest["date"].strftime("%Y-%m-%d")
    )

    r2.metric(
        "📉 Lowest Earning Day",
        f"Rs {lowest['earnings']:,.0f}",
        lowest["date"].strftime("%Y-%m-%d")
    )
    st.subheader("Earnings Trend")

    fig = px.line(
        df,
        x="date",
        y="earnings",
        markers=True,
        title="Daily Earnings"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Top Driver of the Month")

    df_all = pd.DataFrame(daily_sheet.get_all_records())

    if not df_all.empty:

        df_all["date"] = pd.to_datetime(df_all["date"], errors="coerce")

        df_all = df_all[df_all["status"] == "Correct"]

        df_all["driver_salary"] = pd.to_numeric(df_all["driver_salary"], errors="coerce").fillna(0)
        df_all["tip"] = pd.to_numeric(df_all["tip"], errors="coerce").fillna(0)

        df_all["earnings"] = df_all["driver_salary"] + df_all["tip"]

        current_month = datetime.today().strftime("%Y-%m")
        df_all["month"] = df_all["date"].dt.strftime("%Y-%m")

        df_month = df_all[df_all["month"] == current_month]

        if not df_month.empty:

            leaderboard = (
                df_month.groupby("driver_name")["earnings"]
                .sum()
                .reset_index()
                .sort_values("earnings", ascending=False)
            )

            leaderboard["rank"] = leaderboard["earnings"].rank(method="min", ascending=False)
            leaderboard = leaderboard.sort_values("rank")

            # Top Driver
            top_driver = leaderboard.iloc[0]

            st.success(f"🏆 Top Driver This Month: {top_driver['driver_name']}")

            # Current driver's rank
            my_row = leaderboard[leaderboard["driver_name"] == driver["driver_name"]]

            if not my_row.empty:
                my_rank = int(my_row.iloc[0]["rank"])
                st.info(f"⭐ Your Rank This Month: #{my_rank}")

            st.markdown("### Monthly Leaderboard")

            display_board = leaderboard[["rank", "driver_name"]].rename(
                columns={
                    "rank": "Rank",
                    "driver_name": "Driver"
                }
            )

            st.dataframe(display_board)

        else:
            st.info("No earnings recorded this month yet.")

# -------------------------------------------------------------------
# EARNINGS REPORT (Daily + Date Range)
# -------------------------------------------------------------------
def page_earnings_report(user_type, driver=None):

    st.markdown("<div class='title-text'>📅 Earnings Report</div>", unsafe_allow_html=True)

    df = pd.DataFrame(daily_sheet.get_all_records())
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["status"] == "Correct"]


    # Filter for driver only
    if user_type == "driver":
        df = df[df["driver_name"] == driver["driver_name"]]

    mode = st.radio("Select Report Type", ["Single Day", "Date Range"])

    # -------------------------------------------------------------
    # SINGLE DAY REPORT
    # -------------------------------------------------------------
    if mode == "Single Day":

        selected_date = st.date_input("Select Date")
        f = df[df["date"] == pd.to_datetime(selected_date)]

        if f.empty:
            st.info("No records for this date.")
            return

        st.subheader("Daily Summary")

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Mileage", f"{f['daily_mileage'].sum()} km")
        c2.metric("Uber Mileage", f"{f['uber_hire_mileage'].sum()} km")
        c3.metric("Loss Mileage", f"{f['loss_mileage'].sum()} km")

        c4, c5, c6 = st.columns(3)
        c4.metric("Fare", f"Rs {f['fare'].sum():,.2f}")
        c5.metric("Tip", f"Rs {f['tip'].sum():,.2f}")
        c6.metric("Toll Fee", f"Rs {f['toll_fee'].sum():,.2f}")

        c7, c8 = st.columns(2)
        c7.metric("Driver Salary (30%)", f"Rs {f['driver_salary'].sum():,.2f}")
        c8.metric("Total Driver Salary", f"Rs {f['total_driver_salary'].sum():,.2f}")

# REMOVE detailed table block
# st.subheader("Detailed Table")
# st.dataframe(f)


    # -------------------------------------------------------------
    # DATE RANGE REPORT
    # -------------------------------------------------------------
    else:

        col1, col2 = st.columns(2)
        start_date = col1.date_input("Start Date")
        end_date = col2.date_input("End Date")

        mask = (df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))
        f = df[mask]

        if f.empty:
            st.info("No records found for this date range.")
            return

        st.subheader("Date Range Summary")

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Mileage", f"{f['daily_mileage'].sum()} km")
        c2.metric("Uber Mileage", f"{f['uber_hire_mileage'].sum()} km")
        c3.metric("Loss Mileage", f"{f['loss_mileage'].sum()} km")

        c4, c5, c6 = st.columns(3)
        c4.metric("Fare", f"Rs {f['fare'].sum():,.2f}")
        c5.metric("Tip", f"Rs {f['tip'].sum():,.2f}")
        c6.metric("Toll Fee", f"Rs {f['toll_fee'].sum():,.2f}")

        c7, c8 = st.columns(2)
        c7.metric("Driver Salary (30%)", f"Rs {f['driver_salary'].sum():,.2f}")
        c8.metric("Total Driver Salary", f"Rs {f['total_driver_salary'].sum():,.2f}")

        st.subheader("Chart View")
        fig = px.line(f, x="date", y="fare", title="Fare Over Time")
        st.plotly_chart(fig, use_container_width=True)

# REMOVE detailed table block
# st.subheader("Detailed Table")
# st.dataframe(f)
# st.download_button("Download as CSV", f.to_csv(index=False), "earnings_report.csv")

# =====================================================
# CENTRAL VEHICLE SERVICE DATA FUNCTION
# =====================================================

def get_vehicle_service_data():

    df_reports = pd.DataFrame(daily_sheet.get_all_records())
    master_df = pd.DataFrame(vehicle_master_sheet.get_all_records())
    expense_df = pd.DataFrame(vehicle_variable_sheet.get_all_records())

    if df_reports.empty or master_df.empty:
        return pd.DataFrame()

    # -----------------------
    # Current Mileage
    # -----------------------
    df_reports["date"] = pd.to_datetime(df_reports["date"], errors="coerce")
    df_reports["end_mileage"] = pd.to_numeric(
        df_reports["end_mileage"], errors="coerce"
    ).fillna(0)

    df_reports = df_reports[df_reports["status"] == "Correct"]

    latest_mileage = (
        df_reports.sort_values("date")
        .groupby("vehicle_no")
        .tail(1)[["vehicle_no", "end_mileage"]]
        .rename(columns={"end_mileage": "current_mileage"})
    )

    # -----------------------
    # Last Alignment & Air Filter
    # -----------------------
    if not expense_df.empty:

        expense_df["description"] = expense_df["description"].astype(str)

        # Alignment
        align_df = expense_df[
            expense_df["description"].str.contains("alignment", case=False, na=False)
        ].copy()

        align_df["alignment_km"] = (
            align_df["description"].str.extract(r'(\d+)').astype(float)
        )

        latest_align = (
            align_df.sort_values("alignment_km")
            .groupby("vehicle_no")
            .last()
            .reset_index()
        )[["vehicle_no", "alignment_km"]]

        # Air Filter
        air_df = expense_df[
            expense_df["description"].str.contains("air filter", case=False, na=False)
        ].copy()

        air_df["air_filter_km"] = (
            air_df["description"].str.extract(r'(\d+)').astype(float)
        )

        latest_air = (
            air_df.sort_values("air_filter_km")
            .groupby("vehicle_no")
            .last()
            .reset_index()
        )[["vehicle_no", "air_filter_km"]]

    else:
        latest_align = pd.DataFrame(columns=["vehicle_no", "alignment_km"])
        latest_air = pd.DataFrame(columns=["vehicle_no", "air_filter_km"])

    # -----------------------
    # Clean vehicle numbers
    # -----------------------
    def clean(df):
        if not df.empty:
            df["vehicle_no"] = (
                df["vehicle_no"]
                .astype(str)
                .str.replace("-", "", regex=False)
                .str.strip()
            )
        return df

    master_df = clean(master_df)
    latest_mileage = clean(latest_mileage)
    latest_align = clean(latest_align)
    latest_air = clean(latest_air)

    # -----------------------
    # Merge all
    # -----------------------
    vehicle_data = master_df.merge(
        latest_mileage, on="vehicle_no", how="left"
    ).merge(
        latest_align, on="vehicle_no", how="left"
    ).merge(
        latest_air, on="vehicle_no", how="left"
    ).fillna(0)

    # -----------------------
    # Convert numeric columns
    # -----------------------
    numeric_cols = [
        "alignment_km",
        "alignment_interval_km",
        "air_filter_km",
        "air_filter_interval_km",
        "current_mileage"
    ]

    for col in numeric_cols:
        if col in vehicle_data.columns:
            vehicle_data[col] = pd.to_numeric(
                vehicle_data[col],
                errors="coerce"
            ).fillna(0)

    # -----------------------
    # Calculate next services
    # -----------------------
    vehicle_data["next_alignment"] = (
        vehicle_data["alignment_km"]
        + vehicle_data["alignment_interval_km"]
    )

    vehicle_data["next_air_filter"] = (
        vehicle_data["air_filter_km"]
        + vehicle_data["air_filter_interval_km"]
    )

    return vehicle_data

# -------------------------------------------------------------------
# ADMIN DASHBOARD PAGE
# -------------------------------------------------------------------
def page_admin_dashboard():
    # Executive dashboard — UI rebuilt without changing the source data or core formulas.
    df = pd.DataFrame(daily_sheet.get_all_records())
    if df.empty:
        st.warning("No data available.")
        return

    if "status" in df.columns:
        df = df[df["status"] == "Correct"].copy()
    if df.empty:
        st.warning("No approved data available.")
        return

    numeric_cols = [
        "fare", "driver_salary", "platform_fee", "toll_fee", "tip",
        "daily_mileage", "uber_hire_mileage", "loss_mileage",
        "amount_to_ceekay", "bank_deposit", "vehicle_running_cost"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0.0

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    if df.empty:
        st.warning("No valid dated records are available.")
        return

    if "show_overview_figures" not in st.session_state:
        st.session_state.show_overview_figures = False

    top_left, top_mid, top_right = st.columns([4.4, 1.0, 2.6])
    with top_left:
        vehicle_options = ["All Vehicles"]
        if "vehicle_no" in df.columns:
            vehicle_options.extend(sorted({
                str(vehicle).strip()
                for vehicle in df["vehicle_no"].dropna().tolist()
                if str(vehicle).strip()
            }))
        selected_vehicle = st.selectbox(
            "Vehicle",
            vehicle_options,
            index=0,
            key="dashboard_vehicle_filter"
        )

    with top_mid:
        label = "Hide Figures" if st.session_state.show_overview_figures else "View Figures"
        if st.button(label, key="overview_figure_toggle", use_container_width=True):
            st.session_state.show_overview_figures = not st.session_state.show_overview_figures
            st.rerun()
    with top_right:
        d1, d2 = st.columns(2)
        start_date = d1.date_input("From", df["date"].min().date(), key="dash_from")
        end_date = d2.date_input("To", df["date"].max().date(), key="dash_to")

    filtered = df[
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date))
    ].copy()

    if selected_vehicle != "All Vehicles":
        filtered = filtered[
            filtered["vehicle_no"].astype(str).str.strip() == selected_vehicle
        ].copy()

    if filtered.empty:
        st.info("No records found for the selected date range.")
        return

    total_revenue = filtered["fare"].sum()
    total_salary = filtered["driver_salary"].sum()
    total_platform = filtered["platform_fee"].sum()
    running_cost = filtered["vehicle_running_cost"].sum()
    total_cost = total_salary + total_platform + running_cost
    net_profit = total_revenue - total_cost
    total_mileage = filtered["daily_mileage"].sum()
    profit_per_km = net_profit / total_mileage if total_mileage > 0 else 0
    total_trips = len(filtered)

    def private(value):
        return value if st.session_state.show_overview_figures else "********"

    def metric_card(icon, label, value, note, accent):
        st.markdown(
            f'''<div class="ck-kpi-card">
                <div class="ck-kpi-top">
                    <div class="ck-kpi-icon" style="background:{accent}18;color:{accent};">{icon}</div>
                    <div class="ck-kpi-copy">
                        <div class="ck-kpi-label">{label}</div>
                        <div class="ck-kpi-value" style="color:{accent};">{value}</div>
                        <div class="ck-kpi-note">{note}</div>
                    </div>
                </div>
            </div>''',
            unsafe_allow_html=True,
        )

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        metric_card("▣", "TOTAL REVENUE", private(f"Rs. {total_revenue:,.0f}"), "Total fare collected", "#079455")
    with k2:
        metric_card("●", "TOTAL PROFIT", private(f"Rs. {net_profit:,.0f}"), "After running costs", "#2563eb")
    with k3:
        metric_card("◉", "TOTAL KM TRAVELLED", private(f"{total_mileage:,.0f} km"), "Total mileage", "#9333ea")
    with k4:
        metric_card("↗", "AVG PROFIT / KM", private(f"Rs. {profit_per_km:,.2f}"), "Average profit per KM", "#ea580c")
    with k5:
        metric_card("⚑", "TOTAL TRIPS", private(f"{total_trips:,.0f}"), "Recorded trips", "#0f9f9a")

    st.markdown('<div class="ck-dashboard-gap"></div>', unsafe_allow_html=True)

    trend = filtered.copy()
    trend["month"] = trend["date"].dt.to_period("M").dt.to_timestamp()
    trend = trend.groupby("month", as_index=False)["fare"].sum()
    fig_revenue = px.line(trend, x="month", y="fare", markers=True)
    fig_revenue.update_traces(line=dict(width=3, color="#079455"), marker=dict(size=7, color="#079455"), fill="tozeroy", fillcolor="rgba(7,148,85,.08)")
    fig_revenue.update_layout(
        margin=dict(l=12, r=12, t=18, b=10), height=300,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="", yaxis_title="", showlegend=False,
        font=dict(color="#475569", size=11),
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#edf2f7", tickprefix="Rs. ")
    )

    profit_amount = max(net_profit, 0)
    expense_amount = max(total_cost, 0)
    donut_df = pd.DataFrame({"Category": ["Profit", "Expenses"], "Amount": [profit_amount, expense_amount]})
    fig_profit = px.pie(donut_df, names="Category", values="Amount", hole=.67,
                        color="Category", color_discrete_map={"Profit":"#12a36d", "Expenses":"#ef4444"})
    fig_profit.update_traces(textinfo="none", hovertemplate="%{label}: Rs. %{value:,.0f}<extra></extra>")
    profit_pct = profit_amount / (profit_amount + expense_amount) * 100 if (profit_amount + expense_amount) else 0
    fig_profit.update_layout(
        margin=dict(l=8,r=8,t=8,b=8), height=255, showlegend=True,
        legend=dict(orientation="h", y=-.04, x=.5, xanchor="center"),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#475569", size=11),
        annotations=[dict(text=f"<b>{profit_pct:.0f}%</b><br>Profit", x=.5,y=.5,font_size=20,showarrow=False,font_color="#0f172a")]
    )

    # Vehicle financial summary uses the SAME cost components as Vehicle Report.
    # Dashboard date filter applies to revenue/daily operating values. Existing vehicle
    # variable expenses and monthly depreciation follow the Vehicle Report logic.
    vehicle_summary = filtered.groupby("vehicle_no", as_index=False).agg(
        fare=("fare", "sum"),
        driver_salary=("driver_salary", "sum"),
        toll_fee=("toll_fee", "sum"),
        tip=("tip", "sum"),
        platform_fee=("platform_fee", "sum"),
        daily_mileage=("daily_mileage", "sum"),
    )

    variable_df = pd.DataFrame(vehicle_variable_sheet.get_all_records())
    if not variable_df.empty:
        variable_df["amount"] = pd.to_numeric(variable_df.get("amount", 0), errors="coerce").fillna(0)
    master_df = pd.DataFrame(vehicle_master_sheet.get_all_records())

    vehicle_rows = []
    for _, vr in vehicle_summary.iterrows():
        vehicle_no = vr["vehicle_no"]
        total_revenue_v = float(vr["fare"])
        driver_cost_v = float(vr["driver_salary"] + vr["toll_fee"] + vr["tip"])
        platform_fee_v = float(vr["platform_fee"])

        master_match = master_df[master_df["vehicle_no"] == vehicle_no] if not master_df.empty and "vehicle_no" in master_df.columns else pd.DataFrame()
        if not master_match.empty:
            purchase_cost_v = num(master_match.iloc[0].get("purchase_cost", 0))
            useful_years_v = num(master_match.iloc[0].get("useful_years", 0))
            cost_per_km_v = num(master_match.iloc[0].get("cost_per_km", 0))
            monthly_depreciation_v = purchase_cost_v / (useful_years_v * 12) if useful_years_v > 0 else 0.0
        else:
            cost_per_km_v = 0.0
            monthly_depreciation_v = 0.0

        running_cost_v = float(vr["daily_mileage"]) * cost_per_km_v
        if not variable_df.empty and "vehicle_no" in variable_df.columns:
            variable_cost_v = float(variable_df.loc[variable_df["vehicle_no"] == vehicle_no, "amount"].sum())
        else:
            variable_cost_v = 0.0

        total_cost_v = driver_cost_v + platform_fee_v + running_cost_v + variable_cost_v + monthly_depreciation_v
        net_profit_v = total_revenue_v - total_cost_v
        vehicle_rows.append({
            "vehicle_no": vehicle_no,
            "revenue": total_revenue_v,
            "total_cost": total_cost_v,
            "net_profit": net_profit_v,
        })

    vehicle_summary = pd.DataFrame(vehicle_rows)
    if not vehicle_summary.empty:
        vehicle_summary = vehicle_summary.sort_values("net_profit", ascending=False)

    c1, c2, c3 = st.columns([1.7, 1.0, 1.25])
    with c1:
        st.markdown('<div class="ck-panel-title">Revenue Trend</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_revenue, use_container_width=True, config={"displayModeBar": False})
    with c2:
        st.markdown('<div class="ck-panel-title">Profit vs Expense</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_profit, use_container_width=True, config={"displayModeBar": False})
    with c3:
        st.markdown('<div class="ck-panel-title">Top Performing Vehicles</div>', unsafe_allow_html=True)
        if vehicle_summary.empty:
            st.caption("No vehicle data available.")
        else:
            for rank, (_, row) in enumerate(vehicle_summary.head(5).iterrows(), start=1):
                revenue_value = private(f"Rs. {row['revenue']:,.0f}")
                cost_value = private(f"Rs. {row['total_cost']:,.0f}")
                profit_value = private(f"Rs. {row['net_profit']:,.0f}")
                st.markdown(
                    f'''<div class="ck-rank-row"><div class="ck-rank-no">{rank}</div>
                    <div class="ck-rank-main"><b>{row['vehicle_no']}</b>
                    <span>Revenue: {revenue_value} &nbsp; | &nbsp; Cost: {cost_value}</span></div>
                    <div class="ck-rank-value"><span style="font-size:.68rem;color:#64748b;display:block;">NET PROFIT</span>{profit_value}</div></div>''',
                    unsafe_allow_html=True,
                )

    expense_df = pd.DataFrame({
        "Category": ["Vehicle Running Costs", "Driver Salary", "Platform Fee"],
        "Amount": [running_cost, total_salary, total_platform]
    })
    fig_expense = px.pie(expense_df, names="Category", values="Amount", hole=.55)
    fig_expense.update_traces(textinfo="none", hovertemplate="%{label}: Rs. %{value:,.0f}<extra></extra>")
    fig_expense.update_layout(
        margin=dict(l=4,r=4,t=4,b=4), height=240,
        legend=dict(orientation="v", y=.5, x=1.0),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#475569", size=10)
    )

    recent = filtered.sort_values(["date"], ascending=False).head(5)

    alerts = []
    vehicle_data = get_vehicle_service_data()
    if not vehicle_data.empty:
        for _, row in vehicle_data.iterrows():
            current = row.get("current_mileage", 0)
            if row.get("alignment_interval_km", 0) > 0:
                if current >= row.get("next_alignment", 0):
                    alerts.append(("danger", f"{row['vehicle_no']} - Wheel Alignment OVERDUE", f"Current mileage: {current:,.0f} km"))
                elif current >= row.get("next_alignment", 0) - 500:
                    alerts.append(("warning", f"{row['vehicle_no']} - Wheel Alignment Due Soon", f"Current mileage: {current:,.0f} km"))
            if row.get("air_filter_interval_km", 0) > 0:
                if current >= row.get("next_air_filter", 0):
                    alerts.append(("danger", f"{row['vehicle_no']} - Air Filter OVERDUE", f"Current mileage: {current:,.0f} km"))
                elif current >= row.get("next_air_filter", 0) - 1000:
                    alerts.append(("warning", f"{row['vehicle_no']} - Air Filter Due Soon", f"Current mileage: {current:,.0f} km"))

    b1, b2, b3 = st.columns([1.15, 1.2, 1.15])
    with b1:
        st.markdown('<div class="ck-panel-title">Expense Summary</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_expense, use_container_width=True, config={"displayModeBar": False})
    with b2:
        st.markdown('<div class="ck-panel-title">Recent Entries</div>', unsafe_allow_html=True)
        if recent.empty:
            st.caption("No recent entries.")
        else:
            for _, row in recent.iterrows():
                amount = private(f"Rs. {row['fare']:,.0f}")
                st.markdown(
                    f'''<div class="ck-recent-row"><div><b>{row['date'].strftime('%Y/%m/%d')}</b><span>{row['vehicle_no']}</span></div>
                    <strong>{amount}</strong></div>''', unsafe_allow_html=True)
    with b3:
        st.markdown('<div class="ck-panel-title">Service Alerts</div>', unsafe_allow_html=True)
        if alerts:
            for level, title, detail in alerts[:5]:
                symbol = "!" if level == "danger" else "•"
                st.markdown(
                    f'''<div class="ck-alert ck-alert-{level}"><span class="ck-alert-symbol">{symbol}</span>
                    <div><b>{title}</b><small>{detail}</small></div></div>''', unsafe_allow_html=True)
        else:
            st.markdown('<div class="ck-alert ck-alert-success"><span class="ck-alert-symbol">✓</span><div><b>All vehicles are service-ready</b><small>No service alerts at the moment.</small></div></div>', unsafe_allow_html=True)

    st.markdown('<div class="ck-dashboard-footer">© 2026 CEEKAY TOURS. Management Console.</div>', unsafe_allow_html=True)

def page_admin_daily_profit():

    st.markdown("<h2>💰 Daily Profit Report</h2>", unsafe_allow_html=True)

    df = pd.DataFrame(daily_sheet.get_all_records())

    numeric_cols = [
    "fare", "driver_salary", "toll_fee", "tip", "other_expenses",
    "cash_collected", "daily_mileage", "uber_hire_mileage",
    "loss_mileage", "platform_fee", "amount_to_ceekay", "bank_deposit"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    selected_date = st.date_input("Select a Date")
    df_day = df[df["date"] == selected_date.strftime("%Y-%m-%d")]

    if df_day.empty:
        st.warning("No data found for this date.")
        return

    total_fare = df_day["fare"].sum()
    total_salary = (
        df_day["driver_salary"].sum()
        + df_day["tip"].sum()
    )
    platform_fee = df_day["platform_fee"].sum()
    total_daily_mileage = df_day["daily_mileage"].sum()

    
    df_day["vehicle_running_cost"] = pd.to_numeric(
    df_day.get("vehicle_running_cost", 0),
    errors="coerce"
    ).fillna(0)

    vehicle_cost = df_day["vehicle_running_cost"].sum()
    total_cost = total_salary + vehicle_cost + platform_fee
    profit = total_fare - total_cost

    cash_flow = (
        df_day["amount_to_ceekay"].sum()
        + df_day["bank_deposit"].sum()
        - df_day["platform_fee"].sum()
    )

    col1, col2 = st.columns(2)
    col1.metric("Total Fare", f"Rs. {total_fare:,.2f}")
    col2.metric("Total Cost", f"Rs. {total_cost:,.2f}")

    col3, col4 = st.columns(2)
    col3.metric("Profit", f"Rs. {profit:,.2f}")
    col4.metric("Cash Flow", f"Rs. {cash_flow:,.2f}")

    st.metric("Mileage", f"{total_daily_mileage} km")

    st.subheader("Daily Breakdown")
    st.dataframe(df_day)

# -------------------------------------------------------------------
# ADMIN RANGE PROFIT REPORT
# -------------------------------------------------------------------
def page_admin_range_profit():

    st.markdown("<h2>📂 Range Profit Report</h2>", unsafe_allow_html=True)

    df = pd.DataFrame(daily_sheet.get_all_records())
    

    numeric_cols = [
    "fare", "driver_salary", "toll_fee", "tip", "other_expenses",
    "cash_collected", "daily_mileage", "uber_hire_mileage",
    "loss_mileage", "platform_fee", "amount_to_ceekay", "bank_deposit"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    col1, col2 = st.columns(2)
    from_date = col1.date_input("From Date")
    to_date = col2.date_input("To Date")

    df_range = df[
        (df["date"] >= from_date.strftime("%Y-%m-%d")) &
        (df["date"] <= to_date.strftime("%Y-%m-%d"))
    ]

    if df_range.empty:
        st.warning("No data available for this range.")
        return

    total_fare = df_range["fare"].sum()
    total_salary = (
        df_range["driver_salary"].sum()
        + df_range["tip"].sum()
    )
    platform_fee = df_range["platform_fee"].sum()
    total_daily_mileage = df_range["daily_mileage"].sum()

    

    df_range["vehicle_running_cost"] = pd.to_numeric(
    df_range.get("vehicle_running_cost", 0),
    errors="coerce"
    ).fillna(0)

    vehicle_cost = df_range["vehicle_running_cost"].sum()
    total_cost = total_salary + vehicle_cost + platform_fee
    profit = total_fare - total_cost

    cash_flow = (
        df_range["amount_to_ceekay"].sum()
        + df_range["bank_deposit"].sum()
        - df_range["platform_fee"].sum()
    )

    col1, col2 = st.columns(2)
    col1.metric("Total Fare", f"Rs. {total_fare:,.2f}")
    col2.metric("Total Cost", f"Rs. {total_cost:,.2f}")

    col3, col4 = st.columns(2)
    col3.metric("Profit", f"Rs. {profit:,.2f}")
    col4.metric("Cash Flow", f"Rs. {cash_flow:,.2f}")

    st.metric("Mileage", f"{total_daily_mileage} km")

    st.subheader("All Entries in Selected Range")
    st.dataframe(df_range)

# -------------------------------------------------------------------
# ADMIN MONTHLY PROFIT REPORT
# -------------------------------------------------------------------
def page_admin_monthly_profit():

    st.markdown("<h2>📆 Monthly Profit Summary</h2>", unsafe_allow_html=True)

    df = pd.DataFrame(daily_sheet.get_all_records())
  

    numeric_cols = [
    "fare", "driver_salary", "toll_fee", "tip", "other_expenses",
    "cash_collected", "daily_mileage", "uber_hire_mileage",
    "loss_mileage", "platform_fee", "amount_to_ceekay", "bank_deposit"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    selected_month = st.date_input("Select a Month")
    month_str = selected_month.strftime("%Y-%m")

    df_month = df[df["date"].str.startswith(month_str)]

    if df_month.empty:
        st.warning("No data found for this month.")
        return

    total_fare = df_month["fare"].sum()
    total_salary = (
    df_month["driver_salary"].sum()
    + df_month["toll_fee"].sum()
    + df_month["tip"].sum()
    )
    platform_fee = df_month["platform_fee"].sum()
    total_daily_mileage = df_month["daily_mileage"].sum()

    

    df_month["vehicle_running_cost"] = pd.to_numeric(
    df_month.get("vehicle_running_cost", 0),
    errors="coerce"
    ).fillna(0)

    vehicle_cost = df_month["vehicle_running_cost"].sum()
    total_cost = total_salary + vehicle_cost + platform_fee
    profit = total_fare - total_cost

    cash_flow = (
        df_month["amount_to_ceekay"].sum()
        + df_month["bank_deposit"].sum()
        - df_month["platform_fee"].sum()
    )

    col1, col2 = st.columns(2)
    col1.metric("Total Fare", f"Rs. {total_fare:,.2f}")
    col2.metric("Total Cost", f"Rs. {total_cost:,.2f}")

    col3, col4 = st.columns(2)
    col3.metric("Profit", f"Rs. {profit:,.2f}")
    col4.metric("Cash Flow", f"Rs. {cash_flow:,.2f}")

    st.metric("Mileage", f"{total_daily_mileage} km")

    st.subheader("All Entries for This Month")
    st.dataframe(df_month)

# -------------------------------------------------------------------
# PROFIT REPORTS MASTER PAGE
# -------------------------------------------------------------------
def page_profit_reports():

    # Main page heading is rendered centrally by the application shell.
    mode = st.selectbox(
        "Select Report Type",
        ["Daily Profit", "Range Profit", "Monthly Profit"]
    )

    if mode == "Daily Profit":
        page_admin_daily_profit()
    elif mode == "Range Profit":
        page_admin_range_profit()
    elif mode == "Monthly Profit":
        page_admin_monthly_profit()

def page_vehicle_report():

    # Main page heading is rendered centrally by the application shell.
    vehicles = drivers_df["vehicle_no"].unique().tolist()
    selected_vehicle = st.selectbox("Select Vehicle", vehicles)

    # ---------------- Revenue Data ----------------
    df_reports = pd.DataFrame(daily_sheet.get_all_records())
    df_reports = df_reports[
        (df_reports["vehicle_no"] == selected_vehicle) &
        (df_reports["status"] == "Correct")
    ]

    if df_reports.empty:
        st.warning("No revenue data available.")
        return

    numeric_cols = ["fare", "driver_salary", "daily_mileage", "platform_fee"]
    for col in numeric_cols:
        df_reports[col] = pd.to_numeric(df_reports[col], errors="coerce").fillna(0)

    total_revenue = df_reports["fare"].sum()
    total_driver_salary = (
    df_reports["driver_salary"].sum()
    + df_reports["toll_fee"].sum()
    + df_reports["tip"].sum()
    )
    total_platform_fee = df_reports["platform_fee"].sum()

    total_mileage = df_reports["daily_mileage"].sum()
        
    # ---------------- Variable Costs ----------------
    df_variable = pd.DataFrame(vehicle_variable_sheet.get_all_records())
    df_variable["amount"] = pd.to_numeric(df_variable["amount"], errors="coerce").fillna(0)
    df_variable = df_variable[df_variable["vehicle_no"] == selected_vehicle]

    if not df_variable.empty:
        df_variable["amount"] = pd.to_numeric(df_variable["amount"], errors="coerce").fillna(0)
        total_variable = df_variable["amount"].sum()
    else:
        total_variable = 0

    # ---------------- Depreciation + Master Data ----------------
    df_master = pd.DataFrame(vehicle_master_sheet.get_all_records())
    df_master = df_master[df_master["vehicle_no"] == selected_vehicle]

    if not df_master.empty:
        purchase_cost = float(df_master.iloc[0]["purchase_cost"])
        useful_years = float(df_master.iloc[0]["useful_years"])
        cost_per_km = float(df_master.iloc[0].get("cost_per_km", 0))
        monthly_depreciation = purchase_cost / (useful_years * 12)
    else:
        monthly_depreciation = 0
        cost_per_km = 0

    vehicle_running_cost = total_mileage * cost_per_km

    # ---------------- Final Calculation ----------------
    total_cost = (
        total_driver_salary
        + vehicle_running_cost
        + total_variable
        + total_platform_fee
        + monthly_depreciation
    )

    net_profit = total_revenue - total_cost

    # ---------------- Display ----------------
    st.metric("Total Revenue", f"Rs. {total_revenue:,.2f}")
    st.metric("Total Cost", f"Rs. {total_cost:,.2f}")
    st.metric("Net Profit", f"Rs. {net_profit:,.2f}")

    st.markdown("---")
    st.write("### Cost Breakdown")
    st.write(f"Driver Salary: Rs. {total_driver_salary:,.2f}")
    st.write(f"Platform Fee: Rs. {total_platform_fee:,.2f}")
    st.write(f"Running Cost (Mileage): Rs. {vehicle_running_cost:,.2f}")
    st.write(f"Variable Repairs: Rs. {total_variable:,.2f}")
    st.write(f"Monthly Depreciation: Rs. {monthly_depreciation:,.2f}")
    
    st.markdown("---")
    st.subheader("💰 Expense Details")

    if not df_variable.empty:
        df_variable["amount"] = pd.to_numeric(df_variable["amount"], errors="coerce").fillna(0)
        df_variable = df_variable.sort_values("date", ascending=False)
        st.dataframe(df_variable)
    else:
        st.info("No expenses recorded for this vehicle.")

    


    # 🔥 ADD STEP 4 HERE
    st.markdown("---")
    st.subheader("📊 Expense Distribution")

    if not df_variable.empty:

        expense_summary = df_variable.groupby("category")["amount"].sum().reset_index()

        fig = px.pie(
            expense_summary,
            names="category",
            values="amount",
            title="Expense Breakdown by Category"
        )

        st.plotly_chart(fig, use_container_width=True)



# -------------------------------------------------------------------
# SAFE NUMBER CONVERTER
# -------------------------------------------------------------------
def num(v):
    try:
        return float(v)
    except:
        return 0.0

def page_vehicle_entry():

    # Main page heading is rendered centrally by the application shell.
    tab1, tab2 = st.tabs([
        "➕ Add Vehicle",
        "💰 Add Expense"
    ])

   
    # ------------------------------------------------
    # TAB 1 — ADD VEHICLE
    # ------------------------------------------------
    with tab1:

        st.subheader("Register New Vehicle")

        vehicle_no = st.text_input("Vehicle Number")
        purchase_date = st.date_input("Purchase Date")
        purchase_cost = st.number_input("Purchase Cost (Rs.)", min_value=0.0)
        useful_years = st.number_input("Useful Life (Years)", min_value=1.0, value=5.0)

        if st.button("Save Vehicle"):

            if vehicle_no == "":
                st.error("Vehicle number required")
            else:
                vehicle_master_sheet.append_row([
                    vehicle_no,
                    purchase_date.strftime("%Y-%m-%d"),
                    purchase_cost,
                    useful_years
                ])
                st.success("Vehicle added successfully!")

    # ------------------------------------------------
    # TAB 2 — VARIABLE COST
    # ------------------------------------------------
    with tab2:

        st.subheader("Add Repair / Variable Expense")

        vehicles = drivers_df["vehicle_no"].unique().tolist()

        if not vehicles:
            st.warning("No vehicles available")
        else:

            selected_vehicle = st.selectbox("Select Vehicle", vehicles)

            expense_date = st.date_input("Expense Date")

            expense_categories = [
                "Fuel",
                "Leasing",
                "Insurance",
                "Repair",
                "Tyre",
                "Battery",
                "Service",
                "License",
                "GPS",
                "Donations",
                "Other"
            ]

            category = st.selectbox("Expense Category", expense_categories)

            description = st.text_input("Description")
            amount = st.number_input("Amount (Rs.)", min_value=0.0)


            if st.button("Save Variable Expense"):

                vehicle_variable_sheet.append_row([
                    expense_date.strftime("%Y-%m-%d"),
                    selected_vehicle,
                    category,
                    description,
                    amount
             ])

                st.success("Expense recorded!")


# -------------------------------------------------------------------
# ADMIN SUBMISSIONS PAGE
# -------------------------------------------------------------------
def page_admin_submissions():

    st.markdown("## 📁 Pending Driver Submissions")

    df = pd.DataFrame(daily_sheet.get_all_records())

    if df.empty:
        st.info("No submissions found.")
        return

    # Only pending items
    df = df[df["status"].astype(str).str.lower() == "pending"]

    if df.empty:
        st.success("No pending submissions. All done!")
        return

    df["label"] = df.apply(
        lambda r: f"{r['driver_name']} | {r['date']} | Fare Rs.{num(r['fare']):,.2f}",
        axis=1
    )

    selected_label = st.selectbox("Select a submission to review", df["label"].tolist())

    row = df[df["label"] == selected_label].iloc[0]
    sheet_row = row.name + 2

    st.markdown("### 📄 Submission Details")

    st.write("### Driver Information")
    st.write(f"**Driver:** {row['driver_name']}")
    st.write(f"**Date:** {row['date']}")
    st.write(f"**Vehicle:** {row['vehicle_no']}")

    st.write("### Mileage")
    st.write(f"Start Mileage: **{row['start_mileage']}**")
    st.write(f"End Mileage: **{row['end_mileage']}**")
    st.write(f"Daily Mileage: **{row['daily_mileage']} km**")
    st.write(f"Uber Mileage: **{row['uber_hire_mileage']} km**")
    st.write(f"Loss Mileage: **{row['loss_mileage']} km**")

    st.write("### Earnings")
    st.write(f"Fare: **Rs. {num(row['fare']):,.2f}**")
    st.write(f"Tip: **Rs. {num(row['tip']):,.2f}**")
    st.write(f"Toll Fee: **Rs. {num(row['toll_fee']):,.2f}**")
    st.write(f"Other Expenses: **Rs. {num(row['other_expenses']):,.2f}**")
    st.write(f"Cash Collected: **Rs. {num(row['cash_collected']):,.2f}**")
    st.write(f"Amount to CEEKAY: **Rs. {num(row['amount_to_ceekay']):,.2f}**")


    st.write("### Current Status")
    st.write(f"Status: **{row['status']}**")
    st.write(f"Admin Note: **{row['admin_note']}**")

    st.markdown("---")

    st.markdown("## 🛠 Admin Approval Panel")

    admin_note = st.text_input("Admin Note", row.get("admin_note", ""))

    platform_fee = st.number_input(
        "Platform Fee (Rs.)",
        min_value=0.0,
        value=num(row.get("platform_fee", 0))
    )

    bank_deposit = st.number_input(
        "Bank Deposit (Rs.)",
        min_value=0.0,
        value=num(row.get("bank_deposit", 0))
    )

    col1, col2 = st.columns(2)

    if col1.button("✅ Approve"):
        daily_sheet.update_cell(sheet_row, 19, "Correct")
        daily_sheet.update_cell(sheet_row, 20, admin_note)
        daily_sheet.update_cell(sheet_row, 22, platform_fee)
        daily_sheet.update_cell(sheet_row, 23, bank_deposit)

        st.success("Submission approved successfully!")
        st.rerun()

    if col2.button("❌ Reject"):
        daily_sheet.update_cell(sheet_row, 19, "Incorrect")
        daily_sheet.update_cell(sheet_row, 20, admin_note)
        daily_sheet.update_cell(sheet_row, 22, platform_fee)
        daily_sheet.update_cell(sheet_row, 23, bank_deposit)

        st.error("Submission rejected.")
        st.rerun()

# -------------------------------------------------------------------
# ADMIN DAILY ENTRY — DIRECT ENTRY, NO DRIVER LOGIN / APPROVAL REQUIRED
# -------------------------------------------------------------------
def page_admin_daily_entry():

    # Main page heading/subtitle are rendered centrally by the application shell.
    drivers_current = pd.DataFrame(drivers_sheet.get_all_records())

    if drivers_current.empty or "driver_name" not in drivers_current.columns:
        st.warning("No drivers are available in the drivers sheet.")
        return

    drivers_current = drivers_current.copy()
    drivers_current["driver_name"] = drivers_current["driver_name"].astype(str).str.strip()
    drivers_current = drivers_current[drivers_current["driver_name"] != ""]

    if drivers_current.empty:
        st.warning("No valid drivers are available in the drivers sheet.")
        return

    driver_names = drivers_current["driver_name"].tolist()

    # Quick-entry header: driver first, vehicle is still taken automatically.
    selected_driver_name = st.selectbox("Driver", driver_names)
    selected_driver = drivers_current[
        drivers_current["driver_name"] == selected_driver_name
    ].iloc[0].to_dict()

    vehicle_no = str(selected_driver.get("vehicle_no", "")).strip()
    st.caption(f"Assigned Vehicle: {vehicle_no or 'Not assigned'}")

    last_end_mileage = get_last_end_mileage(selected_driver_name)

    # A versioned form key clears fields only after a successful save.
    if "daily_entry_form_version" not in st.session_state:
        st.session_state.daily_entry_form_version = 0
    form_version = st.session_state.daily_entry_form_version

    def clean_default_number(value):
        """Show stored mileage cleanly without unnecessary .00."""
        try:
            value = float(value)
            return str(int(value)) if value.is_integer() else str(value)
        except Exception:
            return str(value or "")

    def parse_quick_number(raw_value, label, required=False):
        """Blank optional fields become zero; required fields stay blank until entered."""
        raw = str(raw_value or "").strip().replace(",", "")
        if raw == "":
            if required:
                st.error(f"{label} is required.")
                return None
            return 0.0
        try:
            value = float(raw)
        except ValueError:
            st.error(f"Please enter a valid number for {label}.")
            return None
        if value < 0:
            st.error(f"{label} cannot be negative.")
            return None
        return value

    with st.form(f"admin_daily_entry_form_{form_version}", clear_on_submit=False):
        # Compact keyboard-first layout. Text inputs are intentional: they can start
        # truly blank, unlike number_input fields that display 0.00 by default.
        report_date = st.date_input("Date", value=date.today())

        st.markdown("#### Mileage")
        m1, m2, m3 = st.columns(3)
        start_mileage_raw = m1.text_input(
            "Start Mileage *",
            value=clean_default_number(last_end_mileage),
            placeholder="Start mileage",
            key=f"daily_start_{form_version}",
        )
        end_mileage_raw = m2.text_input(
            "End Mileage *",
            value="",
            placeholder="Enter end mileage",
            key=f"daily_end_{form_version}",
        )
        uber_hire_mileage_raw = m3.text_input(
            "Uber Hire Mileage *",
            value="",
            placeholder="Enter hire mileage",
            key=f"daily_uber_{form_version}",
        )

        st.markdown("#### Collection")
        f1, f2 = st.columns(2)
        fare_raw = f1.text_input(
            "Fare (Rs.) *",
            value="",
            placeholder="Enter fare",
            key=f"daily_fare_{form_version}",
        )
        cash_collected_raw = f2.text_input(
            "Cash Collected (Rs.) *",
            value="",
            placeholder="Enter cash collected",
            key=f"daily_cash_{form_version}",
        )

        st.markdown("#### Additional Amounts")
        a1, a2, a3 = st.columns(3)
        tip_raw = a1.text_input(
            "Tip (Rs.)",
            value="",
            placeholder="Optional",
            key=f"daily_tip_{form_version}",
        )
        toll_fee_raw = a2.text_input(
            "Toll Fee (Rs.)",
            value="",
            placeholder="Optional",
            key=f"daily_toll_{form_version}",
        )
        other_expenses_raw = a3.text_input(
            "Other Expenses (Rs.)",
            value="",
            placeholder="Optional",
            key=f"daily_other_{form_version}",
        )

        a4, a5 = st.columns(2)
        platform_fee_raw = a4.text_input(
            "Platform Fee (Rs.)",
            value="",
            placeholder="Optional",
            key=f"daily_platform_{form_version}",
        )
        bank_deposit_raw = a5.text_input(
            "Bank Deposit (Rs.)",
            value="",
            placeholder="Optional",
            key=f"daily_bank_{form_version}",
        )

        admin_note = st.text_input(
            "Note",
            value="",
            placeholder="Optional note",
            key=f"daily_note_{form_version}",
        )

        st.caption("Blank optional amount fields are automatically treated as Rs. 0.00.")

        action1, action2 = st.columns(2)
        calculate_clicked = action1.form_submit_button(
            "Show Salary Calculation",
            use_container_width=True
        )
        submitted = action2.form_submit_button(
            "Save Daily Entry",
            use_container_width=True
        )

    # Keyboard helper: Enter behaves like moving to the next visible field instead
    # of prematurely submitting the Streamlit form. Tab continues to work normally.
    components.html(
        """
        <script>
        (function () {
          const doc = window.parent.document;
          const marker = 'data-ck-enter-next';
          if (doc.body.getAttribute(marker) === '1') return;
          doc.body.setAttribute(marker, '1');

          doc.addEventListener('keydown', function (e) {
            if (e.key !== 'Enter' || e.shiftKey || e.ctrlKey || e.altKey || e.metaKey) return;
            const el = e.target;
            if (!el || el.tagName !== 'INPUT') return;
            if (el.type === 'submit' || el.type === 'button' || el.type === 'checkbox') return;

            const fields = Array.from(doc.querySelectorAll('input')).filter(function (x) {
              const r = x.getBoundingClientRect();
              return !x.disabled && !x.readOnly && x.type !== 'hidden' &&
                     x.type !== 'submit' && x.type !== 'button' &&
                     r.width > 0 && r.height > 0;
            });
            const idx = fields.indexOf(el);
            if (idx >= 0 && idx < fields.length - 1) {
              e.preventDefault();
              e.stopPropagation();
              fields[idx + 1].focus();
              if (typeof fields[idx + 1].select === 'function') fields[idx + 1].select();
            }
          }, true);
        })();
        </script>
        """,
        height=0,
        width=0,
    )

    if not calculate_clicked and not submitted:
        return

    # Parse only when one of the two action buttons is clicked.
    start_mileage = parse_quick_number(start_mileage_raw, "Start Mileage", required=True)
    end_mileage = parse_quick_number(end_mileage_raw, "End Mileage", required=True)
    uber_hire_mileage = parse_quick_number(uber_hire_mileage_raw, "Uber Hire Mileage", required=True)
    fare = parse_quick_number(fare_raw, "Fare", required=True)
    cash_collected = parse_quick_number(cash_collected_raw, "Cash Collected", required=True)

    tip = parse_quick_number(tip_raw, "Tip")
    toll_fee = parse_quick_number(toll_fee_raw, "Toll Fee")
    other_expenses = parse_quick_number(other_expenses_raw, "Other Expenses")
    platform_fee = parse_quick_number(platform_fee_raw, "Platform Fee")
    bank_deposit = parse_quick_number(bank_deposit_raw, "Bank Deposit")

    values_to_check = [
        start_mileage, end_mileage, uber_hire_mileage, fare, cash_collected,
        tip, toll_fee, other_expenses, platform_fee, bank_deposit
    ]
    if any(v is None for v in values_to_check):
        return

    if end_mileage < start_mileage:
        st.error("End mileage cannot be lower than start mileage.")
        return

    # Existing operational calculations are intentionally unchanged.
    daily_mileage = max(0, end_mileage - start_mileage)
    loss_mileage = daily_mileage - uber_hire_mileage
    net_fare = max(0, fare - toll_fee)
    driver_salary = net_fare * 0.30
    total_driver_salary = driver_salary + toll_fee + tip
    amount_to_ceekay = cash_collected - total_driver_salary

    if calculate_clicked:
        st.markdown("### Driver Payment Summary")
        p1, p2, p3 = st.columns(3)
        p1.metric("Driver Salary (30%)", f"Rs. {driver_salary:,.2f}")
        p2.metric("Toll Reimbursement", f"Rs. {toll_fee:,.2f}")
        p3.metric("Tip", f"Rs. {tip:,.2f}")

        p4, p5, p6 = st.columns(3)
        p4.metric("Total Driver Payable", f"Rs. {total_driver_salary:,.2f}")
        p5.metric("Amount to CEEKAY", f"Rs. {amount_to_ceekay:,.2f}")
        p6.metric("Other Expenses", f"Rs. {other_expenses:,.2f}")

        st.caption(
            f"Daily Mileage: {daily_mileage:,.2f} km  |  "
            f"Uber Hire Mileage: {uber_hire_mileage:,.2f} km  |  "
            f"Loss Mileage: {loss_mileage:,.2f} km  |  "
            f"Net Fare for Salary: Rs. {net_fare:,.2f}"
        )
        st.info("Review the payment figures above, then click Save Daily Entry when ready.")
        return

    master_df = pd.DataFrame(vehicle_master_sheet.get_all_records())
    cost_per_km = 0.0

    if not master_df.empty and "vehicle_no" in master_df.columns:
        master_df = master_df.copy()
        master_df["vehicle_no_clean"] = (
            master_df["vehicle_no"]
            .astype(str)
            .str.replace("-", "", regex=False)
            .str.replace(" ", "", regex=False)
            .str.upper()
            .str.strip()
        )
        selected_vehicle_clean = (
            vehicle_no.replace("-", "").replace(" ", "").upper().strip()
        )
        vehicle_row = master_df[master_df["vehicle_no_clean"] == selected_vehicle_clean]
        if not vehicle_row.empty:
            cost_per_km = num(vehicle_row.iloc[0].get("cost_per_km", 0))

    vehicle_running_cost = daily_mileage * cost_per_km

    new_row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        report_date.strftime("%Y-%m-%d"),
        selected_driver_name,
        vehicle_no,
        start_mileage,
        end_mileage,
        daily_mileage,
        uber_hire_mileage,
        loss_mileage,
        fare,
        tip,
        toll_fee,
        other_expenses,
        cash_collected,
        0,
        driver_salary,
        total_driver_salary,
        amount_to_ceekay,
        "Correct",
        admin_note,
        "",
        platform_fee,
        bank_deposit,
        cost_per_km,
        vehicle_running_cost
    ]

    daily_sheet.append_row(new_row)

    st.success(
        f"Daily entry saved successfully. Total Driver Payable: Rs. {total_driver_salary:,.2f} | "
        f"Amount to CEEKAY: Rs. {amount_to_ceekay:,.2f}"
    )

    # Clear only after saving; salary preview never clears the entered data.
    st.session_state.daily_entry_form_version += 1
    st.rerun()



# -------------------------------------------------------------------
# MONTHLY CASH FLOW
# -------------------------------------------------------------------
def page_monthly_cash_flow():
    reports = pd.DataFrame(daily_sheet.get_all_records())

    if reports.empty:
        st.info("No daily reports are available yet.")
        return

    reports = reports.copy()
    if "status" in reports.columns:
        reports = reports[reports["status"].astype(str).str.lower() == "correct"]

    reports["date"] = pd.to_datetime(reports.get("date"), errors="coerce")
    reports = reports.dropna(subset=["date"])
    if reports.empty:
        st.info("No valid dated reports are available.")
        return

    reports["fare"] = pd.to_numeric(reports.get("fare", 0), errors="coerce").fillna(0)

    # Use the actual total driver payable already stored by the daily-entry logic.
    if "total_driver_salary" in reports.columns:
        reports["driver_payable"] = pd.to_numeric(reports["total_driver_salary"], errors="coerce").fillna(0)
    else:
        salary = pd.to_numeric(reports.get("driver_salary", 0), errors="coerce").fillna(0)
        toll = pd.to_numeric(reports.get("toll_fee", 0), errors="coerce").fillna(0)
        tip = pd.to_numeric(reports.get("tip", 0), errors="coerce").fillna(0)
        reports["driver_payable"] = salary + toll + tip

    reports["month"] = reports["date"].dt.strftime("%Y-%m")
    platform_fee = pd.to_numeric(reports.get("platform_fee", 0), errors="coerce").fillna(0)
    reports["platform_fee_cash"] = platform_fee

    monthly = reports.groupby("month", as_index=False).agg(
        monthly_revenue=("fare", "sum"),
        driver_payable=("driver_payable", "sum"),
        platform_fee=("platform_fee_cash", "sum"),
    )
    monthly["cash_before_electricity"] = (
        monthly["monthly_revenue"]
        - monthly["driver_payable"]
        - monthly["platform_fee"]
    )

    elec = pd.DataFrame(monthly_cash_flow_sheet.get_all_records())
    if elec.empty:
        elec = pd.DataFrame(columns=["month", "electricity_bill", "updated_at", "note"])
    if "electricity_bill" not in elec.columns:
        elec["electricity_bill"] = 0
    elec["electricity_bill"] = pd.to_numeric(elec["electricity_bill"], errors="coerce").fillna(0)
    elec["month"] = elec.get("month", "").astype(str)

    monthly = monthly.merge(elec[["month", "electricity_bill"]], on="month", how="left")
    monthly["electricity_bill"] = monthly["electricity_bill"].fillna(0)
    monthly["real_cash_flow"] = monthly["cash_before_electricity"] - monthly["electricity_bill"]
    monthly = monthly.sort_values("month")

    st.markdown("### Add / Update Electricity Bill")
    month_options = sorted(monthly["month"].unique().tolist(), reverse=True)
    selected_month = st.selectbox("Month", month_options, key="cashflow_bill_month")
    current_bill = float(monthly.loc[monthly["month"] == selected_month, "electricity_bill"].iloc[0])
    bill_raw = st.text_input(
        "Electricity Bill (Rs.)",
        value="" if current_bill == 0 else f"{current_bill:g}",
        placeholder="Enter monthly electricity bill",
        key="cashflow_electricity_bill",
    )
    note = st.text_input("Note", placeholder="Optional", key="cashflow_note")

    if st.button("Save Electricity Bill", use_container_width=True, key="save_cashflow_bill"):
        try:
            bill = float(str(bill_raw).replace(",", "").strip() or 0)
            if bill < 0:
                raise ValueError
        except ValueError:
            st.error("Please enter a valid electricity bill amount.")
            return

        values = monthly_cash_flow_sheet.get_all_values()
        row_to_update = None
        for idx, row in enumerate(values[1:], start=2):
            if row and str(row[0]).strip() == selected_month:
                row_to_update = idx
                break
        now_txt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if row_to_update:
            monthly_cash_flow_sheet.update(f"A{row_to_update}:D{row_to_update}", [[selected_month, bill, now_txt, note]])
        else:
            monthly_cash_flow_sheet.append_row([selected_month, bill, now_txt, note])
        st.success(f"Electricity bill saved for {selected_month}.")
        st.rerun()

    st.markdown("---")
    latest = monthly.iloc[-1]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Monthly Revenue", f"Rs. {latest['monthly_revenue']:,.2f}")
    c2.metric("Driver Payable", f"Rs. {latest['driver_payable']:,.2f}")
    c3.metric("Platform Fee", f"Rs. {latest['platform_fee']:,.2f}")
    c4.metric("Electricity Bill", f"Rs. {latest['electricity_bill']:,.2f}")
    c5.metric("Real Cash Flow", f"Rs. {latest['real_cash_flow']:,.2f}")
    st.caption(f"Latest month shown: {latest['month']}")

    st.markdown("### Monthly Cash Flow Trend")
    chart_df = monthly.copy()
    fig = px.line(
        chart_df, x="month", y="real_cash_flow", markers=True,
        labels={"month": "Month", "real_cash_flow": "Real Cash Flow (Rs.)"},
        title="Real Monthly Cash Flow"
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), separators=".,")
    fig.update_yaxes(tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Monthly Cash Flow Details")
    display = monthly.rename(columns={
        "month": "Month",
        "monthly_revenue": "Monthly Revenue",
        "driver_payable": "Driver Payable",
        "platform_fee": "Platform Fee",
        "cash_before_electricity": "Cash Flow Before Electricity",
        "electricity_bill": "Electricity Bill",
        "real_cash_flow": "Real Cash Flow",
    })
    for col in ["Monthly Revenue", "Driver Payable", "Platform Fee", "Cash Flow Before Electricity", "Electricity Bill", "Real Cash Flow"]:
        display[col] = display[col].map(lambda x: f"{x:,.2f}")
    st.dataframe(display, use_container_width=True, hide_index=True)


# -------------------------------------------------------------------
# SETTINGS — SAFE MASTER DATA EDITOR
# -------------------------------------------------------------------
def _settings_row_values(ws):
    values = ws.get_all_values()
    if not values:
        return [], []
    return values[0], values[1:]


def _setting_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _setting_number(value, default=0.0):
    try:
        if value in (None, ""):
            return float(default)
        return float(str(value).replace(",", "").strip())
    except Exception:
        return float(default)


def page_settings():
    st.caption("Change master/configuration values stored in the CEEKAY_Driver_Reports Google Sheet. Daily report history is protected and cannot be edited here.")

    tab1, tab2, tab3 = st.tabs([
        "Drivers & Assignment",
        "Vehicle Master",
        "Electricity Settings",
    ])

    # ---------------------------------------------------------------
    # DRIVERS / VEHICLE ASSIGNMENT
    # ---------------------------------------------------------------
    with tab1:
        st.markdown("### Drivers & Vehicle Assignment")
        headers, rows = _settings_row_values(drivers_sheet)
        if not rows:
            st.info("No drivers are available in the drivers sheet.")
        else:
            options = {
                f"{r[0] if len(r) > 0 else 'Driver'}  •  {r[3] if len(r) > 3 else ''}": i + 2
                for i, r in enumerate(rows)
            }
            selected_label = st.selectbox("Select Driver", list(options.keys()), key="settings_driver_select")
            sheet_row = options[selected_label]
            row = rows[sheet_row - 2]
            row = row + [""] * max(0, 4 - len(row))

            with st.form("settings_driver_form"):
                c1, c2 = st.columns(2)
                driver_name = c1.text_input("Driver Name", value=_setting_text(row[0]))
                vehicle_no = c2.text_input("Assigned Vehicle", value=_setting_text(row[3]))
                username = c1.text_input("Username (legacy field)", value=_setting_text(row[1]))
                password = c2.text_input("Password (legacy field)", value=_setting_text(row[2]))
                save_driver = st.form_submit_button("Save Driver Settings", use_container_width=True)

            if save_driver:
                if not driver_name.strip():
                    st.error("Driver name is required.")
                elif not vehicle_no.strip():
                    st.error("Assigned vehicle is required.")
                else:
                    drivers_sheet.update(
                        f"A{sheet_row}:D{sheet_row}",
                        [[driver_name.strip(), username.strip(), password.strip(), vehicle_no.strip()]],
                    )
                    st.success("Driver settings updated successfully.")
                    st.rerun()

        st.info("Username and password are retained only because they already exist in your sheet. The current system uses a single administrator login.")

    # ---------------------------------------------------------------
    # VEHICLE MASTER
    # ---------------------------------------------------------------
    with tab2:
        st.markdown("### Vehicle Master Settings")
        headers, rows = _settings_row_values(vehicle_master_sheet)
        if not rows:
            st.info("No vehicles are available in vehicle_master.")
        else:
            options = {
                f"{r[0] if len(r) > 0 else 'Vehicle'}": i + 2
                for i, r in enumerate(rows)
            }
            selected_vehicle_label = st.selectbox("Select Vehicle", list(options.keys()), key="settings_vehicle_select")
            sheet_row = options[selected_vehicle_label]
            row = rows[sheet_row - 2]
            row = row + [""] * max(0, 12 - len(row))

            with st.form("settings_vehicle_form"):
                c1, c2 = st.columns(2)
                vehicle_no = c1.text_input("Vehicle Number", value=_setting_text(row[0]))
                license_date = c2.text_input("License Renewal Date", value=_setting_text(row[1]), help="Recommended format: YYYY-MM-DD")
                insurance_date = c1.text_input("Insurance Renewal Date", value=_setting_text(row[2]), help="Recommended format: YYYY-MM-DD")
                lease_installment = c2.number_input("Lease Installment Amount (Rs.)", min_value=0.0, value=_setting_number(row[3]), step=1000.0)
                lease_total = c1.number_input("Total Lease Installments", min_value=0.0, value=_setting_number(row[4]), step=1.0)
                lease_start = c2.text_input("Lease Start Date", value=_setting_text(row[5]), help="Recommended format: YYYY-MM-DD")
                alignment_interval = c1.number_input("Wheel Alignment Interval (KM)", min_value=0.0, value=_setting_number(row[6]), step=500.0)
                air_filter_interval = c2.number_input("Air Filter Interval (KM)", min_value=0.0, value=_setting_number(row[7]), step=1000.0)
                purchase_date = c1.text_input("Purchase Date", value=_setting_text(row[8]), help="Recommended format: YYYY-MM-DD")
                purchase_cost = c2.number_input("Purchase Cost (Rs.)", min_value=0.0, value=_setting_number(row[9]), step=10000.0)
                useful_years = c1.number_input("Useful Life (Years)", min_value=0.0, value=_setting_number(row[10]), step=1.0)
                cost_per_km = c2.number_input("Running Cost per KM (Rs.)", min_value=0.0, value=_setting_number(row[11]), step=1.0)
                save_vehicle = st.form_submit_button("Save Vehicle Settings", use_container_width=True)

            if save_vehicle:
                if not vehicle_no.strip():
                    st.error("Vehicle number is required.")
                else:
                    vehicle_master_sheet.update(
                        f"A{sheet_row}:L{sheet_row}",
                        [[
                            vehicle_no.strip(), license_date.strip(), insurance_date.strip(),
                            lease_installment, lease_total, lease_start.strip(),
                            alignment_interval, air_filter_interval, purchase_date.strip(),
                            purchase_cost, useful_years, cost_per_km,
                        ]],
                    )
                    st.success("Vehicle master settings updated successfully.")
                    st.rerun()

        st.warning("Changes to cost per KM, service intervals, lease details, purchase cost or useful life will affect future calculations/reports that use those master values.")

    # ---------------------------------------------------------------
    # MONTHLY ELECTRICITY
    # ---------------------------------------------------------------
    with tab3:
        st.markdown("### Monthly Electricity Settings")
        headers, rows = _settings_row_values(monthly_cash_flow_sheet)
        if not rows:
            st.info("No electricity bills have been recorded yet. Add the first one from Monthly Cash Flow.")
        else:
            options = {
                f"{r[0] if len(r) > 0 else 'Month'}": i + 2
                for i, r in enumerate(rows)
            }
            selected_month_label = st.selectbox("Select Month", list(options.keys()), key="settings_electricity_month")
            sheet_row = options[selected_month_label]
            row = rows[sheet_row - 2]
            row = row + [""] * max(0, 4 - len(row))

            with st.form("settings_electricity_form"):
                month = st.text_input("Month", value=_setting_text(row[0]), help="Use YYYY-MM format")
                bill = st.number_input("Electricity Bill (Rs.)", min_value=0.0, value=_setting_number(row[1]), step=100.0)
                note = st.text_input("Note", value=_setting_text(row[3]))
                save_electricity = st.form_submit_button("Save Electricity Settings", use_container_width=True)

            if save_electricity:
                now_txt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                monthly_cash_flow_sheet.update(
                    f"A{sheet_row}:D{sheet_row}",
                    [[month.strip(), bill, now_txt, note.strip()]],
                )
                st.success("Electricity settings updated successfully.")
                st.rerun()

# -------------------------------------------------------------------
# MAIN APP — SINGLE ADMIN ACCOUNT
# -------------------------------------------------------------------
if "is_admin_logged" not in st.session_state:
    st.session_state.is_admin_logged = False

if not st.session_state.is_admin_logged:
    left, center, right = st.columns([1, 1.05, 1])
    with center:
        with st.container(border=True):
            if not render_centered_logo(140):
                st.markdown('<div class="login-logo">CT</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-name" style="text-align:center">CEEKAY Tours</div><div class="login-sub" style="text-align:center">Business Management Console<br>Administrator Access</div>', unsafe_allow_html=True)
            username=st.text_input("Username",placeholder="Enter username",key="admin_login_username")
            password=st.text_input("Password",type="password",placeholder="Enter password",key="admin_login_password")
            if st.button("Sign in",use_container_width=True,key="admin_login_button"):
                if username==ADMIN_USERNAME and password==ADMIN_PASSWORD:
                    st.session_state.is_admin_logged=True
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")
            st.markdown('<div class="ck-login-note">Single administrator account • Existing CEEKAY Tours database</div>',unsafe_allow_html=True)
else:
    page=sidebar_menu()
    meta={
      "Dashboard":("Business Dashboard","Revenue, profitability, mileage and fleet health at a glance."),
      "Daily Entry":("Daily Operations","Record driver and trip income directly from the admin workspace."),
      "Profit Reports":("Profit Reports","Review daily, date-range and monthly business performance."),
      "Monthly Cash Flow":("Monthly Cash Flow","Track monthly cash available after driver payments and electricity."),
      "Vehicle Entry":("Vehicle Costs & Service","Maintain vehicle master data, running costs and service expenses."),
      "Vehicle Report":("Vehicle Report","Review vehicle-level income, expenses, mileage and profitability."),
      "Settings":("Settings","Update master values and configuration stored in the CEEKAY Tours Google Sheet.")
    }
    if page!="Logout":
        title,sub=meta[page]
        st.markdown(f'<div class="ck-page-kicker">CEEKAY TOURS • MANAGEMENT</div><div class="finance-title">{title}</div><div class="finance-subtitle">{sub}</div>',unsafe_allow_html=True)
    if page=="Dashboard": page_admin_dashboard()
    elif page=="Daily Entry": page_admin_daily_entry()
    elif page=="Profit Reports": page_profit_reports()
    elif page=="Monthly Cash Flow": page_monthly_cash_flow()
    elif page=="Vehicle Entry": page_vehicle_entry()
    elif page=="Vehicle Report": page_vehicle_report()
    elif page=="Settings": page_settings()
    elif page=="Logout":
        st.session_state.clear()
        st.rerun()
