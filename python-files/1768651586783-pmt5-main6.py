import streamlit as st
import pandas as pd
import numpy as np

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Levis Payment", layout="wide")

# =========================
# TITLE
# =========================
st.markdown(
    "<h1 style='text-align:center;color:red;font-weight:bold;'>Levis Payment Working</h1>",
    unsafe_allow_html=True
)

# =========================
# FILE UPLOAD
# =========================
uploaded_file = st.file_uploader("Upload Levis Excel File", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    # =========================
    # FORCE newdate TO DATETIME
    # =========================
    date_col = "newdate"
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # =========================
    # SIDEBAR FILTERS (AUTO)
    # =========================
    st.sidebar.header("Filters")

    party_list = sorted(df["TERTIARYNAMEfromDSR"].dropna().unique())
    selected_party = st.sidebar.selectbox(
        "Select Party",
        ["All"] + list(party_list)
    )

    st.sidebar.markdown("### Enter Date Manually (DD-MM-YYYY)")
    from_date_str = st.sidebar.text_input("From Date", "")
    to_date_str = st.sidebar.text_input("To Date", "")

    view_summary = st.checkbox("Show Summary", value=True)
    view_report = st.checkbox("Show Full Report", value=True)

    # =========================
    # PARSE MANUAL DATE
    # =========================
    from_date = to_date = None
    try:
        if from_date_str:
            from_date = pd.to_datetime(from_date_str, format="%d-%m-%Y")
        if to_date_str:
            to_date = pd.to_datetime(to_date_str, format="%d-%m-%Y")
    except Exception:
        st.sidebar.error("❌ Date format must be DD-MM-YYYY")

    # =========================
    # MASTER DATA
    # =========================
    margin_data = {
        "ONE STOP SHOP       . JALANDHAR": 25.04,
        "A One Clothing Jalandar": 25.04,
        "SHIV SHAKTI - BATALA": 22.00,
        "ACTIVE STORE - BATHINDA": 22.00,
        "AMU ENTERPRISES - ANANTNAG": 26.00,
        "ANAND EXCLUSIVE - FEROZPUR CITY": 25.04,
        "ANAND EXCLUSIVE LUXE - FEROZPUR CITY": 25.00,
        "Capital Garments-Muktsar": 22.15,
        "Capital-Nawashahar": 22.15,
        "Dhaliwal Sangrur": 24.00,
        "GURU JI AGENCY - AMRITSAR": 28.00,
        "Jahaan Enterprises - Jalandhar": 20.00,
        "Mom N Me": 28.00,
        "Obros Anantnag": 28.00,
        "Obros Baramulla": 28.00,
        "Obros Srinagar": 28.00,
        "ObrosNirman": 28.00,
        "Ram-garments-Jalandar": 25.04,
        "SAR RETAIL PVT LTD - GANGYAL": 22.00,
        "SAR RETAIL PVT LTD - MOHALI": 25.04,
        "SAR RETAIL PVT LTD - SANGRUR": 22.00,
        "SAR RETAIL PVT LTD - YAMUNANAGAR": 22.00,
        "SAR-RETAIL-PVT.-LTD.---JAMMU": 25.04,
        "VINTAGE FASHION - KHARAR": 20.00,
        "VINTAGE FASHION - ZIRAKPUR": 20.00
    }

    # =========================
    # CALCULATION FUNCTION
    # =========================
    def calculate(df):
        df = df.copy()

        df["Qty"] = pd.to_numeric(df["Qty"], errors="coerce").fillna(0)

        df["BASE MARGIN %"] = df["TERTIARYNAMEfromDSR"].map(margin_data)
        df["MRP VALUE"] = df["TotalMRP"]
        df["DISC AMT"] = df["TotalMRP"] - df["RealisedValue"]
        df.loc[df["DISC AMT"].abs() < 10, "DISC AMT"] = 0
        df["NET AMT"] = df["MRP VALUE"] - df["DISC AMT"]

        calc_cols = [
            "GST AMT","MARGIN AMT","FACTOR(MRP)",
            "AMOUNT(MRP-FACTOR)","INPUT","PAYABLE","billed amt"
        ]
        df[calc_cols] = np.nan

        old_mask = df["Stock remark"].str.upper() == "OLD"
        new_mask = df["Stock remark"].str.upper() == "NEW"
        valid_mask = old_mask | new_mask

        df.loc[valid_mask, "GST AMT"] = np.where(
            df.loc[valid_mask, "NET AMT"] >= 2625,
            df.loc[valid_mask, "NET AMT"] * 18 / 118,
            df.loc[valid_mask, "NET AMT"] * 5 / 105
        )

        df.loc[valid_mask, "MARGIN AMT"] = (
            df.loc[valid_mask, "NET AMT"] *
            df.loc[valid_mask, "BASE MARGIN %"] / 100
        )

        df.loc[old_mask, "FACTOR(MRP)"] = df.loc[old_mask, "BASE MARGIN %"] + 10.71
        df.loc[new_mask, "FACTOR(MRP)"] = df.loc[new_mask, "BASE MARGIN %"] + 15.25

        df.loc[old_mask, "AMOUNT(MRP-FACTOR)"] = (
            df.loc[old_mask, "old MRP sum"] *
            (1 - df.loc[old_mask, "FACTOR(MRP)"] / 100)
        )

        df.loc[new_mask, "AMOUNT(MRP-FACTOR)"] = (
            df.loc[new_mask, "MRP VALUE"] *
            (1 - df.loc[new_mask, "FACTOR(MRP)"] / 100)
        )

        df.loc[valid_mask, "INPUT"] = df["AMOUNT(MRP-FACTOR)"] * 0.05

        df.loc[valid_mask, "PAYABLE"] = (
            df["NET AMT"] - df["GST AMT"] -
            df["MARGIN AMT"] + df["INPUT"]
        )

        df.loc[valid_mask, "billed amt"] = (
            df["AMOUNT(MRP-FACTOR)"] + df["INPUT"]
        )

        return df.round(2)

    # =========================
    # AUTO FILTER APPLY
    # =========================
    df_f = df.copy()

    if selected_party != "All":
        df_f = df_f[df_f["TERTIARYNAMEfromDSR"] == selected_party]

    if from_date and to_date and date_col in df_f.columns:
        df_f = df_f[
            (df_f[date_col] >= from_date) &
            (df_f[date_col] <= to_date)
        ]

    final_df = calculate(df_f)

    # =========================
    # COMMON NUMERIC COLS
    # =========================
    num_cols = final_df.select_dtypes(include="number").columns

    # =========================
    # SUMMARY
    # =========================
    if view_summary:
        st.subheader("Summary Report")
        summary = final_df.groupby("Stock remark")[num_cols].sum().reset_index()
        st.dataframe(summary, use_container_width=True)

    # =========================
    # FULL REPORT
    # =========================
    if view_report:
        st.subheader("Full Report")
        st.dataframe(final_df, use_container_width=True)

        st.subheader("Grand Total")
        st.dataframe(
            final_df[num_cols].sum().to_frame().T,
            use_container_width=True
        )
