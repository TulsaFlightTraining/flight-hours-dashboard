import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import fitz  # PyMuPDF
import re

st.set_page_config(layout="wide")
st.title("Aircraft Monthly Hobbs Usage Tracker")

# Tail numbers to track
TAIL_NUMBERS = ["N7219S", "N8136F", "N3072S", "N1369F", "N5762R", "N5076N", "N8351L"]

def extract_flight_data(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    lines = []
    for page in doc:
        lines.extend(page.get_text().splitlines())

    records = []
    i = 0
    while i < len(lines) - 7:
        try:
            if re.match(r"\d{2}/\d{2}/\d{4}", lines[i].strip()):
                date = pd.to_datetime(lines[i].strip())
                pilot = lines[i + 1].strip()
                type_line = lines[i + 2].strip()
                hobbs_delta = float(lines[i + 3].replace(',', '').replace('+', '').strip())
                hobbs_total = float(lines[i + 4].replace(',', '').strip())
                tach_delta = float(lines[i + 5].replace(',', '').replace('+', '').strip())
                tach_total = float(lines[i + 6].replace(',', '').strip())
                type_clean = "Rental" if "Rental" in type_line else "Maintenance" if "Maintenance" in type_line else "Other"
                records.append([
                    date,
                    pilot if pilot else "Maintenance",
                    type_clean,
                    hobbs_delta,
                    hobbs_total,
                    tach_delta,
                    tach_total
                ])
                i += 7
            else:
                i += 1
        except:
            i += 1
    df = pd.DataFrame(records, columns=[
        "Date", "Pilot", "Type", "Hobbs +/-", "Hobbs Total", "Tach +/-", "Tach Total"
    ])
    return df

def plot_monthly_usage(df, tail_number):
    df["Month"] = df["Date"].dt.to_period("M")
    monthly = df.groupby("Month")["Hobbs +/-"].sum().reset_index()
    monthly["Month"] = monthly["Month"].dt.to_timestamp()
    monthly["Month_Num"] = range(len(monthly))

    plt.figure(figsize=(10, 5))
    sns.regplot(
        x="Month_Num",
        y="Hobbs +/-",
        data=monthly,
        marker='o',
        ci=None,
        line_kws={"color": "red"}
    )
    plt.xticks(ticks=monthly["Month_Num"], labels=monthly["Month"].dt.strftime('%b %Y'), rotation=45)
    plt.title(f"{tail_number} - Monthly Hobbs Usage with Trend Line")
    plt.xlabel("Month")
    plt.ylabel("Total Hobbs +/-")
    plt.grid(True)
    st.pyplot(plt.gcf())
    plt.close()

# Create upload sections for each aircraft
for tail in TAIL_NUMBERS:
    with st.expander(f"Upload Report for {tail}"):
        uploaded_file = st.file_uploader(f"Upload PDF for {tail}", type="pdf", key=tail)
        if uploaded_file:
            df = extract_flight_data(uploaded_file)
            if not df.empty:
                st.success(f"Parsed {len(df)} log entries for {tail}.")
                plot_monthly_usage(df, tail)
            else:
                st.warning("No valid entries found in this PDF.")
