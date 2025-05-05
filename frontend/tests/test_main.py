import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from personal_finance_tracker_front import main


@pytest.fixture
def mock_streamlit():
    with patch("personal_finance_tracker_front.main.st") as mocked_st:
        mocked_st.session_state = MagicMock()
        mocked_st.session_state.get.return_value = "mock_token"
        mocked_st.session_state.__getitem__.side_effect = (
            lambda key: "income" if key == "current_category" else MagicMock()
        )
        mocked_st.form.return_value.__enter__.return_value = MagicMock()
        mocked_st.container.return_value = MagicMock()
        mocked_st.success = MagicMock()
        mocked_st.warning = MagicMock()
        mocked_st.error = MagicMock()
        mocked_st.markdown = MagicMock()
        mocked_st.radio.return_value = "Login"
        mocked_st.button.return_value = False

        def selectbox_side_effect(label, options, *args, **kwargs):
            if "Type" in label:
                return "expense"
            elif "Category" in label:
                return "Food"
            elif "Category Type" in label:
                return "expense"
            return "expense"

        def text_input_side_effect(label, *args, **kwargs):
            if "Category Name" in label:
                return ""
            elif "Description" in label:
                return "Lunch"
            return ""

        mocked_st.selectbox.side_effect = selectbox_side_effect
        mocked_st.text_input.side_effect = text_input_side_effect

        def tabs_side_effect(tab_names):
            return tuple(MagicMock() for _ in range(len(tab_names)))

        def columns_side_effect(spec):
            num_cols = spec if isinstance(spec, int) else len(spec)
            return [MagicMock() for _ in range(num_cols)]

        mocked_st.tabs.side_effect = tabs_side_effect
        mocked_st.columns.side_effect = columns_side_effect
        mocked_st.date_input.side_effect = [
            datetime(2025, 1, 1),  # Start Date (Overview)
            datetime(2025, 1, 31),  # End Date (Overview)
            datetime(2025, 1, 1),  # Transaction Date (Create)
            datetime(2025, 1, 1),  # Transaction Date (Edit)
        ]
        mocked_st.checkbox.return_value = True
        mocked_st.number_input.return_value = 100.0
        mocked_st.form_submit_button.return_value = True
        yield mocked_st


@pytest.fixture
def mock_api():
    with patch("personal_finance_tracker_front.main.api") as mocked_api:
        mocked_api.get_headers.return_value = {
            "Authorization": "Bearer mock_token"
        }
        mocked_api.get_categories.return_value = [
            {
                "id": 1,
                "name": "Food",
                "type": "expense",
                "is_predefined": True,
                "user_id": None,
            },
            {
                "id": 2,
                "name": "Salary",
                "type": "income",
                "is_predefined": True,
                "user_id": None,
            },
        ]
        mocked_api.get_summary.return_value = {
            "total_income": 1000.0,
            "total_expenses": 800.0,
            "net_balance": 200.0,
            "expenses_by_category": [{"name": "Food", "total": 500.0}],
        }
        mocked_api.get_transactions.return_value = [
            {
                "id": 1,
                "category_id": 1,
                "type": "expense",
                "amount": 100.0,
                "date": "2025-01-01",
                "description": "Lunch",
                "is_recurring": False,
            },
        ]
        mocked_api.create_category.return_value = {
            "id": 3,
            "name": "New Category",
            "type": "expense",
            "is_predefined": False,
            "user_id": 1,
        }
        yield mocked_api


def test_category_mapping(mock_api):
    cats = mock_api.get_categories()
    category_map = {c["name"]: c["id"] for c in cats}
    id_to_category = {c["id"]: c["name"] for c in cats}
    categories = list(category_map.keys())
    categories_by_type = {"income": [], "expense": []}
    for c in cats:
        categories_by_type[c["type"]].append(c["name"])

    assert category_map == {"Food": 1, "Salary": 2}
    assert id_to_category == {1: "Food", 2: "Salary"}
    assert categories == ["Food", "Salary"]
    assert categories_by_type == {"income": ["Salary"], "expense": ["Food"]}


def test_create_transaction_payload(mock_streamlit, mock_api):
    mock_streamlit.session_state.get.return_value = "mock_token"
    mock_streamlit.selectbox.side_effect = ["expense", "Food"]
    mock_streamlit.number_input.return_value = 100.0
    mock_streamlit.text_input.return_value = "Lunch"
    mock_streamlit.date_input.return_value = datetime(2025, 1, 1)
    mock_streamlit.checkbox.return_value = False
    mock_streamlit.form_submit_button.return_value = True

    mock_streamlit.session_state.__getitem__.return_value = "expense"
    mock_streamlit.session_state.__setitem__.return_value = None

    category_map = {"Food": 1, "Salary": 2}

    with patch(
        "personal_finance_tracker_front.main.api.create_transaction"
    ) as mock_create:
        c_type = "expense"
        c_amount = 100.0
        c_description = "Lunch"
        c_date = datetime(2025, 1, 1)
        c_category = "Food"
        c_is_recurring = False
        txn = {
            "type": c_type,
            "amount": c_amount,
            "description": c_description,
            "date": c_date.isoformat(),
            "category_id": category_map[c_category],
            "is_recurring": c_is_recurring,
        }
        mock_create(txn)

    mock_create.assert_called_once_with({
        "type": "expense",
        "amount": 100.0,
        "description": "Lunch",
        "date": "2025-01-01T00:00:00",
        "category_id": 1,
        "is_recurring": False,
    })


def test_no_transactions_warning(mock_streamlit, mock_api):
    mock_streamlit.session_state.get.return_value = "mock_token"
    mock_api.get_transactions.return_value = []  # No transactions

    with patch(
        "personal_finance_tracker_front.main.st.warning"
    ) as mock_warning:
        main.main_app()
        mock_warning.assert_called_once_with("No transactions to manage.")
