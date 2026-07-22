FROM node:20-bullseye

WORKDIR /work

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    unzip \
    openjdk-17-jre \
    pandoc \
    libreoffice-impress \
    locales \
    fonts-noto-cjk \
    libgbm1 \
    libxkbcommon0 \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen

ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

ARG TARGETARCH

RUN if [ "$TARGETARCH" = "amd64" ]; then \
        QUARTO_ARCH="amd64"; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
        QUARTO_ARCH="arm64"; \
    else \
        echo "Unsupported architecture: $TARGETARCH" && exit 1; \
    fi \
    && wget https://github.com/quarto-dev/quarto-cli/releases/download/v1.9.36/quarto-1.9.36-linux-${QUARTO_ARCH}.deb \
    && apt-get update \
    && apt-get install -y --no-install-recommends ./quarto-1.9.36-linux-${QUARTO_ARCH}.deb \
    && rm quarto-1.9.36-linux-${QUARTO_ARCH}.deb \
    && rm -rf /var/lib/apt/lists/*

RUN quarto install chrome-headless-shell --no-prompt

RUN pip3 install --no-cache-dir python-pptx Pillow


RUN libreoffice --version || soffice --version
