FROM node:20-bullseye

WORKDIR /work

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    openjdk-17-jre \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/quarto-dev/quarto-cli/releases/download/v1.9.36/quarto-1.9.36-linux-arm64.deb \
    && apt-get update \
    && apt-get install -y ./quarto-1.9.36-linux-arm64.deb \
    && rm quarto-1.9.36-linux-arm64.deb