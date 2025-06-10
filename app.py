import streamlit as st
import os
from pathlib import Path
import pandas as pd
from hts_agent import HTSAgent
from data_ingestion import HTSDataIngestion
from duty_calculator import ProductInfo

# Page config
st.set_page_config(
    page_title="TariffBot - HTS Assistant",
    page_icon="🚢",
    layout="wide"
)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

def initialize_agent():
    """Initialize the HTS agent"""
    if not st.session_state.initialized:
        with st.spinner("Initializing TariffBot..."):
            try:
                st.session_state.agent = HTSAgent()
                
                # Check if data exists
                pdf_path = "data/general_notes.pdf"
                if os.path.exists(pdf_path):
                    st.session_state.agent.initialize(pdf_path)
                    st.session_state.initialized = True
                    st.success("TariffBot initialized successfully!")
                else:
                    st.warning("General Notes PDF not found. Some features may be limited.")
                    st.session_state.agent.initialize()
                    st.session_state.initialized = True
                    
            except Exception as e:
                st.error(f"Error initializing TariffBot: {str(e)}")
                return False
    
    return True

def main():
    st.title("🚢 TariffBot - HTS Assistant")
    st.markdown("*Your intelligent assistant for U.S. International Trade Commission data*")
    
    # Sidebar for data management
    with st.sidebar:
        st.header("🔧 Data Management")
        
        if st.button("Download HTS Data"):
            with st.spinner("Downloading HTS data..."):
                try:
                    ingestion = HTSDataIngestion()
                    pdf_path, csv_files = ingestion.run_ingestion()
                    st.success(f"Downloaded {len(csv_files)} CSV files and PDF")
                    st.session_state.initialized = False  # Reset to reinitialize
                except Exception as e:
                    st.error(f"Error downloading data: {str(e)}")
        
        st.markdown("---")
        st.markdown("**Status:**")
        
        # Check data status
        pdf_exists = os.path.exists("data/general_notes.pdf")
        db_exists = os.path.exists("data/hts_data.db")
        
        st.write(f"📄 General Notes PDF: {'✅' if pdf_exists else '❌'}")
        st.write(f"🗃️ HTS Database: {'✅' if db_exists else '❌'}")
        st.write(f"🤖 Agent Status: {'✅ Ready' if st.session_state.initialized else '❌ Not Initialized'}")
    
    # Initialize agent
    if not initialize_agent():
        st.stop()
    
    # Main interface tabs
    tab1, tab2, tab3 = st.tabs(["💬 Ask Questions", "🧮 Duty Calculator", "📊 Batch Calculator"])
    
    with tab1:
        st.header("Ask TariffBot")
        st.markdown("Ask questions about trade policies, agreements, or HTS codes.")
        
        # Example questions
        with st.expander("📝 Example Questions"):
            st.markdown("""
            - What is United States-Israel Free Trade?
            - What are the general rules for calculating duties?
            - How does the GSP (Generalized System of Preferences) work?
            - What are the special provisions for NAFTA countries?
            """)
        
        # Question input
        question = st.text_area(
            "Your Question:",
            placeholder="Enter your question about HTS, trade policies, or tariff calculations...",
            height=100
        )
        
        if st.button("Ask TariffBot", type="primary"):
            if question.strip():
                with st.spinner("Thinking..."):
                    try:
                        response = st.session_state.agent.process_query(question)
                        st.markdown("### 🤖 TariffBot Response:")
                        st.markdown(response)
                    except Exception as e:
                        st.error(f"Error processing question: {str(e)}")
            else:
                st.warning("Please enter a question.")
    
    with tab2:
        st.header("HTS Duty Calculator")
        st.markdown("Calculate duties and landed costs for specific HTS codes.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Product Information")
            hts_code = st.text_input("HTS Code", placeholder="e.g., 0101.21.00")
            cost = st.number_input("Product Cost ($)", min_value=0.0, step=0.01)
            freight = st.number_input("Freight Cost ($)", min_value=0.0, step=0.01)
            insurance = st.number_input("Insurance Cost ($)", min_value=0.0, step=0.01)
        
        with col2:
            st.subheader("Quantity & Weight")
            quantity = st.number_input("Quantity", min_value=1, step=1)
            unit_weight = st.number_input("Unit Weight (kg)", min_value=0.0, step=0.1)
            country = st.selectbox(
                "Country of Origin",
                ["CN", "CA", "MX", "DE", "FR", "GB", "JP", "KR", "IN", "AU"],
                help="Select the country code where the product originates"
            )
        
        if st.button("Calculate Duty", type="primary"):
            if hts_code and cost > 0:
                with st.spinner("Calculating..."):
                    try:
                        result = st.session_state.agent.quick_duty_calculation(
                            hts_code, cost, freight, insurance, quantity, unit_weight
                        )
                        
                        st.markdown("### 💰 Calculation Results:")
                        st.code(result, language=None)
                        
                    except Exception as e:
                        st.error(f"Error calculating duty: {str(e)}")
            else:
                st.warning("Please enter valid HTS code and product cost.")
    
    with tab3:
        st.header("Batch Duty Calculator")
        st.markdown("Upload a CSV file with multiple products for batch calculation.")
        
        # Template download
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download CSV Template"):
                template_data = {
                    'hts_code': ['0101.21.00', '0102.90.40'],
                    'cost': [1000.0, 2000.0],
                    'freight': [100.0, 200.0],
                    'insurance': [50.0, 100.0],
                    'quantity': [10, 5],
                    'unit_weight': [100.0, 200.0],
                    'country_of_origin': ['CN', 'MX']
                }
                template_df = pd.DataFrame(template_data)
                csv = template_df.to_csv(index=False)
                st.download_button(
                    label="Download Template",
                    data=csv,
                    file_name="hts_batch_template.csv",
                    mime="text/csv"
                )
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload CSV File",
            type=['csv'],
            help="Upload a CSV file with columns: hts_code, cost, freight, insurance, quantity, unit_weight"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.subheader("📋 Uploaded Data Preview")
                st.dataframe(df.head())
                
                if st.button("Calculate All Duties", type="primary"):
                    results = []
                    progress_bar = st.progress(0)
                    
                    for idx, row in df.iterrows():
                        try:
                            result = st.session_state.agent.quick_duty_calculation(
                                row['hts_code'], row['cost'], row['freight'],
                                row['insurance'], row['quantity'], row['unit_weight']
                            )
                            
                            # Parse result for display
                            lines = result.split('\n')
                            duty_amount = 0
                            total_cost = 0
                            
                            for line in lines:
                                if 'Duty Amount:' in line:
                                    duty_amount = float(line.split(':')[1].strip())
                                elif 'Total Landed Cost:' in line:
                                    total_cost = float(line.split(':')[1].strip())
                            
                            results.append({
                                'HTS Code': row['hts_code'],
                                'Product Cost': row['cost'],
                                'CIF Value': row['cost'] + row['freight'] + row['insurance'],
                                'Duty Amount': duty_amount,
                                'Total Landed Cost': total_cost
                            })
                            
                        except Exception as e:
                            results.append({
                                'HTS Code': row['hts_code'],
                                'Product Cost': row['cost'],
                                'CIF Value': 0,
                                'Duty Amount': 0,
                                'Total Landed Cost': 0,
                                'Error': str(e)
                            })
                        
                        progress_bar.progress((idx + 1) / len(df))
                    
                    # Display results
                    results_df = pd.DataFrame(results)
                    st.subheader("📊 Calculation Results")
                    st.dataframe(results_df)
                    
                    # Download results
                    csv_results = results_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Results",
                        data=csv_results,
                        file_name="duty_calculations_results.csv",
                        mime="text/csv"
                    )
                    
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>TariffBot v1.0 | Powered by Open Source LLMs | 
        <a href='https://hts.usitc.gov' target='_blank'>Data Source: HTS.USITC.GOV</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()