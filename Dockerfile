FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY streamlit_app.py .
COPY .streamlit .streamlit
RUN mkdir -p /data
ENV VOICEBRIDGE_DB=/data/voicebridge.sqlite
EXPOSE 3000
CMD ["streamlit","run","streamlit_app.py","--server.address=0.0.0.0","--server.port=3000","--server.headless=true"]
