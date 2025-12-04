#!/bin/bash

# Script para instalar Chrome/Chromium no Render.com

echo "🔧 Instalando dependências do Chrome..."

# Atualizar repositórios
apt-get update

# Instalar dependências necessárias
apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1

# Instalar Chrome
echo "📥 Baixando Google Chrome..."
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

echo "📦 Instalando Google Chrome..."
apt-get install -y ./google-chrome-stable_current_amd64.deb

# Limpar
rm google-chrome-stable_current_amd64.deb

# Verificar instalação
echo "✅ Verificando instalação..."
google-chrome --version

# Instalar ChromeDriver
echo "📥 Instalando ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")

wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip
mv chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver
rm chromedriver_linux64.zip

echo "✅ ChromeDriver instalado:"
chromedriver --version

echo "🎉 Instalação concluída!"
