FROM python:3.10.0

# Update apt
RUN apt-get update -y
RUN apt-get upgrade -y

# Install Poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="/root/.local/bin:$PATH"

# Packages used by poetry dependencies
RUN apt-get install -y graphviz
# Interactive command line dependencies
RUN apt-get install -y screen

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

# Project initialization:
# NB. Virtual env isn't needed as docker image is already isolated
RUN poetry config virtualenvs.create false \
&& poetry install --no-interaction --no-ansi

# Create folders, and files for the project
COPY . /code

# To install `nation-game` module (pip deps installed in first poetry pass)
RUN poetry install --no-interaction --no-ansi

# Should be started in interactive shell using `docker run -it nation-game`
# CMD poetry run python main.py
CMD PATH="/code/nation_game/bin/docker:$PATH" bash
