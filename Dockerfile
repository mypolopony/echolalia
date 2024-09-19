# Use an official Python image as the base
FROM python:3.11-slim as base

#########
# Stage 0: Base
#########
 
# Set the working directory in the container
WORKDIR /app

# Copy the Poetry files first to leverage Docker caching for dependencies
COPY pyproject.toml poetry.lock ./

# Copy the rest of the application
COPY . .

# Install Poetry
RUN pip install poetry

# Install dependencies, without using a virtual environment
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

##########
# Stage 1, Debugger: This allows for debugging from the host within in the container
##########

FROM base as debugger

# Install the debugpy package
RUN pip install debugpy

# Open up the port (is this better than using it in the docker run command?)
EXPOSE 5678

ENTRYPOINT = ["python", "-m", "debugpy", "--listen", "0:0:0:0:5678", "-m"]

#########
# Stage 2, Primary: This is the primary image that will be used for running the application
#########

FROM base as primary

# Command to run the application (adjust to your project’s needs)
ENTRYPOINT ["python", "-m"]