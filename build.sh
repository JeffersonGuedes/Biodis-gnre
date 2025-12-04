#!/bin/bash
set -e

echo "📦 Instalando dependências Python..."
pip install -r requirements.txt

echo "🔧 Instalando dependências do Chrome..."
apt-get update
apt-get install -y wget gnupg unzip

echo "📥 Instalando Google Chrome..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable

echo "📥 Instalando ChromeDriver..."
# Detectar versão exata do Chrome instalado
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
echo "Chrome version detectada: $CHROME_VERSION"

# Baixar ChromeDriver compatível
wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip
unzip -q /tmp/chromedriver.zip -d /tmp/
mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver
rm -rf /tmp/chromedriver*

echo "🔍 Verificando versões..."
google-chrome --version
chromedriver --version

echo "✅ Build concluído!"
google-chrome --version
chromedriver --version
