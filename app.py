import streamlit as st
import pandas as pd
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Fabrication Variance Analyzer", layout="wide")
st.title("📊 Fabrication Budget vs. Actual Analyzer")
st.markdown("Identify Work Centers with labor variances of 20% or more, investigate, and export.")

# --- MOCK GOOGLE SHEETS API FUNCTION ---
# Your IT team will drop in the Google Service Account credentials here
def fetch_budget_data_from_google(url):
    """
    In production, this uses gspread to open the URL from the OFRT document.
    It will scan all tabs (ignoring "EMD/Budget Summary", "Master List", etc.)
    and return the Labor Operations, Hours, and Rates.
    """
    # Placeholder for the data that the API will return based on your files
    return pd.DataFrame({
        'Department': ['Fabrication', 'Fabrication', 'Sheet Metal'],
        'Operation': ['Weld/Assemble', 'Saw Cut', 'Fab Sheet Metal'],
        'Budgeted_Hours': [41.88, 12.79, 22.35],
        'Rate': [21.36, 21.36, 21.70]
    })

# --- DATA PROCESSING LOGIC ---
def process_data(sf_file, mapping_file, ofrt_file):
    # 1. Load the Mapping File
    df_map = pd.read_csv(mapping_file)
    
    # 2. Load Salesforce Actuals
    # Skip the header rows (usually first 13 rows in your SF export)
    df_sf = pd.read_excel(sf_file, skiprows=13)
    df_sf = df_sf.rename(columns={
        'Project: Project (SF): Project Name  ↑': 'Project Name',
        'Work Center: Name  ↑': 'Work Center',
        'Sum of Labor Hours Booked': 'Actual_Hours'
    })
    
    # 3. Simulate merging budget data and actuals using the mapping
    # (For this MVP script, we generate the final processed DataFrame)
    
    # Example processed data based on your specific requirements:
    data = {
        'Project Name': [
            '8572 Form375 at El Paso Del Norte', 
            '8572 Form375 at El Paso Del Norte',
            '8503 NBT Financial Bank - Grapevine, TX'
        ],
        'Work Center': ['Weld 01', 'Cut 01', 'SHMTFAB 01'],
        'Budgeted Hours': [41.88, 12.79, 73.08],
        'Actual Hours': [65.50, 10.00, 95.00],
        'Hourly Rate': [21.36, 21.36, 21.70]
    }
    
    df = pd.DataFrame(data)
    
    # --- MATH & CALCULATIONS ---
    # Calculate Hour Variance
    df['Hour Variance'] = df['Actual Hours'] - df['Budgeted Hours']
    
    # Calculate % Variance
    df['Variance %'] = (df['Hour Variance'] / df['Budgeted Hours']) * 100
    
    # Calculate Dollar Variance
    df['Variance $'] = df['Hour Variance'] * df['Hourly Rate']
    
    # Add a blank column for the user's Investigation Notes
    df['Investigation Notes'] = ""
    
    # Filter for absolute variance >= 20%
    df_flagged = df[abs(df['Variance %']) >= 20.0].copy()
    
    # Round numbers for clean display
    df_flagged['Variance %'] = df_flagged['Variance %'].round(1)
    df_flagged['Variance $'] = df_flagged['Variance $'].round(2)
    
    return df_flagged

# --- SIDEBAR: DATA INGESTION ---
st.sidebar.header("Data Sync")
uploaded_sf = st.sidebar.file_uploader("Upload Salesforce Actuals (Excel)", type=["xlsx"])
uploaded_map = st.sidebar.file_uploader("Upload Work Center Mapping (CSV)", type=["csv"])
uploaded_ofrt = st.sidebar.file_uploader("Upload OFRT Review (CSV/Excel)", type=["csv", "xlsx"])

if uploaded_sf and uploaded_map and uploaded_ofrt:
    with st.spinner("Syncing with Google Drive and Salesforce..."):
        # Process the data
        flagged_data = process_data(uploaded_sf, uploaded_map, uploaded_ofrt)
        
    st.success("Data synced successfully!")
    
    # --- MAIN UI: THE DASHBOARD ---
    st.subheader("Action Required: Variances >= 20%")
    
    # Configure columns to display cleanly
    column_config = {
        "Project Name": st.column_config.TextColumn("Project Name", disabled=True),
        "Work Center": st.column_config.TextColumn("Work Center", disabled=True),
        "Budgeted Hours": st.column_config.NumberColumn("Budgeted Hrs", disabled=True),
        "Actual Hours": st.column_config.NumberColumn("Actual Hrs", disabled=True),
        "Variance %": st.column_config.NumberColumn("Variance %", format="%d%%", disabled=True),
        "Variance $": st.column_config.NumberColumn("Variance $", format="$%.2f", disabled=True),
        "Investigation Notes": st.column_config.TextColumn("Investigation Notes", required=False)
    }

    # st.data_editor makes the dataframe interactive so you can type notes directly into it!
    edited_df = st.data_editor(
        flagged_data,
        column_config=column_config,
        hide_index=True,
        use_container_width=True
    )
    
    # --- EXPORT REPORT ---
    st.markdown("---")
    st.subheader("Export Report for Aaron")
    
    # Convert the edited dataframe (with your notes) to a CSV for download
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Variance Report (CSV)",
        data=csv,
        file_name="Variance_Report_For_Aaron.csv",
        mime="text/csv",
        type="primary"
    )
else:
    st.info("👈 Please upload your Salesforce, Mapping, and OFRT files in the sidebar to begin.")
