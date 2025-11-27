# 📄 Sistema de Emissão GNRE - Biodis

Sistema automatizado para processar XMLs de NF-e e emitir GNREs (Guia Nacional de Recolhimento de Tributos Estaduais) em lote.

## ⚡ ATUALIZAÇÃO: Agora SEM LOGIN!

O sistema acessa diretamente o formulário de emissão:
- URL: `https://www.gnre.pe.gov.br:444/gnre/v/guia/index`
- **Não precisa de credenciais**
- Preenche automaticamente os campos
- Gera GNRE e baixa PDF
- Clica "Nova GNRE" e continua

## 🎯 Funcionalidades

- ✅ Upload de múltiplos XMLs de NF-e
- ✅ Extração automática de dados fiscais
- ✅ Validação completa de dados (CNPJ, CPF, UF, etc.)
- ✅ **Emissão automática SEM LOGIN**
- ✅ Processamento em lote
- ✅ Download automático de PDFs
- ✅ Screenshots de evidências
- ✅ Modo visual (veja o navegador trabalhando)

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Google Chrome instalado
- ~~Credenciais de acesso ao portal GNRE~~ **NÃO NECESSÁRIO!**

## 🚀 Instalação e Uso

### Primeira vez
```powershell
# 1. Instalar dependências
.\setup.ps1

# 2. Iniciar sistema
.\iniciar.ps1
```

### Uso normal
```powershell
.\iniciar.ps1
```

## 💻 Como Usar

1. **Configure modo visual (recomendado)**
   - Na sidebar, DESMARQUE "Modo Headless"
   - Assim você vê o navegador preenchendo os formulários

2. **Upload dos XMLs**
   - Arraste arquivos XML ou clique para selecionar
   - Pode ser 1 ou mais arquivos

3. **Processar**
   - Clique em "🔍 Processar XMLs"
   - Revise os dados extraídos

4. **Emitir**
   - Clique em "🚀 Emitir GNREs"
   - Veja o navegador trabalhando automaticamente:
     - Acessa formulário GNRE
     - Preenche campos
     - Gera GNRE
     - Baixa PDF
     - Clica "Nova GNRE"
     - Repete para próximo XML

5. **Resultado**
   - PDFs em `outputs/`
   - Screenshots em `screenshots/`

## 📁 Estrutura do Projeto

```
sistema-conversao-gnre-biodis/
├── app.py                      # Aplicação Streamlit principal
├── main.py                     # Script CLI (opcional)
├── requirements.txt            # Dependências Python
├── README.md                   # Este arquivo
├── utils/                      # Módulos utilitários
│   ├── __init__.py
│   ├── gnre_bot.py            # Automação do portal GNRE
│   ├── xml_parser.py          # Parser de XMLs NF-e
│   └── validators.py          # Validadores de dados
├── outputs/                    # PDFs das GNREs geradas
├── screenshots/                # Evidências do processo
└── temp_xmls/                  # XMLs temporários
```

## 📊 Dados Extraídos dos XMLs

O sistema extrai automaticamente:

- ✅ Número da NF-e
- ✅ Série
- ✅ Data de emissão
- ✅ CNPJ do emitente
- ✅ Inscrição Estadual do emitente
- ✅ UF de origem e destino
- ✅ Valor do ICMS DIFAL
- ✅ Dados do destinatário
- ✅ Chave de acesso da NF-e

## ⚙️ Configurações Avançadas

### Modo Headless
- ✅ **Ativado**: Navegador roda em segundo plano (mais rápido)
- ❌ **Desativado**: Você pode ver o navegador trabalhando (útil para debug)

### Salvar Evidências
- ✅ **Ativado**: Salva screenshots de cada etapa
- ❌ **Desativado**: Não salva screenshots (economiza espaço)

## 🔍 Validações Implementadas

O sistema valida:

- ✅ CNPJ (estrutura e dígitos verificadores)
- ✅ CPF (estrutura e dígitos verificadores)
- ✅ Inscrição Estadual
- ✅ UF (códigos válidos)
- ✅ Datas (formato e valores razoáveis)
- ✅ Valores monetários (mínimo e máximo)
- ✅ Código de receita
- ✅ Estrutura do XML NF-e

## 📝 Campos da GNRE

O sistema preenche automaticamente:

| Campo GNRE | Origem | Descrição |
|------------|--------|-----------|
| c01_UfFavorecida | UF Destino | Estado favorecido |
| c02_receita | Fixo: 100102 | ICMS DIFAL |
| c03_idContribuinteEmitente | CNPJ Emitente | CNPJ do remetente |
| c04_tipoDocumentoOrigem | Fixo: 2 | NF-e |
| c05_numeroDocumento | Número NF-e | Número do documento |
| c06_dataEmissao | Data Emissão | Data de emissão |
| c10_valorPrincipal | Valor ICMS DIFAL | Valor a recolher |
| c14_dataVencimento | Data Emissão | Vencimento |
| c17_inscricaoEstadual | IE Emitente | Inscrição Estadual |

## 🚨 Tratamento de Erros

O sistema trata:

- ❌ XMLs inválidos ou corrompidos
- ❌ NF-es sem DIFAL a recolher
- ❌ Campos obrigatórios ausentes
- ❌ Erros de conexão com portal GNRE
- ❌ Timeout em operações
- ❌ Credenciais inválidas

## 📦 Arquivos Gerados

### Outputs (PDFs)
Localização: `outputs/`

Formato: `GNRE_{numero_nfe}_{timestamp}.pdf`

### Screenshots
Localização: `screenshots/`

Capturas automáticas de:
1. Página inicial
2. Após login
3. Tela de emissão
4. Formulário preenchido
5. GNRE gerada
6. Erros (se houver)

## 🔐 Segurança

- ⚠️ **Não compartilhe suas credenciais**
- ⚠️ **Credenciais são armazenadas apenas na sessão**
- ⚠️ **Limpe credenciais ao sair**
- ⚠️ **Use em ambiente seguro**

## 🐛 Solução de Problemas

### Erro: "Selenium não encontrado"
```bash
pip install selenium webdriver-manager
```

### Erro: "Chrome driver não encontrado"
- Certifique-se que o Google Chrome está instalado
- O webdriver-manager baixa automaticamente

### Erro: "XML inválido"
- Verifique se é um XML de NF-e válido
- Certifique-se que o arquivo não está corrompido

### Erro: "Não há DIFAL"
- A NF-e não possui ICMS DIFAL a recolher
- Verifique o campo `vICMSUFDest` no XML

## 📞 Suporte

Para dúvidas ou problemas:
- Verifique os logs no terminal
- Revise os screenshots salvos
- Consulte a documentação do portal GNRE

## 📄 Licença

Sistema desenvolvido para uso interno da Biodis Industrial LTDA.

## 🔄 Atualizações

### Versão 1.0.0 (Atual)
- ✅ Upload múltiplo de XMLs
- ✅ Processamento em lote
- ✅ Validações completas
- ✅ Interface Streamlit
- ✅ Automação completa

---

**Desenvolvido por**: Biodis Industrial LTDA  
**Data**: Novembro 2025
