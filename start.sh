#!/bin/bash

# Instalar dependências
pip install -r requirements.txt

# Iniciar Streamlit com configurações para Render
streamlit run app.py \
  --server.headless true \
  --server.port $PORT \
  --server.address 0.0.0.0 \
  --server.enableCORS false \
  --server.enableXsrfProtection false
