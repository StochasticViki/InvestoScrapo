import streamlit as st
import pandas as pd
from investoscrapo.client import InvestingClient

# Initialize client
client = InvestingClient()

# Session state to store selected companies across multiple searches
if "selected_companies" not in st.session_state:
    st.session_state.selected_companies = []

st.title("Investing Historical Data Downloader")

# --- Company Search ---
search_query = st.text_input("Search Company:")

if st.button("Search"):
    search_results = client.Search(search_query)
    
    # Show results as a multiselect widget
    options = [f"{r['description']} ({r['symbol']}, {r['exchange']})" for r in search_results]
    
    selected = st.multiselect(
        "Select companies to add to your list:",
        options=options
    )
    
    # Add selected companies to session_state
    for sel in selected:
        # Map the selected string back to the dict
        for r in search_results:
            label = f"{r['description']} ({r['symbol']}, {r['exchange']})"
            if label == sel and r not in st.session_state.selected_companies:
                st.session_state.selected_companies.append(r)

# --- Show currently selected companies ---
st.subheader("Currently Selected Companies:")
for idx, comp in enumerate(st.session_state.selected_companies):
    st.write(f"{idx+1}. {comp['description']} ({comp['symbol']}, {comp['exchange']})")
    if st.button(f"Remove {comp['symbol']}", key=f"remove_{idx}"):
        st.session_state.selected_companies.pop(idx)
        st.experimental_rerun()  # Refresh to update list

# --- Date Selection ---
st.subheader("Select Date Range:")
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")

# --- Download Historical Data ---
if st.button("Download Historical Data"):
    if not st.session_state.selected_companies:
        st.warning("No companies selected!")
    else:
        df_list = client.Download_Historical(st.session_state.selected_companies,
                                             start_date.strftime("%Y-%m-%d"),
                                             end_date.strftime("%Y-%m-%d"))
        
        # Combine all dfs into one Excel file with multiple sheets
        excel_path = "historical_data.xlsx"
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            for i, df in enumerate(df_list):
                sheet_name = st.session_state.selected_companies[i]["symbol"]
                df.to_excel(writer, index=False, sheet_name=sheet_name)
        
        st.success(f"Historical data saved to {excel_path}")
        st.download_button(
            "Download Excel File",
            data=open(excel_path, "rb").read(),
            file_name="historical_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
