# Fleet Hobbs Monthly Report

This app allows flight schools to upload PDF reports from Flight Circle for multiple aircraft, parse Hobbs data, and generate trend visualizations. It produces a downloadable PDF summary with monthly Hobbs usage graphs per aircraft and fleet-wide totals.

## Features
- Upload a Flight Circle PDF per aircraft tail number
- Automatically parse Hobbs usage
- Visualize Hobbs usage by month with trend lines
- Export a multi-page PDF report

## Usage
1. Upload PDFs via the Streamlit sidebar
2. Wait for the graphs to render and report to generate
3. Download the final report as `Fleet_Hobbs_Monthly_Report.pdf`

## Tech Stack
- Streamlit
- Pandas
- Matplotlib + Seaborn
- PyMuPDF

