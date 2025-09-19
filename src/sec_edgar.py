

import requests
import json
import time
from pathlib import Path
from config import settings
from sec_edgar_downloader import Downloader

from utils.logger import logger, ErrorHandler
import time


from data.database import FinancialDataDB


from parsers.sec_parser import SECFilingParser



class SECEdgarScraper:
    def __init__(self):
        self.base_url = settings.SEC_EDGAR_BASE_URL
        self.delay = settings.SEC_RATE_LIMIT_DELAY
        self.raw_data_path = settings.RAW_DATA_PATH / "sec_filings"
        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        
        # Load companies data
        with open(Path(__file__).parent.parent / "config" / "companies.json", "r") as f:
            self.companies = json.load(f)["companies"]


        self.max_retries = 3
        self.retry_delay = 5  # seconds

        self.db = FinancialDataDB()


        self.parser = SECFilingParser()

    def extract_filing_data(self, file_path):
        """Extract relevant data from SEC filing using advanced parser"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Determine filing format and parse accordingly
            if file_path.endswith('.html') or file_path.endswith('.htm'):
                parsed_data = self.parser.parse_html_filing(content)
            elif file_path.endswith('.xml'):
                parsed_data = self.parser.parse_xml_filing(content)
            else:
                # Fallback to text parsing
                parsed_data = {
                    "sections": self._extract_sections(content),
                    "content_length": len(content)
                }
            
            if parsed_data:
                parsed_data["file_path"] = str(file_path)
                return parsed_data
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return None


    # def get_company_filings(self, company, filing_type="10-K", limit=5):
    #     """Download SEC filings for a company"""
    #     dl = Downloader(company["name"], self.raw_data_path / company["ticker"])
        
    #     try:
    #         # Download filings
    #         dl.get(filing_type, company["cik"], limit=limit)
    #         print(f"Downloaded {limit} {filing_type} filings for {company['name']}")
    #         return True
    #     except Exception as e:
    #         print(f"Error downloading filings for {company['name']}: {str(e)}")
    #         return False
    
    # def extract_filing_data(self, file_path):
    #     """Extract relevant data from SEC filing text"""
    #     try:
    #         with open(file_path, 'r', encoding='utf-8') as f:
    #             content = f.read()
            
    #         # Simple extraction - in a real project, you'd use more sophisticated parsing
    #         data = {
    #             "file_path": str(file_path),
    #             "content_length": len(content),
    #             "sections": self._extract_sections(content)
    #         }
            
    #         return data
    #     except Exception as e:
    #         print(f"Error reading file {file_path}: {str(e)}")
    #         return None


    def get_company_filings(self, company, filing_type="10-K", limit=5):
        """Download SEC filings for a company with retry logic"""
        dl = Downloader(company["name"], self.raw_data_path / company["ticker"])
        
        for attempt in range(self.max_retries):
            try:
                # Download filings
                dl.get(filing_type, company["cik"], limit=limit)
                logger.info(f"Downloaded {limit} {filing_type} filings for {company['name']}")
                return True
            except Exception as e:
                ErrorHandler.log_retry_attempt(
                    f"download SEC filings for {company['name']}",
                    attempt + 1,
                    self.max_retries,
                    self.retry_delay * (attempt + 1)
                )
                
                if attempt == self.max_retries - 1:
                    ErrorHandler.handle_error(
                        f"Failed to download {filing_type} filings for {company['name']}",
                        e
                    )
                    return False
                
                time.sleep(self.retry_delay * (attempt + 1))
        
        return False


    
    def _extract_sections(self, content):
        """Extract sections from filing content (simplified)"""
        sections = {}
        
        # Look for common sections in SEC filings
        section_markers = {
            "business": r"ITEM 1\. BUSINESS",
            "risk_factors": r"ITEM 1A\. RISK FACTORS",
            "financial_statements": r"ITEM 8\. FINANCIAL STATEMENTS"
        }
        
        for section, pattern in section_markers.items():
            # This is a simplified approach - real implementation would use proper parsing
            if pattern in content:
                sections[section] = f"Section '{section}' found"
        
        return sections
    
    # def process_all_companies(self, filing_type="10-K", limit=2):
    #     """Process SEC filings for all companies"""
    #     results = {}
        
    #     for company in self.companies:
    #         print(f"Processing {company['name']}...")
            
    #         # Download filings
    #         success = self.get_company_filings(company, filing_type, limit)
    #         if success:
    #             # In a real implementation, you would process the downloaded files
    #             results[company["ticker"]] = {
    #                 "status": "success",
    #                 "message": f"Downloaded {limit} {filing_type} filings"
    #             }
    #         else:
    #             results[company["ticker"]] = {
    #                 "status": "error",
    #                 "message": "Failed to download filings"
    #             }
            
    #         # Respect rate limiting
    #         time.sleep(self.delay)
        
    #     return results



    def process_all_companies(self, filing_type="10-K", limit=2):
        """Process SEC filings for all companies and store in database"""
        results = {}
        
        for company in self.companies:
            logger.info(f"Processing {company['name']}...")
            
            # Add company to database if not exists
            company_id = self.db.add_company(company["name"], company["ticker"], company["cik"])
            if not company_id:
                company_id = self.db.get_company_id(company["ticker"])
            
            # Download filings
            success = self.get_company_filings(company, filing_type, limit)
            if success:
                # Process downloaded files and add to database
                ticker_path = self.raw_data_path / company["ticker"]
                if ticker_path.exists():
                    for filing_path in ticker_path.glob("**/*.txt"):
                        filing_data = self.extract_filing_data(filing_path)
                        if filing_data:
                            # Extract filing date from path (simplified)
                            filing_date = filing_path.parent.name
                            self.db.add_sec_filing(
                                company_id,
                                filing_type,
                                filing_date,
                                filing_data["file_path"],
                                filing_data["content_length"],
                                filing_data["sections"]
                            )
                
                results[company["ticker"]] = {
                    "status": "success",
                    "message": f"Downloaded and processed {limit} {filing_type} filings"
                }
            else:
                results[company["ticker"]] = {
                    "status": "error",
                    "message": "Failed to download filings"
                }
            
            # Respect rate limiting
            time.sleep(self.delay)
        
        return results

# Example usage
if __name__ == "__main__":
    scraper = SECEdgarScraper()
    results = scraper.process_all_companies(limit=2)
    print(json.dumps(results, indent=2))