FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

WORKDIR /opt

RUN apt-get update && apt-get -y upgrade 

ADD . .

RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# streamlit
EXPOSE 8501

WORKDIR /opt/NER

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]