# Makefile for Shipping Rate Streamlit Application

# Define variables
APP_NAME = shipping-rate-streamlit-app
DOCKER_IMAGE = $(APP_NAME):latest
DOCKER_COMPOSE = docker-compose.yml
PYTHON = python3
# Default target
.PHONY: all
all: build

# Build the Docker image
.PHONY: build
build:
	docker build -t $(DOCKER_IMAGE) .

# Run the application using Docker Compose
.PHONY: run
run:
	docker-compose up

# Clean up Docker containers and images
.PHONY: clean
clean:
	docker-compose down
	docker rmi $(DOCKER_IMAGE)

# Push the Docker image to a registry (example: Docker Hub)
.PHONY: push
push:
	docker push $(DOCKER_IMAGE)

# Help command
.PHONY: help
help:
	@echo "Makefile commands:"
	@echo "  build      - Build the Docker image"
	@echo "  run        - Run the application using Docker Compose"
	@echo "  clean      - Clean up Docker containers and images"
	@echo "  push       - Push the Docker image to a registry"
	@echo "  help       - Show this help message"