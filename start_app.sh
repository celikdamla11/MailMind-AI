#!/bin/bash
cd /Users/damlacelik/Desktop/FlRAGProject
/Users/damlacelik/Desktop/FlRAGProject/.venv/bin/python -m streamlit run app_ui.py --server.headless=true &
sleep 2
open http://localhost:8501