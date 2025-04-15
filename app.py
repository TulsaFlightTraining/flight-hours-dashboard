import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import fitz  # PyMuPDF
from matplotlib.dates import date2num
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import matplotlib.dates as mdates
import re
import streamlit as st

st.set_page_config(layout="wide")
st.title("Monthly Hobbs Report Generator")

# --- FUNCTION TO PARSE PDF ---
def parse_flight_circle_pdf_all_pages(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    all_lines = []
    for i in range(doc.page_count):
        all_lines.extend(doc[i].get_text().splitlines())

    parsed_entries = []
    i = 0
    while i < len(all_lines) - 7:
        try:
            if re.match(r"\d{2}/\d{2}/\d{4}", all_lines[i].strip()):
                date = pd.to_datetime(all_lines[i].strip())
                pilot = all_lines[i + 1].strip()
                type_line = all_lines[i + 2].strip()
                hobbs_delta = float(all_lines[i + 4].replace(',', '').replace('+', '').strip())
                hobbs_total = float(all_lines[i + 5].replace(',', '').strip())
                tach_delta = float(all_lines[i + 6].replace(',', '').replace('+', '').strip())
                tach_total = float(all_lines[i + 7].replace(',', '').strip())
                type_clean = "Rental" if "Rental" in type_line else "Maintenance" if "Maintenance" in type_line else "Other"
                parsed_entries.append([
                    date, pilot if pilot else "Maintenance", type_clean,
                    hobbs_delta, hobbs_total, tach_delta, tach_total
                ])
                i += 8
            else:
                i += 1
        except Exception:
            i += 1

    return pd.DataFrame(parsed_entries, columns=[
        "Date", "Pilot Name", "Type", "Hobbs +/-", "Hobbs Total", "Tach +/-", "Tach Total"
    ])

# --- STREAMLIT FILE UPLOAD ---
st.sidebar.header("Upload PDFs by Aircraft")
tail_numbers = ["N7219S", "N8136F", "N3072S", "N1369F", "N5762R", "N5076N", "N8351L"]

uploaded_files = {}
for tail in tail_numbers:
    uploaded_files[tail] = st.sidebar.file_uploader(f"Upload PDF for {tail}", type="pdf", key=tail)

# --- PROCESS & PLOT ---
all_monthly_data = []
for tail, pdf in uploaded_files.items():
    if pdf is not None:
        df = parse_flight_circle_pdf_all_pages(pdf)
        df["Month"] = df["Date"].dt.to_period("M")
        monthly = df.groupby("Month")["Hobbs +/-"].sum().reset_index()
        monthly["Month"] = monthly["Month"].dt.to_timestamp()
        monthly["Tail Number"] = tail
        all_monthly_data.append(monthly)

if all_monthly_data:
    df_all = pd.concat(all_monthly_data)
    df_all["Month_Num"] = date2num(df_all["Month"])
    full_months = pd.date_range(start=df_all["Month"].min(), end=df_all["Month"].max(), freq="MS")

    st.subheader("Monthly Hobbs Charts with Trend Lines")

    with PdfPages("Fleet_Hobbs_Monthly_Report.pdf") as pdf:
        for tail in df_all["Tail Number"].unique():
            df_tail = df_all[df_all["Tail Number"] == tail].set_index("Month").reindex(full_months, fill_value=0).reset_index().rename(columns={"index": "Month"})
            df_tail["Month_Num"] = date2num(df_tail["Month"])

            # Streamlit display
            st.markdown(f"### {tail}")
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=df_tail, x="Month", y="Hobbs +/-", marker="o", ax=ax, label=tail)
            sns.regplot(x="Month_Num", y="Hobbs +/-", data=df_tail, scatter=False, ci=None, color="red", ax=ax, label="Trend")
            ax.set_title(f"Monthly Hobbs Usage – {tail}")
            ax.set_xlabel("Month")
            ax.set_ylabel("Hobbs +/-")
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
            ax.tick_params(axis='x', rotation=45)
            ax.legend()
            ax.yaxis.grid(True, linestyle='--', alpha=0.7)
            ax.xaxis.grid(True, linestyle='--', alpha=0.5)
            st.pyplot(fig)
            pdf.savefig(fig)
            plt.close()

        # Fleet-wide summary
        fleet_summary = df_all.groupby("Month")["Hobbs +/-"].sum().reindex(full_months, fill_value=0).reset_index()
        fleet_summary.rename(columns={"index": "Month"}, inplace=True)
        fleet_summary["Month_Num"] = date2num(fleet_summary["Month"])

        st.markdown("### Combined Fleet Total")
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(data=fleet_summary, x="Month", y="Hobbs +/-", marker="o", ax=ax, label="Fleet Total")
        sns.regplot(x="Month_Num", y="Hobbs +/-", data=fleet_summary, scatter=False, ci=None, color="red", ax=ax, label="Trend")
        ax.set_title("Combined Monthly Hobbs Usage (Fleet)")
        ax.set_xlabel("Month")
        ax.set_ylabel("Total Hobbs +/- Hours")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        ax.tick_params(axis='x', rotation=45)
        ax.legend()
        st.pyplot(fig)
        pdf.savefig(fig)
        plt.close()

    st.success("Fleet_Hobbs_Monthly_Report.pdf generated successfully.")
