import streamlit as st
import pandas as pd
from investoscrapo.client import InvestingClient
import io
from datetime import date, datetime, timedelta
import base64
from yfin_search import yahoo_finance_search
# import logging
from bse_scraper.BSE_Client import bse_scraper 
from nse_scraper.NSE_Client import nse_scraper
investing = InvestingClient()
bse = bse_scraper()
nse = nse_scraper()

def search_bse(query):
    
    standardized_results = []
    
    bse_results = bse.fetch_search_results(query)


    for item in bse_results:
        if item["description"] == "No Match Found":
            result = {}
            break
        else:
            result = {
                'id': item.get('id', 'N/A'),  # BSE scrip code
                'description': item.get('description', 'N/A'),
                'symbol': item.get('id', 'N/A'),  # Using BSE scrip code as symbol
                'exchange': 'BSE',
                'type': 'Stock - BSE',
                'isin': item.get('isin', 'N/A')  # Keep ISIN for reference
            }
        
        standardized_results.append(result)
    
    return standardized_results


st.set_page_config(
    page_title="VS Labs",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

def set_background(image_file):
    with open(image_file, "rb") as f:
        img_data = f.read()
    b64_encoded = base64.b64encode(img_data).decode()
    style = f"""
        <style>
        .stApp {{
            background-image: url(data:image/jpeg;base64,{b64_encoded});
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        </style>
    """
    st.markdown(style, unsafe_allow_html=True)

set_background("assets/back.jpg")

st.markdown(
    """
    <style>
    div[data-testid="stContainer"][style*="height"] {
        background-color: rgba(11, 28, 45, 0.65);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        border: 1px solid rgba(0, 229, 255, 0.15);
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

"""
# :material/query_stats: VS Labs
Easy analysis of securities.
"""

col1, col2 = st.columns([1.5, 5])

modes_map = {
    "Beta": "beta",
    "Volatility": "vol",
    "Prices": "price",
    "Volume": "volume",
    "Thinly Traded": "tt",
}
SOURCE_MAP = {
    "NSE": "nse",
    "BSE": "bse",
    "Yahoo Finance": "yahoo",
    "Investing.com": "investing",
}
if "previous_source" not in st.session_state:
    st.session_state.previous_source = "NSE" 

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "selected_list" not in st.session_state:
    st.session_state.selected_list = []

if "from_date" not in st.session_state:
    st.session_state.from_date = date.today() - timedelta(days=365)

if "to_date" not in st.session_state:
    st.session_state.to_date = date.today()

with col1:
    with st.container(border=True):
    # Buttons for picking modes
        selected_modes = st.pills(
            "Modes",
            options=list(modes_map.keys()),
            default=["Beta"],
            selection_mode="multi"
        )
    with st.container(border=True):
        st.subheader("Date Range")

        d1, d2 = st.columns(2)

        with d1:
            from_date = st.date_input(
                "From",
                value=st.session_state.from_date,
                max_value=st.session_state.to_date - timedelta(days=1),
            )

        with d2:
            to_date = st.date_input(
                "To",
                value=st.session_state.to_date,
                min_value=from_date + timedelta(days=1),
            )

        # Update session state
        st.session_state.from_date = from_date
        st.session_state.to_date = to_date


active_modes = [modes_map[m] for m in selected_modes]

with col2:
    with st.container(border=True):

        # HEADER ROW
        h1, h2 = st.columns([5.5, 3.5])

        with h1:
            st.markdown("###  Search Securities")

        with h2:
            source = st.pills(
                "Source",
                options=list(SOURCE_MAP.keys()),
                default="NSE",
                selection_mode="single",
                label_visibility="collapsed",
            )

        # SEARCH BAR ROW
        
        with st.form("search_form"):
            q1, q2 = st.columns([5, 1])

            with q1:
                query = st.text_input(
                    "Search",
                    placeholder="Search by name or symbol",
                    label_visibility="collapsed",
                )

            with q2:
                search_clicked = st.form_submit_button(
                    "Search",
                    use_container_width=True
                )
        if source != st.session_state.previous_source:
            st.session_state.search_results = []
            st.session_state.selected_list = []
            st.session_state.previous_source = source

        # Move the search logic OUTSIDE the form
        if search_clicked and query:
            with st.spinner("Searching..."):
                if source == "Yahoo Finance":
                    st.session_state.search_results = yahoo_finance_search(query)
                elif source == "Investing.com":
                    st.session_state.search_results = investing.Search(query)
                elif source == "BSE":
                    st.session_state.search_results = search_bse(query)
                elif source == "NSE":
                    st.session_state.search_results = nse.fetch_search_results(query)
                else:
                    pass
        # RESULTS AREA
        st.markdown("### Results")

        results_container = st.container(height=350)

        with results_container:
            if not st.session_state.search_results:
                st.info("Search for a security to see results here.")
            else:
                for result in st.session_state.search_results:
                    col_info, col_button = st.columns([4, 1])
                    with col_info:
                       st.markdown(f"""
                        **{result['description']}**  
                        `{result['symbol']}` • {result['exchange']} • {result['type']}
                        """) 
                    with col_button:
                        is_added = any(item["id"] == result["id"] for item in st.session_state.selected_list)
                        if not is_added:
                            if st.button("Add", key=f"add_{result['id']}"):
                                st.session_state.selected_list.append(result)
                                st.rerun()
                        else:
                            st.success("✓")
                    st.divider()        


# SELECTED LIST SECTION (below col2)
st.markdown("---")
st.markdown("### 📋 Selected Securities")

if not st.session_state.selected_list:
    st.info("No securities selected yet. Search and add securities above.")
else:
    # Display selected items
    for idx, item in enumerate(st.session_state.selected_list):
        col_info, col_remove = st.columns([5, 1])
        
        with col_info:
            st.markdown(f"""
            **{item['description']}**  
            `{item['symbol']}` • {item['exchange']} • {item['type']}
            """)
        
        with col_remove:
            if st.button("Remove", key=f"remove_{item['id']}"):
                st.session_state.selected_list.pop(idx)
                st.rerun()
        
        st.divider()