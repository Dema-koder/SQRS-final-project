import requests
import streamlit as st
from typing import Optional, List, Dict
import pandas as pd
API_URL = st.secrets["api_url"]

def login(username: str, password: str) -> str:
    """Authenticate and return a bearer token."""
    resp = requests.post(f"{API_URL}/token", data={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()["access_token"]

def register_user(username: str, email: str, password: str) -> None:
    """Register a new user."""
    resp = requests.post(f"{API_URL}/register", json={"username": username, "email": email, "password": password})
    resp.raise_for_status()

def get_headers() -> Dict[str, str]:
    """Return headers dict with current token."""
    return {"Authorization": f"Bearer {st.session_state.token}"}

def get_categories() -> List[Dict]:
    """Fetch list of categories."""
    resp = requests.get(f"{API_URL}/categories/", headers=get_headers())
    resp.raise_for_status()
    return resp.json()

def create_category(name: str, type_: str, is_predefined: bool = False) -> Dict:
    """Create a new category."""
    payload = {"name": name, "type": type_, "is_predefined": is_predefined}
    resp = requests.post(f"{API_URL}/categories/", headers=get_headers(), json=payload)
    resp.raise_for_status()
    return resp.json()

def get_summary(start: str, end: str, category_ids: Optional[List[int]] = None) -> Dict:
    """Fetch analytics summary."""
    params = {"start_date": start, "end_date": end}
    if category_ids:
        params["category_id"] = ",".join(map(str, category_ids))
    resp = requests.get(f"{API_URL}/analytics/summary", headers=get_headers(), params=params)
    resp.raise_for_status()
    return resp.json()

def get_transactions(start: str, end: str, category_ids: Optional[List[int]] = None) -> List[Dict]:
    """Fetch transactions list."""
    params = {"start_date": start, "end_date": end}
    if category_ids:
        params["category_id"] = ",".join(map(str, category_ids))
    resp = requests.get(f"{API_URL}/transactions/", headers=get_headers(), params=params)
    resp.raise_for_status()
    return resp.json()

def create_transaction(txn: Dict) -> Dict:
    """POST a new transaction."""
    resp = requests.post(f"{API_URL}/transactions/", headers=get_headers(), json=txn)
    resp.raise_for_status()
    return resp.json()

def update_transaction(txn_id: int, txn: Dict) -> Dict:
    """PATCH an existing transaction."""
    resp = requests.patch(f"{API_URL}/transactions/{txn_id}", headers=get_headers(), json=txn)
    resp.raise_for_status()
    return resp.json()

def delete_transaction(txn_id: int) -> None:
    """DELETE a transaction."""
    resp = requests.delete(f"{API_URL}/transactions/{txn_id}", headers=get_headers())
    resp.raise_for_status()
    
# ─── at the top with your other helpers ─────────────────────────────────────────

def refresh_data(
    start_iso: str,
    end_iso:   str,
    selected_names: Optional[List[str]] = None
) -> Dict:
    """
    Fetch categories, summary, and transactions in one shot.
    Returns a dict with:
      - category_map, id_to_category, categories, categories_by_type
      - summary (dict)
      - df (DataFrame of transactions, with Date, Amount, Category columns)
    """
    cats = get_categories()
    category_map   = {c["name"]: c["id"]   for c in cats}
    id_to_category = {c["id"]:   c["name"] for c in cats}
    categories     = list(category_map.keys())

    categories_by_type = {"income": [], "expense": []}
    for c in cats:
        categories_by_type[c["type"]].append(c["name"])

    sel_ids = [category_map[n] for n in selected_names] if selected_names else None

    summary = get_summary(start_iso, end_iso, sel_ids)

    txns = get_transactions(start_iso, end_iso, sel_ids)
    df = pd.DataFrame(txns)
    if not df.empty:
        df["Date"]     = pd.to_datetime(df["date"])
        df["Amount"]   = df["amount"]
        df["Category"] = df["category_id"].map(id_to_category)

    return {
        "category_map":       category_map,
        "id_to_category":     id_to_category,
        "categories":         categories,
        "categories_by_type": categories_by_type,
        "summary":            summary,
        "df":                 df
    }
