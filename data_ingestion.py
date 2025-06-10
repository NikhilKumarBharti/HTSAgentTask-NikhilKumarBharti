import os
import requests
import pandas as pd
import sqlite3
import time
import random
from pathlib import Path
from typing import List, Dict, Tuple
from urllib.parse import urlencode
from config import Config

class HTSDataIngestion:
    def __init__(self):
        self.config = Config()
        self.data_dir = Path(self.config.DATA_DIR)
        self.data_dir.mkdir(exist_ok=True)
        
        # HTS API endpoint
        self.hts_api_url = "https://hts.usitc.gov/reststop/exportList"
        
        # Define HTS chapter ranges for systematic download
        self.hts_ranges = [
            {"name": "agricultural", "from": "0100", "to": "2400", "description": "Live animals, food, beverages, tobacco"},
            {"name": "chemicals", "from": "2500", "to": "4000", "description": "Chemicals, plastics, rubber"},
            {"name": "textiles", "from": "4100", "to": "6300", "description": "Hides, textiles, footwear"},
            {"name": "base_metals", "from": "7200", "to": "8300", "description": "Base metals and articles"},
            {"name": "machinery", "from": "8400", "to": "8500", "description": "Machinery and electrical equipment"},
            {"name": "transport", "from": "8600", "to": "8900", "description": "Vehicles, aircraft, vessels"},
            {"name": "miscellaneous", "from": "9000", "to": "9700", "description": "Miscellaneous manufactured articles"}
        ]
        
        # Alternative: Download in smaller chunks to avoid timeouts
        self.chunk_ranges = self._generate_chapter_chunks()
    
    def _generate_chapter_chunks(self, chunk_size: int = 5) -> List[Dict]:
        """Generate smaller chapter chunks for more reliable downloads"""
        chunks = []
        for start in range(1, 100, chunk_size):
            end = min(start + chunk_size - 1, 99)
            chunks.append({
                "name": f"chapters_{start:02d}_{end:02d}",
                "from": f"{start:02d}00",
                "to": f"{end:02d}99",
                "description": f"HTS Chapters {start}-{end}"
            })
        return chunks
    
    def build_hts_url(self, from_chapter: str, to_chapter: str, format_type: str = "CSV", styles: bool = True) -> str:
        """Build the HTS API URL with proper parameters"""
        params = {
            "from": from_chapter,
            "to": to_chapter,
            "format": format_type,
            "styles": str(styles).lower()
        }
        return f"{self.hts_api_url}?{urlencode(params)}"
    
    def download_hts_range_with_retry(self, from_chapter: str, to_chapter: str, filename: str, max_retries: int = 3) -> str:
        """Download HTS data for a specific range with retry logic"""
        csv_path = self.data_dir / filename
        
        # Skip if file already exists and is not empty
        if csv_path.exists() and csv_path.stat().st_size > 1000:  # At least 1KB
            print(f"✅ File already exists: {filename}")
            return str(csv_path)
        
        url = self.build_hts_url(from_chapter, to_chapter)
        
        for attempt in range(max_retries):
            try:
                print(f"📥 Downloading {filename} (attempt {attempt + 1}/{max_retries})")
                print(f"URL: {url}")
                
                # Add delay between attempts
                if attempt > 0:
                    delay = (2 ** attempt) + random.uniform(0, 2)
                    print(f"⏳ Waiting {delay:.1f} seconds before retry...")
                    time.sleep(delay)
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/csv,application/csv,text/plain,*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                    'Cache-Control': 'no-cache'
                }
                
                response = requests.get(url, headers=headers, timeout=120)
                response.raise_for_status()
                
                # Check if we got meaningful data
                if len(response.text) < 100:
                    raise ValueError(f"Response too short: {len(response.text)} characters")
                
                # Save the CSV data
                with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                    f.write(response.text)
                
                # Validate the CSV
                try:
                    df = pd.read_csv(csv_path)
                    if len(df) == 0:
                        raise ValueError("Empty CSV file")
                    print(f"✅ Successfully downloaded: {filename} ({len(df)} rows, {len(df.columns)} columns)")
                    return str(csv_path)
                except Exception as e:
                    print(f"⚠️ CSV validation warning: {e}")
                    # Still return the path - might be readable by other tools
                    return str(csv_path)
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Download attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    print(f"❌ All {max_retries} attempts failed for {filename}")
                    return None
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                if attempt == max_retries - 1:
                    return None
        
        return None
    
    def download_general_notes(self) -> str:
        """Download HTS General Notes PDF (keeping original functionality)"""
        # Try the official notes endpoint first
        notes_urls = [
            #"https://hts.usitc.gov/reststop/file?filename=notes&release=currentRelease",
            "https://hts.usitc.gov/reststop/file?release=currentRelease&filename=General%20Notes",
            f"{self.config.HTS_BASE_URL}/notes" if hasattr(self.config, 'HTS_BASE_URL') else None
        ]
        
        pdf_path = self.data_dir / "general_notes.pdf"
        
        if pdf_path.exists():
            print(f"✅ General Notes PDF already exists at {pdf_path}")
            return str(pdf_path)
        
        for url in notes_urls:
            if not url:
                continue
                
            try:
                print(f"📥 Trying to download General Notes from: {url}")
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Downloaded General Notes to {pdf_path}")
                return str(pdf_path)
            
            except Exception as e:
                print(f"❌ Failed to download from {url}: {e}")
                continue
        
        print("⚠️ Could not download General Notes PDF")
        return None
    
    def download_hts_csvs(self, use_chunks: bool = True) -> List[str]:
        """Download HTS CSV files using the REST API"""
        downloaded_files = []
        
        # Choose between predefined ranges or smaller chunks
        ranges_to_download = self.chunk_ranges if use_chunks else self.hts_ranges
        
        print(f"🔄 Starting download of {len(ranges_to_download)} HTS ranges...")
        
        for range_info in ranges_to_download:
            filename = f"hts_{range_info['name']}.csv"
            print(f"\n📋 {range_info['description']}")
            
            result = self.download_hts_range_with_retry(
                range_info['from'], 
                range_info['to'], 
                filename
            )
            
            if result:
                downloaded_files.append(result)
            else:
                print(f"❌ Failed to download {filename}")
            
            # Add delay between downloads to be respectful to the server
            time.sleep(2)
        
        print(f"\n✅ Downloaded {len(downloaded_files)} out of {len(ranges_to_download)} HTS files")
        return downloaded_files
    
    def download_complete_hts(self) -> str:
        """Download the complete HTS schedule in one file"""
        print("📥 Attempting to download complete HTS schedule...")
        filename = "hts_complete.csv"
        
        result = self.download_hts_range_with_retry("0100", "9999", filename, max_retries=5)
        
        if result:
            print("✅ Successfully downloaded complete HTS schedule")
        else:
            print("❌ Failed to download complete HTS schedule")
            print("💡 Tip: Try downloading in smaller chunks instead")
        
        return result
    
    def enhance_csv_data(self, csv_path: str) -> pd.DataFrame:
        """Enhance CSV data with full country names and cleaned data"""
        try:
            df = pd.read_csv(csv_path)
            
            # Enhance country codes if available
            if hasattr(self.config, 'COUNTRY_CODES') and 'country_code' in df.columns:
                df['country_name'] = df['country_code'].map(
                    self.config.COUNTRY_CODES
                ).fillna(df['country_code'])
            
            # Clean and standardize columns
            df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
            
            # Clean duty rate formats if present
            duty_rate_columns = [col for col in df.columns if 'duty' in col or 'rate' in col]
            for col in duty_rate_columns:
                df[col] = df[col].astype(str).str.strip()
            
            return df
        
        except Exception as e:
            print(f"⚠️ Error enhancing CSV data for {csv_path}: {e}")
            # Return basic DataFrame if enhancement fails
            return pd.read_csv(csv_path)
    
    def create_sqlite_database(self, csv_files: List[str]):
        """Create SQLite database from CSV files"""
        if not csv_files:
            print("⚠️ No CSV files to process into database")
            return
        
        db_path = self.config.SQLITE_DB_PATH if hasattr(self.config, 'SQLITE_DB_PATH') else self.data_dir / "hts_data.db"
        
        try:
            conn = sqlite3.connect(db_path)
            
            for csv_file in csv_files:
                try:
                    df = self.enhance_csv_data(csv_file)
                    table_name = Path(csv_file).stem
                    
                    df.to_sql(table_name, conn, if_exists='replace', index=False)
                    print(f"✅ Created table {table_name} in database ({len(df)} rows)")
                    
                except Exception as e:
                    print(f"❌ Error processing {csv_file}: {e}")
                    continue
            
            conn.close()
            print(f"✅ Database created at {db_path}")
            
        except Exception as e:
            print(f"❌ Error creating SQLite database: {e}")
    
    def run_ingestion(self, download_method: str = "chunks") -> Tuple[str, List[str]]:
        """
        Run complete data ingestion process
        
        Args:
            download_method: "chunks" (recommended), "ranges", or "complete"
        """
        print("🚀 Starting HTS data ingestion...")
        print(f"📁 Data directory: {self.data_dir}")
        
        # Download General Notes PDF
        pdf_path = self.download_general_notes()
        
        # Download CSV files based on method
        if download_method == "complete":
            csv_file = self.download_complete_hts()
            csv_files = [csv_file] if csv_file else []
        elif download_method == "ranges":
            csv_files = self.download_hts_csvs(use_chunks=False)
        else:  # chunks (default)
            csv_files = self.download_hts_csvs(use_chunks=True)
        
        # Create database
        if csv_files:
            self.create_sqlite_database(csv_files)
        else:
            print("⚠️ No CSV files downloaded - skipping database creation")
        
        print("🎉 Data ingestion completed!")
        print(f"📊 Results: PDF={'✅' if pdf_path else '❌'}, CSV files={len(csv_files)}")
        
        return pdf_path, csv_files

if __name__ == "__main__":
    ingestion = HTSDataIngestion()
    
    # Try different download methods if one fails
    methods_to_try = ["chunks", "ranges", "complete"]
    
    for method in methods_to_try:
        print(f"\n🔄 Trying download method: {method}")
        try:
            pdf_path, csv_files = ingestion.run_ingestion(download_method=method)
            if csv_files:
                print(f"✅ Success with {method} method!")
                break
            else:
                print(f"❌ No files downloaded with {method} method")
        except Exception as e:
            print(f"❌ {method} method failed: {e}")
            continue
    else:
        print("❌ All download methods failed. Please check your internet connection and try again later.")