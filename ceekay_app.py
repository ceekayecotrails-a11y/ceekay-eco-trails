import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
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

# Google Drive client
drive_service = build('drive', 'v3', credentials=creds)

# Your screenshot folder ID
SCREENSHOT_FOLDER_ID = "1iuoSZvJXOWstZS4q_Wz4KCjoZbbXqDYB"

file = client.open("CEEKAY_Driver_Reports")
drivers_sheet = file.worksheet("drivers")
daily_sheet = file.worksheet("daily_reports")

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
# UPLOAD FILE TO GOOGLE DRIVE
# -------------------------------------------------------------------
def upload_to_drive(file, filename):
    from googleapiclient.http import MediaIoBaseUpload

    FOLDER_ID = "1IJWmZ4mhIAo6r83S9nHwjYAe9FR1XpP3"

    file_metadata = {
        "name": filename,
        "parents": [FOLDER_ID],
    }

    media = MediaIoBaseUpload(
        file,
        mimetype=file.type,
        resumable=True
    )

    drive = build("drive", "v3", credentials=creds)

    uploaded_file = (
        drive.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )

    file_id = uploaded_file.get("id")

    drive.permissions().create(
        fileId=file_id,
        body={"role": "reader", "type": "anyone"}
    ).execute()

    return f"https://drive.google.com/uc?id={file_id}"

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
        st.image("logo.png", use_column_width=True)
        st.markdown("---")

    icons = {
        "Home": "🏠",
        "Daily Report": "📝",
        "Earnings Report": "📊",
        "Dashboard": "📊",
        "Profit Reports": "📈",
        "Submissions": "📁",
        "Logout": "🚪"
    }

    # DRIVER MENU
    if user_type == "driver":
        return st.sidebar.radio(
            "",
            ["Home", "Daily Report", "Earnings Report", "Logout"],
            format_func=lambda x: f"{icons[x]} {x}"
        )

    # ADMIN MENU
    if user_type == "admin":
        return st.sidebar.radio(
            "",
            ["Dashboard", "Profit Reports", "Submissions", "Logout"],
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
        "screenshot": None
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

        st.session_state.screenshot = st.file_uploader(
            "Upload Earnings Screenshot (PNG/JPG) *",
            type=["png", "jpg", "jpeg"]
        )

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
            salary = fare * 0.30
            total_salary = salary + tip + toll
            to_ceekay = cash - total_salary

            st.info(f"**Daily Mileage:** {daily} km")
            st.warning(f"**Loss Mileage:** {loss} km")
            st.success(f"**Driver Salary (30%): Rs. {salary:,.2f}**")
            st.success(f"**Total Driver Salary: Rs. {total_salary:,.2f}**")
            st.info(f"**Amount to Hand Over: Rs. {to_ceekay:,.2f}**")

    if st.session_state.screenshot:
        st.image(
            st.session_state.screenshot,
            caption="Uploaded Screenshot",
            use_column_width=True
        )

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
        if not st.session_state.screenshot:
            st.error("Screenshot is required.")
            return

        daily = st.session_state.end - st.session_state.start
        loss = daily - st.session_state.uber
        salary = st.session_state.fare * 0.30
        total_salary = salary + (st.session_state.tip or 0) + (st.session_state.toll or 0)
        to_ceekay = st.session_state.cash - total_salary

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


# -------------------------------------------------------------------
# ADMIN DASHBOARD PAGE
# -------------------------------------------------------------------
def page_admin_dashboard():

    st.markdown("<h2>📊 Admin Dashboard</h2>", unsafe_allow_html=True)

    df = pd.DataFrame(daily_sheet.get_all_records())
    df = df[df["status"] == "Correct"]


    if df.empty:
        st.warning("No data available.")
        return

    # Convert numeric values
    numeric_cols = [
        "fare", "driver_salary", "toll_fee", "other_expenses",
        "daily_mileage", "uber_hire_mileage", "loss_mileage",
        "platform_fee", "amount_to_ceekay", "bank_deposit", "cash_collected"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Convert date
    df["date"] = pd.to_datetime(df["date"])

    # ---------------------- ADVANCED TREND CHART ----------------------
    st.subheader("📊 Trend Analytics")

    col1, col2 = st.columns(2)
    start_date = col1.date_input("From Date", df["date"].min())
    end_date = col2.date_input("To Date", df["date"].max())

    mask = (df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))
    filtered = df[mask]

    st.caption(f"Showing data from {start_date} to {end_date}")


    trend_options = {
        "Daily Fare": "fare",
        "Driver Salary": "driver_salary",
        "Total Mileage": "daily_mileage",
        "Uber Mileage": "uber_hire_mileage",
        "Loss Mileage": "loss_mileage",
        "Cash Collected": "cash_collected",
        "Amount to CEEKAY": "amount_to_ceekay"
    }

    selected_trend = st.selectbox("Select Trend to View:", list(trend_options.keys()))
    y_column = trend_options[selected_trend]

    daily_data = filtered.groupby(filtered["date"].dt.date)[y_column].sum().reset_index()
    daily_data.columns = ["date", "value"]

    fig = px.line(
        daily_data,
        x="date",
        y="value",
        title=f"{selected_trend} Trend",
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")
    # --------------------------------------------------------------

    # ---------------------- ADMIN SUMMARY SECTION ----------------------
    total_fare = filtered["fare"].sum()
    total_salary = filtered["driver_salary"].sum()
    total_daily_mileage = filtered["daily_mileage"].sum()
    total_uber_mileage = filtered["uber_hire_mileage"].sum()
    total_loss_mileage = filtered["loss_mileage"].sum()

    total_platform_fee = filtered["platform_fee"].sum()
    total_vehicle_cost = total_daily_mileage * 15.37
    total_cost = total_salary + total_vehicle_cost + total_platform_fee

    net_profit = total_fare - total_cost

    cash_flow = (
        filtered["amount_to_ceekay"].sum()
        + filtered["bank_deposit"].sum()
        - filtered["platform_fee"].sum()
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Fare", f"Rs. {total_fare:,.2f}")
    col2.metric("Total Cost", f"Rs. {total_cost:,.2f}")
    col3.metric("Net Earnings", f"Rs. {net_profit:,.2f}")

    col4, col5, col6 = st.columns(3)
    col4.metric("Total Mileage", f"{total_daily_mileage} km")
    col5.metric("Uber Mileage", f"{total_uber_mileage} km")
    col6.metric("Loss Mileage", f"{total_loss_mileage} km")

    st.metric("Cash Flow", f"Rs. {cash_flow:,.2f}")


# -------------------------------------------------------------------
# ADMIN DAILY PROFIT REPORT
# -------------------------------------------------------------------
def page_admin_daily_profit():

    st.markdown("<h2>💰 Daily Profit Report</h2>", unsafe_allow_html=True)

    df = pd.DataFrame(daily_sheet.get_all_records())
    page_admin_daily_profit

    numeric_cols = [
        "fare", "driver_salary", "toll_fee", "other_expenses",
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
    total_salary = df_day["driver_salary"].sum()
    platform_fee = df_day["platform_fee"].sum()
    total_daily_mileage = df_day["daily_mileage"].sum()

    vehicle_cost = total_daily_mileage * 15.37
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
    page_admin_daily_profit

    numeric_cols = [
        "fare", "driver_salary", "toll_fee", "other_expenses",
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
    total_salary = df_range["driver_salary"].sum()
    platform_fee = df_range["platform_fee"].sum()
    total_daily_mileage = df_range["daily_mileage"].sum()

    vehicle_cost = total_daily_mileage * 15.37
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
    page_admin_daily_profit

    numeric_cols = [
        "fare", "driver_salary", "toll_fee", "other_expenses",
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
    total_salary = df_month["driver_salary"].sum()
    platform_fee = df_month["platform_fee"].sum()
    total_daily_mileage = df_month["daily_mileage"].sum()

    vehicle_cost = total_daily_mileage * 15.37
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

# -------------------------------------------------------------------
# SAFE NUMBER CONVERTER
# -------------------------------------------------------------------
def num(v):
    try:
        return float(v)
    except:
        return 0.0

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

    st.write("### Screenshot")
    ss = row.get("screenshot_url", "")
    if ss:
        st.image(ss)
    else:
        st.info("No screenshot uploaded")

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

        if page == "Home":
            st.success(f"Welcome {driver['driver_name']}!")

        elif page == "Daily Report":
            st.error("You cannot submit a new report until admin confirms your last report.")

        # elif page == "My Summary":
#     page_driver_summary(driver)


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

        if page == "Home":
            st.success(f"Welcome {driver['driver_name']}!")

        elif page == "Daily Report":
            page_driver_form(driver)

        elif page == "My Summary":
            page_driver_summary(driver)

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

    elif page == "Submissions":
        page_admin_submissions()

    elif page == "Logout":
        st.session_state.page = None
        st.session_state.is_admin_logged = False
        st.rerun()















































