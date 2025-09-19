
import re
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from utils.logger import logger

class SECFilingParser:
    """Advanced parser for SEC EDGAR filings"""
    
    def __init__(self):
        self.section_patterns = {
            "business": r"ITEM\s*1\.?\s*BUSINESS",
            "risk_factors": r"ITEM\s*1A\.?\s*RISK\s*FACTORS",
            "financial_statements": r"ITEM\s*8\.?\s*FINANCIAL\s*STATEMENTS",
            "mdna": r"ITEM\s*7\.?\s*MANAGEMENT'S\s*DISCUSSION\s*AND\s*ANALYSIS"
        }
    
    def parse_html_filing(self, html_content):
        """Parse HTML format SEC filing"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            # Extract text
            text = soup.get_text(separator='\n', strip=True)
            
            # Parse sections
            sections = self._extract_sections(text)
            
            return {
                "sections": sections,
                "metadata": self._extract_metadata(soup),
                "tables": self._extract_tables(soup)
            }
            
        except Exception as e:
            logger.error(f"Failed to parse HTML filing: {str(e)}")
            return None
    
    def parse_xml_filing(self, xml_content):
        """Parse XML format SEC filing (XBRL)"""
        try:
            root = ET.fromstring(xml_content)
            
            # Namespace handling
            namespaces = {
                'xbrli': 'http://www.xbrl.org/2003/instance',
                'us-gaap': 'http://fasb.org/us-gaap/2021-01-01'
            }
            
            # Extract financial facts
            facts = {}
            for elem in root.findall('.//xbrli:fact', namespaces):
                context_ref = elem.get('contextRef')
                unit_ref = elem.get('unitRef')
                value = elem.text
                facts[elem.tag.split('}')[1]] = {
                    'value': value,
                    'context': context_ref,
                    'unit': unit_ref
                }
            
            return {
                "facts": facts,
                "contexts": self._extract_contexts(root, namespaces)
            }
            
        except Exception as e:
            logger.error(f"Failed to parse XML filing: {str(e)}")
            return None
    
    def _extract_sections(self, text):
        """Extract sections from filing text using regex patterns"""
        sections = {}
        
        for section_name, pattern in self.section_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start_pos = match.start()
                
                # Find the end of the section (next ITEM or end of document)
                next_item_match = re.search(r"ITEM\s*\d+[A-Z]?\.", text[start_pos + 10:])
                if next_item_match:
                    end_pos = start_pos + 10 + next_item_match.start()
                    section_content = text[start_pos:end_pos]
                else:
                    section_content = text[start_pos:]
                
                sections[section_name] = section_content.strip()
        
        return sections
    
    def _extract_metadata(self, soup):
        """Extract metadata from SEC filing"""
        metadata = {}
        
        # Extract company information
        company_info = soup.find('company-info')
        if company_info:
            metadata['company_name'] = company_info.get('name', '')
            metadata['cik'] = company_info.get('cik', '')
        
        # Extract filing date and type
        acceptance = soup.find('acceptance-datetime')
        if acceptance:
            metadata['filing_date'] = acceptance.text[:10]
        
        return metadata
    
    def _extract_tables(self, soup):
        """Extract tables from SEC filing"""
        tables = []
        
        for table in soup.find_all('table'):
            table_data = []
            
            # Extract table headers
            headers = []
            for th in table.find_all('th'):
                headers.append(th.get_text(strip=True))
            
            # Extract table rows
            for tr in table.find_all('tr'):
                row = []
                for td in tr.find_all('td'):
                    row.append(td.get_text(strip=True))
                if row:
                    table_data.append(row)
            
            if headers or table_data:
                tables.append({
                    'headers': headers,
                    'data': table_data
                })
        
        return tables
    
    def _extract_contexts(self, root, namespaces):
        """Extract contexts from XBRL filing"""
        contexts = {}
        
        for context in root.findall('.//xbrli:context', namespaces):
            context_id = context.get('id')
            period = context.find('xbrli:period', namespaces)
            
            if period is not None:
                start_date = period.find('xbrli:startDate', namespaces)
                end_date = period.find('xbrli:endDate', namespaces)
                instant = period.find('xbrli:instant', namespaces)
                
                context_info = {
                    'start_date': start_date.text if start_date is not None else None,
                    'end_date': end_date.text if end_date is not None else None,
                    'instant': instant.text if instant is not None else None
                }
                
                contexts[context_id] = context_info
        
        return contexts