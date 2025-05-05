import requests
import streamlit as st
from typing import Optional, List, Dict
API_URL = st.secrets["api_url"]


def login(username: str, password: str) -> str:
    """Authenticate and return a bearer token."""
    resp = requests.post(f"{API_URL}/token",
                         data={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()["access_token"]


def register_user(username: str, email: str, password: str) -> None:
    """Register a new user."""
    resp = requests.post(f"{API_URL}/register",
                         json={"username": username,
                               "email": email,
                               "password": password
                               })
    resp.raise_for_status()


def get_headers() -> Dict[str, str]:
    """Return headers dict with current token."""
    return {"Authorization": f"Bearer {st.session_state.token}"}


def get_categories() -> List[Dict]:
    """Fetch list of categories."""
    resp = requests.get(f"{API_URL}/categories/", headers=get_headers())
    resp.raise_for_status()
    return resp.json()


def create_category(name: str,
                    type_: str,
                    is_predefined: bool = False) -> Dict:
    """Create a new category."""
    payload = {"name": name,
               "type": type_,
               "is_predefined": is_predefined}
    resp = requests.post(f"{API_URL}/categories/",
                         headers=get_headers(),
                         json=payload)
    resp.raise_for_status()
    return resp.json()


def get_summary(start: str,
                end: str,
                category_ids: Optional[List[int]] = None) -> Dict:
    """Fetch analytics summary."""
    params = {"start_date": start, "end_date": end}
    if category_ids:
        params["category_id"] = ",".join(map(str, category_ids))
    resp = requests.get(f"{API_URL}/analytics/summary",
                        headers=get_headers(),
                        params=params)
    resp.raise_for_status()
    return resp.json()


def get_transactions(start: str,
                     end: str,
                     category_ids: Optional[List[int]] = None) -> List[Dict]:
    """Fetch transactions list."""
    params = {"start_date": start, "end_date": end}
    if category_ids:
        params["category_id"] = ",".join(map(str, category_ids))
    resp = requests.get(f"{API_URL}/transactions/",
                        headers=get_headers(),
                        params=params)
    resp.raise_for_status()
    return resp.json()


def create_transaction(txn: Dict) -> Dict:
    """POST a new transaction."""
    resp = requests.post(f"{API_URL}/transactions/",
                         headers=get_headers(),
                         json=txn)
    resp.raise_for_status()
    return resp.json()


def update_transaction(txn_id: int, txn: Dict) -> Dict:
    """PATCH an existing transaction."""
    resp = requests.patch(f"{API_URL}/transactions/{txn_id}",
                          headers=get_headers(),
                          json=txn)
    resp.raise_for_status()
    return resp.json()


def delete_transaction(txn_id: int) -> None:
    """DELETE a transaction."""
    resp = requests.delete(f"{API_URL}/transactions/{txn_id}",
                           headers=get_headers())
    resp.raise_for_status()
