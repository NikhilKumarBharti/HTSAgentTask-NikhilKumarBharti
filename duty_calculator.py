import sqlite3
import pandas as pd
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from config import Config

@dataclass
class ProductInfo:
    hts_code: str
    cost: float
    freight: float
    insurance: float
    quantity: int
    unit_weight: float
    country_of_origin: str = "CN"

@dataclass
class DutyCalculation:
    hts_code: str
    product_description: str
    cif_value: float
    duty_rate: str
    duty_amount: float
    total_landed_cost: float
    duty_type: str
    breakdown: Dict[str, float]

class DutyCalculator:
    def __init__(self):
        self.config = Config()
        self.db_path = self.config.SQLITE_DB_PATH
    
    def get_hts_data(self, hts_code: str) -> Optional[Dict]:
        """Retrieve HTS data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Search across all tables for the HTS code
            tables = self._get_table_names(conn)
            
            for table in tables:
                query = f"""
                SELECT * FROM {table} 
                WHERE hts_code LIKE ? OR hts_number LIKE ?
                LIMIT 1
                """
                
                df = pd.read_sql_query(
                    query, conn, 
                    params=[f"%{hts_code}%", f"%{hts_code}%"]
                )
                
                if not df.empty:
                    conn.close()
                    return df.iloc[0].to_dict()
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error retrieving HTS data: {e}")
            return None
    
    def _get_table_names(self, conn) -> List[str]:
        """Get all table names from database"""
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in cursor.fetchall()]
    
    def parse_duty_rate(self, duty_rate: str) -> Tuple[str, float]:
        """Parse duty rate string and return type and value"""
        if not duty_rate or pd.isna(duty_rate):
            return "free", 0.0
        
        duty_rate = str(duty_rate).strip().lower()
        
        # Free duty
        if "free" in duty_rate or duty_rate == "0":
            return "free", 0.0
        
        # Percentage rate (e.g., "15%", "5.2%")
        percent_match = re.search(r'(\d+\.?\d*)%', duty_rate)
        if percent_match:
            return "percentage", float(percent_match.group(1))
        
        # Cents per kilogram (e.g., "25¢/kg", "15.5¢/kg")
        cents_kg_match = re.search(r'(\d+\.?\d*)¢?/kg', duty_rate)
        if cents_kg_match:
            return "cents_per_kg", float(cents_kg_match.group(1))
        
        # Dollars per unit (e.g., "$2.50/unit", "$1.25 each")
        dollar_unit_match = re.search(r'\$(\d+\.?\d*)', duty_rate)
        if dollar_unit_match:
            return "dollars_per_unit", float(dollar_unit_match.group(1))
        
        # Default to free if cannot parse
        return "free", 0.0
    
    def calculate_duty(self, product_info: ProductInfo) -> DutyCalculation:
        """Calculate duty for a product"""
        # Get HTS data
        hts_data = self.get_hts_data(product_info.hts_code)
        
        if not hts_data:
            return DutyCalculation(
                hts_code=product_info.hts_code,
                product_description="HTS code not found",
                cif_value=0,
                duty_rate="Unknown",
                duty_amount=0,
                total_landed_cost=0,
                duty_type="unknown",
                breakdown={}
            )
        
        # Calculate CIF value
        cif_value = product_info.cost + product_info.freight + product_info.insurance
        
        # Get duty rate
        duty_rate_str = hts_data.get('duty_rate', 'Free')
        duty_type, duty_value = self.parse_duty_rate(duty_rate_str)
        
        # Calculate duty amount
        duty_amount = self._calculate_duty_amount(
            duty_type, duty_value, cif_value, 
            product_info.quantity, product_info.unit_weight
        )
        
        # Calculate total landed cost
        total_landed_cost = cif_value + duty_amount
        
        # Create breakdown
        breakdown = {
            "product_cost": product_info.cost,
            "freight": product_info.freight,
            "insurance": product_info.insurance,
            "cif_value": cif_value,
            "duty_amount": duty_amount,
            "total_landed_cost": total_landed_cost
        }
        
        return DutyCalculation(
            hts_code=product_info.hts_code,
            product_description=hts_data.get('product_description', 'Unknown'),
            cif_value=cif_value,
            duty_rate=duty_rate_str,
            duty_amount=duty_amount,
            total_landed_cost=total_landed_cost,
            duty_type=duty_type,
            breakdown=breakdown
        )
    
    def _calculate_duty_amount(self, duty_type: str, duty_value: float, 
                             cif_value: float, quantity: int, 
                             unit_weight: float) -> float:
        """Calculate duty amount based on duty type"""
        if duty_type == "free":
            return 0.0
        elif duty_type == "percentage":
            return (duty_value / 100) * cif_value
        elif duty_type == "cents_per_kg":
            total_weight = quantity * unit_weight
            return (duty_value / 100) * total_weight  # Convert cents to dollars
        elif duty_type == "dollars_per_unit":
            return duty_value * quantity
        else:
            return 0.0
    
    def format_calculation_result(self, calculation: DutyCalculation) -> str:
        """Format calculation result as readable text"""
        return f"""
HTS Code: {calculation.hts_code}
Product: {calculation.product_description}

Cost Breakdown:
- Product Cost: ${calculation.breakdown['product_cost']:.2f}
- Freight: ${calculation.breakdown['freight']:.2f}
- Insurance: ${calculation.breakdown['insurance']:.2f}
- CIF Value: ${calculation.breakdown['cif_value']:.2f}

Duty Calculation:
- Duty Rate: {calculation.duty_rate}
- Duty Type: {calculation.duty_type}
- Duty Amount: ${calculation.duty_amount:.2f}

Total Landed Cost: ${calculation.total_landed_cost:.2f}
        """.strip()

if __name__ == "__main__":
    calculator = DutyCalculator()
    
    # Test calculation
    product = ProductInfo(
        hts_code="0101.21.00",
        cost=1000.0,
        freight=100.0,
        insurance=50.0,
        quantity=10,
        unit_weight=100.0
    )
    
    result = calculator.calculate_duty(product)
    print(calculator.format_calculation_result(result))