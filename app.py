import streamlit as st
import pandas as pd
from investoscrapo.client import InvestingClient
import io
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Investment Data Downloader",
    page_icon="📈",
    layout="wide"
)

# Initialize client with error handling
@st.cache_resource
def init_client():
    """Initialize the InvestingClient with caching"""
    try:
        return InvestingClient()
    except Exception as e:
        st.error(f"Failed to initialize client: {str(e)}")
        return None

client = init_client()

# Session state initialization
if "selected_companies" not in st.session_state:
    st.session_state.selected_companies = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "last_search" not in st.session_state:
    st.session_state.last_search = ""

# Custom CSS for better styling
st.markdown("""
<style>
.company-card {
    padding: 15px;
    margin: 10px 0;
    border-radius: 8px;
    background-color: var(--secondary-background-color, #f0f2f6) !important;
    border: 2px solid var(--primary-color, #1f77b4);
    color: var(--text-color, #262730) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.company-card strong {
    color: var(--text-color, #262730) !important;
    font-size: 1.1em;
}
.metric-card {
    background-color: var(--background-color, #ffffff);
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    color: var(--text-color, #262730) !important;
}

/* Ensure text visibility in both light and dark modes */
[data-theme="dark"] .company-card {
    background-color: #2d3748 !important;
    border-color: #4299e1 !important;
    color: #e2e8f0 !important;
}
[data-theme="dark"] .company-card strong {
    color: #e2e8f0 !important;
}
</style>
""", unsafe_allow_html=True)

# Main title and description
st.title("📈 Investment Historical Data Downloader")
st.markdown("Search and download historical stock data for multiple companies")

if not client:
    st.stop()

# Create two columns for better layout
col1, col2 = st.columns([2, 1])

with col1:
    # --- Company Search Section ---
    st.header("🔍 Company Search")
    
    with st.form("search_form"):
        search_query = st.text_input(
            "Enter company name or symbol:",
            placeholder="e.g., Apple, AAPL, Microsoft"
        )
        search_button = st.form_submit_button("Search", use_container_width=True)

    if search_button and search_query:
        if search_query != st.session_state.last_search:
            with st.spinner("Searching companies..."):
                try:
                    search_results = client.Search(search_query)
                    st.session_state.search_results = search_results
                    st.session_state.last_search = search_query
                    
                    if not search_results:
                        st.warning("No companies found for your search query.")
                    else:
                        st.success(f"Found {len(search_results)} companies")
                        
                except Exception as e:
                    st.error(f"Search failed: {str(e)}")
                    logger.error(f"Search error: {e}")

    # Display search results
    if st.session_state.search_results:
        st.subheader("Search Results")
        
        for idx, result in enumerate(st.session_state.search_results):
            with st.container():
                col_info, col_btn = st.columns([3, 1])
                
                with col_info:
                    st.markdown(f"""
                    <div class="company-card">
                        <strong>{result['description']}</strong><br>
                        Symbol: {result['symbol']} | Exchange: {result['exchange']}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_btn:
                    # Check if company is already selected
                    is_selected = any(comp['symbol'] == result['symbol'] for comp in st.session_state.selected_companies)
                    
                    if not is_selected:
                        if st.button(f"Add", key=f"add_{idx}", use_container_width=True):
                            st.session_state.selected_companies.append(result)
                            st.rerun()
                    else:
                        st.success("✓ Added")

with col2:
    # --- Selected Companies Panel ---
    st.header("📊 Selected Companies")
    
    if st.session_state.selected_companies:
        st.markdown(f"**{len(st.session_state.selected_companies)} companies selected**")
        
        # Clear all button
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.selected_companies = []
            st.rerun()
        
        st.markdown("---")
        
        # Display selected companies
        for idx, comp in enumerate(st.session_state.selected_companies):
            with st.container():
                st.markdown(f"""
                **{comp['description']}**  
                {comp['symbol']} ({comp['exchange']})
                """)
                
                if st.button(f"Remove", key=f"remove_{idx}"):
                    st.session_state.selected_companies.pop(idx)
                    st.rerun()
                
                if idx < len(st.session_state.selected_companies) - 1:
                    st.markdown("---")
    else:
        st.info("No companies selected yet. Use the search to add companies.")

# --- Date Selection and Download Section ---
st.header("📅 Download Configuration")

col_date1, col_date2, col_download = st.columns([1, 1, 1])

with col_date1:
    # Set default dates (1 year ago to today)
    default_start = datetime.now() - timedelta(days=365)
    start_date = st.date_input(
        "Start Date:",
        value=default_start,
        max_value=datetime.now().date()
    )

with col_date2:
    end_date = st.date_input(
        "End Date:",
        value=datetime.now().date(),
        max_value=datetime.now().date()
    )

with col_download:
    st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
    download_button = st.button(
        "📥 Download Data",
        use_container_width=True,
        type="primary"
    )

# Validation and download logic
if download_button:
    # Validation
    errors = []
    
    if not st.session_state.selected_companies:
        errors.append("No companies selected!")
    
    if start_date >= end_date:
        errors.append("Start date must be before end date!")
    
    if (end_date - start_date).days > 365 * 5:  # 5 years limit
        errors.append("Date range cannot exceed 5 years!")
    
    if errors:
        for error in errors:
            st.error(error)
    else:
        # Download process
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("Downloading historical data...")
            
            df_list = client.Download_Historical(
                st.session_state.selected_companies,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            
            progress_bar.progress(50)
            status_text.text("Processing data...")
            
            # Create Excel file in memory
            excel_buffer = io.BytesIO()
            
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                for i, df in enumerate(df_list):
                    if df is not None and not df.empty:
                        sheet_name = st.session_state.selected_companies[i]["symbol"]
                        # Clean sheet name (Excel has character limits)
                        sheet_name = sheet_name[:31]  # Excel limit
                        df.to_excel(writer, index=False, sheet_name=sheet_name)
                        
                        # Add some formatting
                        workbook = writer.book
                        worksheet = writer.sheets[sheet_name]
                        
                        # Format headers
                        header_format = workbook.add_format({
                            'bold': True,
                            'text_wrap': True,
                            'valign': 'top',
                            'fg_color': '#D7E4BD',
                            'border': 1
                        })
                        
                        for col_num, value in enumerate(df.columns.values):
                            worksheet.write(0, col_num, value, header_format)
                            worksheet.set_column(col_num, col_num, 15)
            
            progress_bar.progress(100)
            status_text.text("✅ Data processed successfully!")
            
            # Generate filename with timestamp
            filename = f"historical_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # Success metrics
            col_metric1, col_metric2, col_metric3 = st.columns(3)
            
            with col_metric1:
                st.metric("Companies Downloaded", len(df_list))
            
            with col_metric2:
                total_rows = sum(len(df) for df in df_list if df is not None)
                st.metric("Total Data Points", total_rows)
            
            with col_metric3:
                days_range = (end_date - start_date).days
                st.metric("Date Range (Days)", days_range)
            
            # Download button
            st.download_button(
                label="📥 Download Excel File",
                data=excel_buffer.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            # Data preview
            if df_list and len(df_list) > 0:
                st.subheader("📊 Data Preview")
                
                # Show preview of first company's data
                preview_df = df_list[0]
                if preview_df is not None and not preview_df.empty:
                    st.markdown(f"**Preview: {st.session_state.selected_companies[0]['description']}**")
                    st.dataframe(
                        preview_df.head(10),
                        use_container_width=True
                    )
                    
                    if len(preview_df) > 10:
                        st.info(f"Showing first 10 rows of {len(preview_df)} total rows")
            
        except Exception as e:
            st.error(f"Download failed: {str(e)}")
            logger.error(f"Download error: {e}")
        
        finally:
            progress_bar.empty()
            status_text.empty()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>Built with Streamlit • Data provided by investing.com</small>
</div>
""", unsafe_allow_html=True)