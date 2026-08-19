import re
import pandas as pd
from typing import Dict, Any, Tuple, Optional

def clean_text(text: Any) -> str:
    """Clean and standardise input text."""
    if text is None or pd.isna(text):
        return ""
    # Convert to string and strip whitespace
    text_str = str(text).strip()
    # Replace multiple spaces/newlines with single ones
    text_str = re.sub(r'[ \t]+', ' ', text_str)
    return text_str

def validate_csv(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate that the uploaded CSV contains useful prospect information.
    Returns (is_valid, error_message).
    """
    if df.empty:
        return False, "The uploaded CSV file is empty."
    
    # Check for any of the columns that can build a profile
    potential_columns = [
        "profile", "name", "job_title", "company", 
        "company_description", "website", "linkedin"
    ]
    
    # Find which of these columns exist in the DataFrame
    existing_cols = [col for col in potential_columns if col in df.columns]
    
    if not existing_cols:
        return False, (
            "Your CSV does not contain enough prospect information. "
            "Please include a 'profile' column or fields such as name, job_title, "
            "company, or company_description."
        )
    
    # Check if there is at least one row with non-empty values in these columns
    non_empty_rows = df[existing_cols].dropna(how="all")
    if non_empty_rows.empty:
        return False, "All rows in the prospect information columns are empty."
        
    return True, ""

def build_profile(row: Dict[str, Any]) -> str:
    """
    Intelligently combine available fields into a single profile string if 'profile' is missing.
    """
    # Clean keys for robust lookups (case-insensitive, strip whitespace)
    row_clean = {str(k).strip().lower(): v for k, v in row.items()}
    
    # If explicit 'profile' column exists and is not empty, use it directly
    if 'profile' in row_clean and row_clean['profile'] and not pd.isna(row_clean['profile']):
        p_val = clean_text(row_clean['profile'])
        if p_val:
            return p_val
            
    # Otherwise, combine existing columns into a coherent profile description
    parts = []
    
    name = clean_text(row_clean.get('name'))
    job_title = clean_text(row_clean.get('job_title'))
    company = clean_text(row_clean.get('company'))
    company_desc = clean_text(row_clean.get('company_description') or row_clean.get('company_desc'))
    website = clean_text(row_clean.get('website'))
    linkedin = clean_text(row_clean.get('linkedin'))
    
    if name:
        parts.append(f"Name: {name}")
    if job_title:
        parts.append(f"Job Title: {job_title}")
    if company:
        parts.append(f"Company: {company}")
    if company_desc:
        parts.append(f"Company Description: {company_desc}")
    if website:
        parts.append(f"Website: {website}")
    if linkedin:
        parts.append(f"LinkedIn Profile: {linkedin}")
        
    return "\n".join(parts)

def safe_filename(base: str, ext: str = "csv") -> str:
    """Generate a clean, safe filename."""
    # Remove non-alphanumeric characters except underscore/hyphen
    clean_base = re.sub(r'[^a-zA-Z0-9_\-]', '_', base)
    return f"{clean_base}.{ext}"

def validate_sender_info(name: str, company: str, role: str, product: str, website: str) -> str:
    """
    Format sender information if any is provided.
    If none is provided, returns 'No sender information provided.'
    """
    parts = []
    if name.strip():
        parts.append(f"Name: {name.strip()}")
    if company.strip():
        parts.append(f"Company: {company.strip()}")
    if role.strip():
        parts.append(f"Role: {role.strip()}")
    if product.strip():
        parts.append(f"Product/Service: {product.strip()}")
    if website.strip():
        parts.append(f"Website: {website.strip()}")
        
    if not parts:
        return "No sender information provided. Do not invent any sender details."
    return "\n".join(parts)
