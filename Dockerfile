FROM node:20-bullseye

WORKDIR /work

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    openjdk-17-jre \
    pandoc \
    locales \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

RUN wget https://github.com/quarto-dev/quarto-cli/releases/download/v1.9.36/quarto-1.9.36-linux-arm64.deb \
    && apt-get update \
    && apt-get install -y ./quarto-1.9.36-linux-arm64.deb \
    && rm quarto-1.9.36-linux-arm64.deb

RUN quarto install tinytex --update-path