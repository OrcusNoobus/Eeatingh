"""
Serviciu de procesare comenzi - Functii pentru parsarea si salvarea comenzilor.
"""

import json
import os
import re
import unicodedata
from datetime import datetime
from typing import Optional, Dict
from bs4 import BeautifulSoup
import locale

from app.config import COMENZI_NOI, COMENZI_PROCESATE, COMENZI_ANULATE
from app.logging_config import get_logger

logger = get_logger("order_service")


def remove_diacritics(text: str) -> str:
    """
    Remove diacritics from Romanian text.
    
    Args:
        text: String with diacritics
        
    Returns:
        String without diacritics
    """
    if not text:
        return text
    
    # Normalize to NFD (decomposed form) and filter out combining characters
    nfd = unicodedata.normalize('NFD', text)
    without_diacritics = ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')
    
    return without_diacritics


def parse_romanian_date(date_str: str) -> str:
    """
    Parse Romanian date format from forwarded email and convert to YYYY-MM-DD HH:MM:SS.
    
    Args:
        date_str: Date string in Romanian format (e.g., "sâm., 1 nov. 2025 la 18:05")
        
    Returns:
        Date string in format YYYY-MM-DD HH:MM:SS, or current timestamp if parsing fails
    """
    try:
        # Romanian month abbreviations mapping
        ro_months = {
            'ian.': 1, 'feb.': 2, 'mar.': 3, 'apr.': 4, 'mai': 5, 'iun.': 6,
            'iul.': 7, 'aug.': 8, 'sep.': 9, 'oct.': 10, 'nov.': 11, 'dec.': 12
        }
        
        # Remove day name and clean up (e.g., "sâm., 1 nov. 2025 la 18:05" -> "1 nov. 2025 la 18:05")
        date_str_clean = re.sub(r'^[a-zăâîșț]+\.,?\s*', '', date_str.strip(), flags=re.IGNORECASE)
        
        # Extract components: day, month, year, time
        # Pattern: "1 nov. 2025 la 18:05" or similar variations
        match = re.search(r'(\d{1,2})\s+([a-zăâîșț]+\.?)\s+(\d{4})(?:\s+la\s+)?(\d{1,2}):(\d{2})', date_str_clean, re.IGNORECASE)
        
        if match:
            day = int(match.group(1))
            month_str = match.group(2).lower()
            year = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            
            # Get month number
            month = ro_months.get(month_str, None)
            
            if month:
                # Create datetime object
                dt = datetime(year, month, day, hour, minute, 0)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # If parsing fails, return current timestamp
        logger.warning(f"Could not parse date '{date_str}', using current timestamp")
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    except Exception as e:
        logger.error(f"Error parsing date '{date_str}': {e}")
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_order_html(html_doc: str) -> Optional[Dict]:
    """
    Extract order data from HTML document or JSON and return as a dictionary.
    
    Args:
        html_doc: String with email HTML content or JSON data
        
    Returns:
        Dict with order data in format {"comanda": {...}} or None if parsing fails
    """
    try:
        # First, try to parse as JSON (new format)
        # New format: {"comenzi": [{"comanda": {...}}], "message": "...", "total": 1}
        try:
            json_data = json.loads(html_doc)
            
            # Check if it has the expected structure
            if isinstance(json_data, dict) and 'comenzi' in json_data:
                comenzi_list = json_data['comenzi']
                
                if isinstance(comenzi_list, list) and len(comenzi_list) > 0:
                    # Extract the first order from the array
                    first_order = comenzi_list[0]
                    
                    # Verify it has the "comanda" key
                    if isinstance(first_order, dict) and 'comanda' in first_order:
                        logger.info(f"✅ JSON parsare reușită - comandă extractă din wrapper")
                        # Return the order in the expected format {"comanda": {...}}
                        return first_order
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
            # Not JSON or invalid structure, continue with HTML parsing
            logger.debug("Input nu este JSON valid sau nu are structura așteptată, încerc parsare HTML...")
            pass
        
        # If JSON parsing failed or was not applicable, proceed with HTML parsing (legacy format)
        soup = BeautifulSoup(html_doc, 'html.parser')
        
        # Initialize order data dictionary in EXACT order from model_comanda_json.txt
        # This order MUST be preserved to match the target JSON structure
        order_data = {
            "id_intern_comanda": None,
            "simbol_monetar": "RON",
            "email_client": "",
            "numar_telefon_client": None,
            "nume_client": None,
            "cartier": "",
            "tip_comanda": "livrare",
            "adresa_livrare_client": None,
            "valoare_comanda": None,
            "discounturi": [],
            "status_comanda": "processing",
            "mod_plata": None,
            "observatii_comanda": "",
            "data_comanda": None,
            "produse_comanda": []
        }
        
        # 1. Extract order ID
        order_id_tag = soup.find('td', string=re.compile(r'Comanda #|Comandă #'))
        if order_id_tag:
            order_data["id_intern_comanda"] = order_id_tag.text.split('#')[1].strip()
        else:
            logger.error("Order ID not found in HTML")
            return None

        # 2. Extract order date from "Forwarded message" section
        # Look for "Date:" line in the forwarded message header
        forwarded_section = soup.find(string=re.compile(r'Forwarded message|Date:', re.IGNORECASE))
        date_found = False
        
        if forwarded_section:
            # Search in the parent and siblings for Date: line
            parent = forwarded_section.parent
            if parent:
                # Look through all text in the parent and nearby elements
                for elem in parent.find_all(string=True):
                    if 'Date:' in elem:
                        # Extract the date part after "Date:"
                        date_match = re.search(r'Date:\s*(.+)', elem, re.IGNORECASE)
                        if date_match:
                            date_str = date_match.group(1).strip()
                            order_data["data_comanda"] = parse_romanian_date(date_str)
                            date_found = True
                            break
        
        # Fallback: search for Date: anywhere in the HTML
        if not date_found:
            all_text = soup.get_text()
            date_match = re.search(r'Date:\s*(.+?)(?:\n|$)', all_text, re.IGNORECASE)
            if date_match:
                date_str = date_match.group(1).strip()
                order_data["data_comanda"] = parse_romanian_date(date_str)
            else:
                # Last resort: use current timestamp
                order_data["data_comanda"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 3. Extract client data, delivery address and notes
        delivery_header = soup.find('td', string='Adresa de livrare:')
        if delivery_header:
            delivery_table = delivery_header.find_parent('table')
            info_tags = delivery_table.find_all('td', style=re.compile(r"font-family.*Roboto Condensed", re.IGNORECASE))
            text_tags = [tag for tag in info_tags if tag.text.strip() and not tag.text.strip().startswith('Adresa')]
            
            if len(text_tags) >= 3:
                order_data["nume_client"] = remove_diacritics(text_tags[0].text.strip())
                order_data["numar_telefon_client"] = text_tags[1].text.strip()
                address_text = text_tags[2].text.strip()
                order_data["adresa_livrare_client"] = remove_diacritics(re.sub(r'\s+', ' ', address_text))
            
            # Extract order notes
            message_header_tag = delivery_table.find('td', string='Mesaj:')
            if message_header_tag:
                message_row = message_header_tag.find_parent('tr').find_next_sibling('tr')
                if message_row:
                    message_tag = message_row.find('td')
                    if message_tag:
                        order_data["observatii_comanda"] = remove_diacritics(message_tag.text.strip())

        # 4. Extract payment method
        payment_header = soup.find('td', string='Plata:')
        if payment_header:
            payment_table = payment_header.find_parent('table')
            payment_method_tag = payment_table.find('td', style=re.compile(r'font-weight:700'))
            if payment_method_tag:
                payment_text = payment_method_tag.text.strip().lower()
                if 'numerar' in payment_text or 'cash' in payment_text:
                    order_data["mod_plata"] = "CASH"
                elif 'pos' in payment_text or 'card' in payment_text:
                    order_data["mod_plata"] = "CARD"
                elif 'online' in payment_text:
                    order_data["mod_plata"] = "ONLINE"
                else:
                    order_data["mod_plata"] = "CASH"

        # 5. Extract total value
        total_tag = soup.find('td', string=lambda text: text and 'TOTAL:' in text.upper() if text else False)
        if not total_tag:
            for td in soup.find_all('td'):
                if td.text and 'TOTAL:' in td.text.upper():
                    total_tag = td
                    break
        
        if total_tag:
            all_numbers = re.findall(r'(\d+\.\d{2})', total_tag.text)
            if all_numbers:
                order_data["valoare_comanda"] = all_numbers[-1]

        # 6. Extract products
        if order_id_tag:
            products_table = order_id_tag.find_parent('table').find('table')
            if products_table:
                product_rows = products_table.find_all('tr')
                for row in product_rows:
                    cols = row.find_all('td')
                    if len(cols) == 3:
                        name = remove_diacritics(cols[0].text.strip())
                        quantity_match = re.search(r'(\d+)', cols[1].text.strip())
                        quantity = int(quantity_match.group(1)) if quantity_match else 0
                        price_match = re.search(r'(\d+\.\d{2})', cols[2].text.strip())
                        price = price_match.group(1) if price_match else "0.00"
                        
                        # Product dictionary in EXACT order from model_comanda_json.txt
                        product_item = {
                            "id_produs": name,
                            "denumire_produs": name,
                            "cantitate_produs": quantity,
                            "pret_produs": price,
                            "id_intern_comanda": order_data["id_intern_comanda"],
                            "observatii_produs": "",
                            "extra": []
                        }
                        order_data["produse_comanda"].append(product_item)
        
        # Validate required data
        if not order_data["id_intern_comanda"]:
            logger.error("Order ID missing")
            return None
        
        # Wrap order data under "comanda" key as per JSON model requirement
        return {"comanda": order_data}
        
    except Exception as e:
        logger.error(f"Error parsing HTML: {e}", exc_info=True)
        return None


def save_order_json(order_data: Dict, output_folder = COMENZI_NOI) -> bool:
    """
    Save order data to a JSON file.
    
    Args:
        order_data: Dictionary with order data (wrapped in "comanda" key)
        output_folder: Folder where JSON is saved (default: comenzi/noi)
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
        
        # Extract order ID from wrapped structure
        order_id = order_data["comanda"]["id_intern_comanda"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_folder / f"{timestamp}_comanda_{order_id}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(order_data, f, indent=4, ensure_ascii=False, sort_keys=False)
        
        logger.info(f"Order #{order_id} saved: {filename.name}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving JSON: {e}", exc_info=True)
        return False


def is_order_processed(order_id: str) -> bool:
    """
    Check if an order has already been processed.
    
    Args:
        order_id: Order ID
        
    Returns:
        True if order was already processed, False otherwise
    """
    folders = [COMENZI_NOI, COMENZI_PROCESATE, COMENZI_ANULATE]
    
    for folder in folders:
        if folder.exists():
            for filename in os.listdir(folder):
                if filename.endswith('.json') and f"comanda_{order_id}.json" in filename:
                    logger.info(f"Order #{order_id} already processed")
                    return True
    
    return False
