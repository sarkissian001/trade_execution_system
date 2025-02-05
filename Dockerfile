FROM python:3.9-slim

WORKDIR /app

# install pg tools and poetry
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    curl -sSL https://install.python-poetry.org | python3

# add poetry to PATH
ENV PATH="/root/.local/bin:${PATH}"

COPY pyproject.toml poetry.lock* ./

# install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install && poetry add psycopg2-binary

COPY . .

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]