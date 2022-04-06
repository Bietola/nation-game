FROM python:3.10.0

# Update apt
RUN apt-get update -y
RUN apt-get upgrade -y

# Install Poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="/root/.local/bin:$PATH"

# Packages used by poetry dependencies
RUN apt-get install -y graphviz

# Install dependencies with poetry
COPY . /app
WORKDIR /app/nation_game
RUN poetry install

# Should be started in interactive shell using `docker run -it nation-game`
# CMD poetry run python main.py
CMD bash
