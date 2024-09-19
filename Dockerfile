# Use an official Python image as the base
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the Poetry files first to leverage Docker caching for dependencies
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the application
COPY . .

# Command to run the application (adjust to your project’s needs)
# CMD ["poetry", "run", "python", "run.py"]
ENTRYPOINT ["python", "-m"]