# agent/tools/filter_csv.py – WERSJA OGÓLNA
import csv
import io
from typing import Dict, List


def filter_csv(csv_text: str, filters: dict) -> List[Dict[str, str]]:
    reader = csv.DictReader(io.StringIO(csv_text))
    results = []
    
    for row in reader:
        match = True
        
        # === OGÓLNE PARSOWANIE DAT DLA _min/_max ===
        for key, value in filters.items():
            if key.endswith('_min') or key.endswith('_max'):
                col_base = key.replace('_min', '').replace('_max', '')
                col_value = row.get(col_base, '')
                
                # Spróbuj wyciągnąć rok z różnych formatów
                year = extract_year(col_value)
                filter_val = int(value)
                
                if key.endswith('_min') and year and year < filter_val:
                    match = False
                if key.endswith('_max') and year and year > filter_val:
                    match = False
                continue
            
            # Reszta filtrów jak dotychczas
            if str(value).lower().strip() not in row.get(key, '').lower().strip():
                match = False
                break
        
        if match:
            results.append(row)
    
    return results

def extract_year(text: str) -> int | None:
    """Wyciąga rok z 'YYYY-MM-DD', 'DD.MM.YYYY', '1986', etc."""
    import re
    match = re.search(r'\b(19|20)\d{2}\b', text)
    return int(match.group(0)) if match else None

