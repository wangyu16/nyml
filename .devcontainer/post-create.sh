#!/usr/bin/env bash
set -euo pipefail
echo "[devcontainer] Running post-create script"

# Install Python requirements if present (user install to avoid system dirs)
if [ -f requirements.txt ]; then
  echo "[devcontainer] Installing Python requirements from requirements.txt"
  python3 -m pip install --user -r requirements.txt
fi

# Install Node dependencies if package.json exists
if [ -f package.json ]; then
  echo "[devcontainer] Installing Node dependencies (npm install)"
  # prefer yarn if yarn.lock exists
  if [ -f yarn.lock ]; then
    yarn install --frozen-lockfile || npm install
  else
    npm install || true
  fi
fi

# Create a virtual environment if not present
if [ ! -d .venv ]; then
  echo "[devcontainer] Creating Python virtual environment at .venv"
  python3 -m venv .venv || true
fi

echo "[devcontainer] Post-create finished"
