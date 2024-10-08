# Use an official Python image as the base
FROM python:3.11-slim as base

#########
# Stage 0: Base
#########
 
# Set the working directory in the container
WORKDIR /app

# Copy the rest of the application
COPY . .

# Install Poetry
RUN pip install poetry

# Install dependencies, without using a virtual environment
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

# Copy the Poetry files first to leverage Docker caching for dependencies
COPY pyproject.toml poetry.lock ./

##########
# Stage 1, Debugger: This allows for debugging from the host within the container
##########

FROM base as debugger

# Set the working directory in the container (again)
WORKDIR /app

# Set the environment variable to avoid frozen modules warning
ENV PYDEVD_DISABLE_FILE_VALIDATION=1

# Install the debugpy package
RUN pip install debugpy

# Open up the port for debugging
EXPOSE 5678

# ENTRYPOINT to start the debugger at a specific entrypoint
ENTRYPOINT ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client"]

#########
# Stage 2, Primary: This is the primary image that will be used for running the application
#########

FROM base as primary

# Set the working directory explicitly (for clarity)
WORKDIR /app

# Command to run the application
ENTRYPOINT ["python", "-m"]