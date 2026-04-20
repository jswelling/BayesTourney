FROM python:3.9-slim

RUN groupadd -r flaskgroup && useradd -r -g flaskgroup -m flaskuser

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gcc graphviz libgraphviz-dev pkg-config python3-dev

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chown -R flaskuser:flaskgroup /app

USER flaskuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "bayestourney:create_app()"]