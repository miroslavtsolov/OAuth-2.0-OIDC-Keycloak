#!/usr/bin/env bash
set -euo pipefail

echo "# Updating apt and installing prerequisites"
sudo apt update
sudo apt install -y ca-certificates curl gnupg python3.12-venv

echo "# Adding Docker's official GPG key"
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "# Adding Docker apt repository"
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "# Installing Docker"
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "# Verifying installation with hello-world..."
sudo docker run hello-world

read -p "Add current user ($USER) to the docker group" ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
  sudo usermod -aG docker "$USER"
  echo "Added $USER to docker"
fi
