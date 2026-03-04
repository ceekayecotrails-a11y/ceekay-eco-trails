import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date
import io
import matplotlib.pyplot as plt

# -------------------------------------------------------------------
# DARK MODE + PAGE CONFIG
# -------------------------------------------------------------------
st.set_page_config(
    page_title="CEEKAY Eco Trails",
    page_icon="",
    layout="wide"
)

st.markdown(
    """
    <style>
    /* Perfect centering for Streamlit images (desktop + mobile) */
    .center-logo [data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)



# -------------------------------------------------------------------
# CUSTOM CSS (Dark Theme + Icon Sidebar)
# -------------------------------------------------------------------
dark_css = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

[data-testid="stSidebar"] {
    background-color: ##0f2f1f;
}

.sidebar-icons {
    font-size: 25px;
    color: #57ff57;
    padding: 15px;
    cursor: pointer;
}
.sidebar-icons:hover {
    color: #aaffaa;
}

.title-text {
    font-size: 32px;
    color: #00ff88;
    font-weight: bold;
}

.subheader-text {
    font-size: 22px;
    color: #66ffcc;
}

.card {
    padding: 20px;
    border-radius: 12px;
    background-color: #1b1b1b;
    color: white;
    margin-bottom: 15px;
    border: 1px solid #333;
}

.stButton>button {
    background-color: #00c26f;
    color: white;
    border-radius: 8px;
    border: none;
}
.stButton>button:hover {
    background-color: #00e68a;
}
</style>
"""
st.markdown(dark_css, unsafe_allow_html=True)

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
def sidebar_menu(user_type):

    with st.sidebar:
        st.markdown("<div class='center-logo'>", unsafe_allow_html=True)
        st.image("logo.png", width=150)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")

    icons = {
        "Home": "🏠",
        "Daily Report": "📝",
        "Earnings Report": "📊",
        "Dashboard": "📊",
        "Profit Reports": "📈",
        "Submissions": "📁",
        "Vehicle Entry": "🛠",
        "Vehicle Report": "🚗",
        "Logout": "🚪"
    }

    # DRIVER MENU
    if user_type == "driver":
        return st.sidebar.radio(
            "",
            ["Dashboard", "Daily Report", "Earnings Report", "Logout"],
            format_func=lambda x: f"{icons[x]} {x}"
        )

    # ADMIN MENU
    if user_type == "admin":
        return st.sidebar.radio(
            "",
            ["Dashboard", "Profit Reports", "Vehicle Entry", "Vehicle Report", "Submissions", "Logout"],
            format_func=lambda x: f"{icons[x]} {x}"
        )

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

    st.markdown("<h2>📊 CEEKAY Executive Dashboard</h2>", unsafe_allow_html=True)

    df = pd.DataFrame(daily_sheet.get_all_records())
    df = df[df["status"] == "Correct"]

    if df.empty:
        st.warning("No data available.")
        return

    # Convert numeric columns safely
    numeric_cols = [
        "fare", "driver_salary", "platform_fee",
        "toll_fee", "tip",
        "daily_mileage", "uber_hire_mileage",
        "loss_mileage", "amount_to_ceekay",
        "bank_deposit"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["date"] = pd.to_datetime(df["date"])

    # Date Filter
    col1, col2 = st.columns(2)
    start_date = col1.date_input("From Date", df["date"].min())
    end_date = col2.date_input("To Date", df["date"].max())

    df = df[
        (df["date"] >= pd.to_datetime(start_date)) &
        (df["date"] <= pd.to_datetime(end_date))
    ]

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview",
        "🚗 Vehicle Performance",
        "💰 Expense Insights",
        "🚗 Vehicle Details"
    ])

    # =====================================================
    # TAB 1 — BUSINESS OVERVIEW
    # =====================================================
    with tab1:
     

        # =====================================================
        # SERVICE ALERT SECTION
        # =====================================================
    
        st.markdown("## 🚨 Service Alerts")
        
        vehicle_data = get_vehicle_service_data()
        
        if vehicle_data.empty:
            st.info("No vehicle data available.")
        else:
        
            alerts = []
        
            for _, row in vehicle_data.iterrows():
        
                current = row["current_mileage"]
        
                if row["alignment_interval_km"] > 0:
        
                    if current >= row["next_alignment"]:
                        alerts.append(f"🔴 {row['vehicle_no']} - Wheel Alignment OVERDUE")
        
                    elif current >= row["next_alignment"] - 500:
                        alerts.append(f"🟡 {row['vehicle_no']} - Wheel Alignment Due Soon")
        
                if row["air_filter_interval_km"] > 0:
        
                    if current >= row["next_air_filter"]:
                        alerts.append(f"🔴 {row['vehicle_no']} - Air Filter OVERDUE")
        
                    elif current >= row["next_air_filter"] - 1000:
                        alerts.append(f"🟡 {row['vehicle_no']} - Air Filter Due Soon")
        
            if alerts:
                for alert in alerts:
                    st.warning(alert)
            else:
                st.success("All vehicles are service-ready ✅")
        
        st.markdown("---")
    
        total_revenue = df["fare"].sum()

        total_revenue = df["fare"].sum()
        total_salary = (
            df["driver_salary"].sum()
            + df["tip"].sum()
        )
        total_platform = df["platform_fee"].sum()

        # Load vehicle cost per km
        df["vehicle_running_cost"] = pd.to_numeric(
            df.get("vehicle_running_cost", 0),
            errors="coerce"
        ).fillna(0)

        running_cost = df["vehicle_running_cost"].sum()
        total_mileage = df["daily_mileage"].sum()
        total_cost = total_salary + total_platform + running_cost
        net_profit = total_revenue - total_cost

        if total_mileage > 0:
            profit_per_km = net_profit / total_mileage
        else:
            profit_per_km = 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Revenue", f"Rs. {total_revenue:,.0f}")
        col2.metric("Total Cost", f"Rs. {total_cost:,.0f}")
        col3.metric("Net Profit", f"Rs. {net_profit:,.0f}")
        col4.metric("Profit per KM", f"Rs. {profit_per_km:,.2f}")

        st.markdown("---")

        daily_trend = df.groupby(df["date"].dt.date)["fare"].sum().reset_index()
        fig = px.line(daily_trend, x="date", y="fare", title="Revenue Trend", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    # =====================================================
    # TAB 2 — VEHICLE PERFORMANCE
    # =====================================================
    with tab2:

        df["vehicle_running_cost"] = pd.to_numeric(
            df.get("vehicle_running_cost", 0),
            errors="coerce"
        ).fillna(0)
    
        vehicle_summary = df.groupby("vehicle_no").agg({
            "fare": "sum",
            "driver_salary": "sum",
            "toll_fee": "sum",
            "tip": "sum",
            "platform_fee": "sum",
            "daily_mileage": "sum",
            "vehicle_running_cost": "sum"
        }).reset_index()
    
        vehicle_summary["real_driver_cost"] = (
            vehicle_summary["driver_salary"]
            + vehicle_summary["tip"]
        )
    
        vehicle_summary["total_cost"] = (
            vehicle_summary["real_driver_cost"]
            + vehicle_summary["platform_fee"]
            + vehicle_summary["vehicle_running_cost"]
        )
    
        vehicle_summary["net_profit"] = (
            vehicle_summary["fare"]
            - vehicle_summary["total_cost"]
        )
    
        st.dataframe(vehicle_summary)
    # =====================================================
    # TAB 3 — EXPENSE INSIGHTS
    # =====================================================
    with tab3:

        total_salary = (
            df["driver_salary"].sum()
            + df["tip"].sum()
        )
        total_platform = df["platform_fee"].sum()
        total_mileage = df["daily_mileage"].sum()
        # Load cost per km
        df["vehicle_running_cost"] = pd.to_numeric(
            df.get("vehicle_running_cost", 0),
            errors="coerce"
        ).fillna(0)

        running_cost = df["vehicle_running_cost"].sum()

        expense_data = pd.DataFrame({
            "Category": ["Driver Salary", "Platform Fee", "Running Cost"],
            "Amount": [total_salary, total_platform, running_cost]
        })

        fig3 = px.pie(
            expense_data,
            names="Category",
            values="Amount",
            title="Expense Breakdown"
        )

        st.plotly_chart(fig3, use_container_width=True)

    # =====================================================
    # TAB 4 — VEHICLE DETAILS
    # =====================================================
    with tab4:

        st.subheader("🚗 Fleet Maintenance & Leasing Overview")

        vehicle_data = get_vehicle_service_data()

        if vehicle_data.empty:
            st.warning("No vehicle data available.")
            st.stop()

        today = datetime.today().date()
        cols = st.columns(2)

        for i, row in vehicle_data.iterrows():

            col = cols[i % 2]

            with col:

                current_mileage = row["current_mileage"]

                if current_mileage >= row["next_alignment"]:
                    alignment_status = "🔴 OVERDUE"
                elif current_mileage >= row["next_alignment"] - 500:
                    alignment_status = "🟡 Due Soon"
                else:
                    alignment_status = "🟢 OK"

                if current_mileage >= row["next_air_filter"]:
                    air_status = "🔴 OVERDUE"
                elif current_mileage >= row["next_air_filter"] - 1000:
                    air_status = "🟡 Due Soon"
                else:
                    air_status = "🟢 OK"

                lease_start = pd.to_datetime(
                    row.get("lease_start_date", today)
                ).date()

                total_installments = num(row.get("lease_total_installments", 0))
                installment_amount = num(row.get("lease_installment_amount", 0))

                months_passed = (today.year - lease_start.year) * 12 + (
                    today.month - lease_start.month
                )

                remaining_months = max(0, total_installments - months_passed)
                remaining_balance = remaining_months * installment_amount

                license_date = pd.to_datetime(row["license_renewal_date"]).date()
                insurance_date = pd.to_datetime(row["insurance_renewal_date"]).date()

                license_days = (license_date - today).days
                insurance_days = (insurance_date - today).days

                st.markdown(f"""
                ### 🚗 {row['vehicle_no']}

                📍 Current Mileage: {int(current_mileage):,} km  

                🛞 Next Wheel Alignment: {int(row['next_alignment']):,} km  
                Status: {alignment_status}  

                🌬 Next Air Filter: {int(row['next_air_filter']):,} km  
                Status: {air_status}  

                ---

                🗓 License Renewal: {license_date}  
                ⏳ Days Remaining: {license_days}

                🛡 Insurance Renewal: {insurance_date}  
                ⏳ Days Remaining: {insurance_days}

                ---

                💳 Lease Installment: Rs. {installment_amount:,.0f}  
                📦 Remaining Months: {remaining_months}  
                💰 Remaining Balance: Rs. {remaining_balance:,.0f}

                ---
                """)


# -------------------------------------------------------------------
# ADMIN DAILY PROFIT REPORT
# -------------------------------------------------------------------
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
        df_day["driver_salary"].sum()
        + df_day["tip"].sum()
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

    st.markdown("<h2>📈 Profit Reports</h2>", unsafe_allow_html=True)

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

    st.markdown("<h2>🚗 Vehicle Financial Report</h2>", unsafe_allow_html=True)

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

    st.markdown("<h2>🛠 Vehicle Management</h2>", unsafe_allow_html=True)

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
# MAIN APP
# -------------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = None


menu = st.sidebar.selectbox("Login", ["Driver", "Admin"])

# DRIVER LOGIN
if menu == "Driver":

    username = st.text_input("Driver Username")
    password = st.text_input("Password", type="password")

    if st.button("Login as Driver"):
        d = driver_auth(username, password)
        if d:
            status = check_driver_status(d["driver_name"])
            st.session_state["driver_status"] = status
            st.session_state["page"] = "driver"
            st.session_state["driver"] = d
            st.rerun()
        else:
            st.error("Invalid Username or Password!")


# DRIVER PAGES
if st.session_state.get("page") == "driver":

    driver = st.session_state["driver"]
    status = st.session_state.get("driver_status", "No Reports")

    if status == "Incorrect":
        st.error("There is an issue with your previous payment. Please contact CEEKAY Eco Trails soon !!!")
        st.stop()

    if status == "Pending":
        st.warning("Your last report is still under review.")
        st.info("You can view reports, but cannot submit a new one until it's confirmed.")

        page = sidebar_menu("driver")

        if page == "Dashboard":
            page_driver_dashboard(driver)

        elif page == "Daily Report":
            st.error("You cannot submit a new report until admin confirms your last report.")




        elif page == "Earnings Report":
            page_earnings_report("driver", driver)

        elif page == "Logout":
            st.session_state.page = None
            st.session_state.driver = None
            st.session_state.driver_status = None
            st.rerun()

    if status == "Correct" or status == "No Reports":
    
        st.success("Have a good day. The vehicle is ready for today")
    
        page = sidebar_menu("driver")
    
        if page == "Dashboard":
            page_driver_dashboard(driver)
    
        elif page == "Daily Report":
            page_driver_form(driver)
    
        elif page == "Earnings Report":
            page_earnings_report("driver", driver)
    
        elif page == "Logout":
            st.session_state.page = None
            st.session_state.driver = None
            st.session_state.driver_status = None
            st.rerun()
       

# ADMIN LOGIN
if menu == "Admin":

    pw = st.text_input("Admin Password", type="password")

    if st.button("Login as Admin"):
        if pw == ADMIN_PASSWORD:
            st.session_state["page"] = "admin"
            st.session_state["is_admin_logged"] = True
            st.rerun()
        else:
            st.error("Incorrect Password!")

# ADMIN PAGES
if st.session_state.get("page") == "admin":

    page = sidebar_menu("admin")

    if page == "Dashboard":
        page_admin_dashboard()

    elif page == "Profit Reports":
        page_profit_reports()

    elif page == "Vehicle Entry":
        page_vehicle_entry()

    elif page == "Vehicle Report":
        page_vehicle_report()

    elif page == "Submissions":
        page_admin_submissions()

    elif page == "Logout":
        st.session_state.page = None
        st.session_state.is_admin_logged = False
        st.rerun()
