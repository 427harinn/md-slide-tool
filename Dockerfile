FROM node:20-bullseye

WORKDIR /work

# Chromeインストール
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    fonts-noto \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Marp CLI
RUN npm install -g @marp-team/marp-cli