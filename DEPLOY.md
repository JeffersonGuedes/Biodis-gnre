# 🚀 Deploy no Streamlit Cloud

Este projeto está configurado para funcionar no Streamlit Cloud.

## 📋 Arquivos de Configuração

### ✅ `packages.txt`
Instala dependências do sistema Linux (chromium e chromedriver):
```
chromium
chromium-driver
```

### ✅ `.streamlit/config.toml`
Configurações do Streamlit Cloud:
```toml
[server]
headless = true
port = 8501
enableCORS = false

[browser]
gatherUsageStats = false
```

### ✅ `requirements.txt`
Já configurado com todas as dependências Python necessárias.

## 🔧 Como Fazer Deploy

### 1. Preparar Repositório

Certifique-se de ter todos os arquivos:
- ✅ `app.py` (aplicação principal)
- ✅ `packages.txt` (dependências do sistema)
- ✅ `requirements.txt` (dependências Python)
- ✅ `.streamlit/config.toml` (configurações)
- ✅ `utils/gnre_bot.py` (já configurado para Linux)
- ✅ `utils/xml_parser.py`
- ✅ `utils/validators.py`

### 2. Fazer Push para GitHub

```bash
git add .
git commit -m "Configuração para Streamlit Cloud"
git push origin main
```

### 3. Deploy no Streamlit Cloud

1. Acesse: https://share.streamlit.io
2. Clique em **"New app"**
3. Conecte seu repositório GitHub
4. Configure:
   - **Repository**: `JeffersonGuedes/Biodis-gnre`
   - **Branch**: `main` (ou `dev`)
   - **Main file path**: `app.py`
   - **App URL**: `biodis-gnre` (ou nome de sua escolha)

5. Clique em **"Deploy!"**

### 4. Aguardar Build

O Streamlit Cloud vai:
- ✅ Instalar chromium e chromium-driver (via `packages.txt`)
- ✅ Instalar dependências Python (via `requirements.txt`)
- ✅ Detectar automaticamente ambiente Linux
- ✅ Iniciar a aplicação em modo headless

## 🔍 Como Funciona

O código foi modificado para **detectar automaticamente** o ambiente:

- **Linux (Streamlit Cloud)**: Usa chromium-driver do sistema
- **Windows/Mac (Local)**: Usa webdriver-manager

**Nenhuma mudança no código principal!** A detecção é automática via `sys.platform`.

## ⚠️ Limitações do Streamlit Cloud

1. **Headless obrigatório**: Navegador roda em modo invisível
2. **Timeout**: Processos muito longos podem ser interrompidos
3. **Memória**: Processar muitos XMLs de uma vez pode estourar a RAM
4. **Downloads temporários**: PDFs ficam na pasta Downloads temporária do container

### 💡 Recomendações:

- Processar no máximo **5-10 XMLs por vez**
- Aguardar alguns segundos entre lotes
- Baixar PDFs imediatamente após geração

## 🐛 Troubleshooting

### Erro: "ChromeDriver not found"
**Causa**: `packages.txt` não foi detectado ou está incorreto  
**Solução**: Verificar se arquivo existe e tem conteúdo correto

### Erro: "Session timeout"
**Causa**: Processamento demorou mais de 10 minutos  
**Solução**: Processar menos XMLs por vez

### Erro: "Memory limit exceeded"
**Causa**: Muitos XMLs sendo processados simultaneamente  
**Solução**: Aguardar entre lotes, processar em grupos menores

### Ver Logs do Streamlit Cloud

1. Abra seu app no Streamlit Cloud
2. Clique no menu **"☰"** (canto superior direito)
3. Clique em **"Manage app"**
4. Veja logs em tempo real na aba **"Logs"**

## 📞 Suporte

- **Docs Streamlit**: https://docs.streamlit.io/streamlit-community-cloud
- **Forum**: https://discuss.streamlit.io
- **Repo**: https://github.com/JeffersonGuedes/Biodis-gnre

## 🎉 Pronto!

Seu sistema agora funciona tanto localmente quanto no Streamlit Cloud sem precisar mudar nada no código!
