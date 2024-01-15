# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10-slim


EXPOSE 5002

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

# System dependencies and poppler-utils
RUN apt-get update && apt-get install -y poppler-utils curl graphviz && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install mitreattack-python & poetry
RUN pip install mitreattack-python
RUN pip install poetry

# Set working directory
WORKDIR /app

# Copy the necessary parts of your app into the container
COPY venv/app/src/attack_flow /app/src/attack_flow

# Copy pyproject.toml and poetry.lock from /app into the working directory
COPY venv/app/pyproject.toml ./app/poetry.lock* /app/

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction

# Copy the rest of the application files into the container
COPY . /app


# Removing non-root user for project simplicity

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
# RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
# USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["/bin/bash"]
