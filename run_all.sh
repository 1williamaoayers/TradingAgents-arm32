#!/bin/bash
echo "================================"

# 使用 web/app.py 作为主入口
exec streamlit run web/app.py --server.port 8501 --server.address 0.0.0.0
