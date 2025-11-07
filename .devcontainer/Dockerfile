# Devcontainer Dockerfile for NYML
FROM mcr.microsoft.com/devcontainers/base:ubuntu

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    build-essential \
    python3 \
    python3-venv \
    python3-pip \
  && rm -rf /var/lib/apt/lists/*

# Install Node.js 20 (LTS)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get update \
  && apt-get install -y --no-install-recommends nodejs \
  && rm -rf /var/lib/apt/lists/*

# Enable corepack (bundled with modern Node) and activate yarn
RUN corepack enable \
  && corepack prepare yarn@stable --activate || true

# Create workspace directory and switch to non-root user
RUN mkdir -p /workspaces/nyml && chown -R vscode:vscode /workspaces

USER vscode
WORKDIR /workspaces/nyml

CMD ["sleep", "infinity"]
