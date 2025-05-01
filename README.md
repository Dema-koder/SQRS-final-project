```commandline
cd backend 
poetry install
poetry run uvicorn finance_tracker.main:app --reload
```


```commandline
cd frontend
poetry install
poetry run streamlit run src/personal_finance_tracker_front/main.py
```

frontend: http://localhost:8501
api: http://127.0.0.1:8000/docs