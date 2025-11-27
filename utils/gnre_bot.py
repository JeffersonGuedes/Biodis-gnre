"""
Bot de automação para emissão de GNRE no portal
SEM LOGIN - Acesso direto ao formulário de emissão
"""

import time
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


# Lista de feriados nacionais (adicione mais conforme necessário)
FERIADOS_2025 = [
    datetime(2025, 1, 1),   # Ano Novo
    datetime(2025, 2, 24),  # Carnaval
    datetime(2025, 2, 25),  # Carnaval
    datetime(2025, 4, 18),  # Sexta-feira Santa
    datetime(2025, 4, 21),  # Tiradentes
    datetime(2025, 5, 1),   # Dia do Trabalho
    datetime(2025, 6, 19),  # Corpus Christi
    datetime(2025, 9, 7),   # Independência
    datetime(2025, 10, 12), # Nossa Senhora Aparecida
    datetime(2025, 11, 2),  # Finados
    datetime(2025, 11, 15), # Proclamação da República
    datetime(2025, 12, 25), # Natal
]

FERIADOS_2026 = [
    datetime(2026, 1, 1),   # Ano Novo
    datetime(2026, 2, 16),  # Carnaval
    datetime(2026, 2, 17),  # Carnaval
    datetime(2026, 4, 3),   # Sexta-feira Santa
    datetime(2026, 4, 21),  # Tiradentes
    datetime(2026, 5, 1),   # Dia do Trabalho
    datetime(2026, 6, 4),   # Corpus Christi
    datetime(2026, 9, 7),   # Independência
    datetime(2026, 10, 12), # Nossa Senhora Aparecida
    datetime(2026, 11, 2),  # Finados
    datetime(2026, 11, 15), # Proclamação da República
    datetime(2026, 12, 25), # Natal
]

FERIADOS = FERIADOS_2025 + FERIADOS_2026


def calcular_data_vencimento():
    """
    Calcula data de vencimento com regras de negócio:
    - Antes das 13h: vencimento hoje
    - Depois das 13h: vencimento dia posterior (próximo dia útil)
    - Se cair em sábado/domingo: próxima segunda-feira
    - Se cair em feriado: próximo dia útil
    - Sexta após 13h: pula para segunda (ou terça se segunda for feriado)
    
    Returns:
        datetime: Data de vencimento calculada
    """
    agora = datetime.now()
    hora_atual = agora.hour
    
    # Regra 1: Definir data base
    if hora_atual >= 13:
        # Depois das 13h: dia posterior
        data_vencimento = agora + timedelta(days=1)
    else:
        # Antes das 13h: dia atual
        data_vencimento = agora
    
    # Regra 2: Ajustar para próximo dia útil (não sábado, domingo ou feriado)
    data_vencimento = ajustar_para_dia_util(data_vencimento)
    
    return data_vencimento


def ajustar_para_dia_util(data):
    """
    Ajusta data para o próximo dia útil (segunda a sexta, exceto feriados)
    
    Args:
        data (datetime): Data a ser ajustada
        
    Returns:
        datetime: Próximo dia útil
    """
    # Remover componente de hora para comparação
    data_sem_hora = data.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Continuar avançando até encontrar um dia útil
    max_tentativas = 10  # Evitar loop infinito
    tentativas = 0
    
    while tentativas < max_tentativas:
        dia_semana = data_sem_hora.weekday()  # 0=segunda, 6=domingo
        
        # Verificar se é sábado (5) ou domingo (6)
        if dia_semana >= 5:
            # Avançar para segunda-feira
            dias_ate_segunda = 7 - dia_semana
            data_sem_hora = data_sem_hora + timedelta(days=dias_ate_segunda)
            tentativas += 1
            continue
        
        # Verificar se é feriado
        if eh_feriado(data_sem_hora):
            # Avançar para próximo dia
            data_sem_hora = data_sem_hora + timedelta(days=1)
            tentativas += 1
            continue
        
        # É dia útil!
        break
    
    return data_sem_hora


def eh_feriado(data):
    """
    Verifica se a data é um feriado
    
    Args:
        data (datetime): Data a verificar
        
    Returns:
        bool: True se for feriado
    """
    data_sem_hora = data.replace(hour=0, minute=0, second=0, microsecond=0)
    return data_sem_hora in FERIADOS


class GNREBot:
    """
    Bot para automação de emissão de GNRE (SEM LOGIN)
    Acessa diretamente: https://www.gnre.pe.gov.br:444/gnre/v/guia/index
    """
    
    def __init__(self, headless=False, salvar_evidencias=True):
        """
        Inicializa o bot
        
        Args:
            headless (bool): Executar browser em modo headless (padrão: False para debug)
            salvar_evidencias (bool): Salvar screenshots durante o processo
        """
        self.headless = headless
        self.salvar_evidencias = salvar_evidencias
        self.driver = None
        self.wait = None
        self.url_emissao = "https://www.gnre.pe.gov.br:444/gnre/v/guia/index"
        
        # Criar diretórios
        self.dir_outputs = Path("outputs")
        self.dir_screenshots = Path("screenshots")
        self.dir_outputs.mkdir(exist_ok=True)
        self.dir_screenshots.mkdir(exist_ok=True)
        
        # Pasta de Downloads do usuário
        self.dir_downloads = Path.home() / "Downloads"
        print(f"📁 Pasta de Downloads configurada: {self.dir_downloads}")
    
    def _inicializar_driver(self):
        """Inicializa o driver do Selenium"""
        options = webdriver.ChromeOptions()
        
        # Detectar se está rodando no Streamlit Cloud (Linux)
        is_linux = sys.platform.startswith('linux')
        
        if self.headless or is_linux:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-extensions')
        
        # Configurar download para pasta Downloads do usuário
        prefs = {
            "download.default_directory": str(self.dir_downloads.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True
        }
        options.add_experimental_option("prefs", prefs)
        
        # Streamlit Cloud (Linux) - usar chromium do sistema
        if is_linux:
            print("🐧 Detectado ambiente Linux (Streamlit Cloud)")
            
            # Procurar chromedriver no sistema
            chrome_driver_paths = [
                '/usr/bin/chromedriver',
                '/usr/local/bin/chromedriver',
                '/home/appuser/.local/bin/chromedriver',
            ]
            
            driver_path = None
            for path in chrome_driver_paths:
                if os.path.exists(path):
                    driver_path = path
                    print(f"✅ ChromeDriver encontrado: {path}")
                    break
            
            if driver_path:
                # Configurar chromium binary
                options.binary_location = '/usr/bin/chromium'
                service = Service(executable_path=driver_path)
            else:
                # Fallback: tentar webdriver-manager
                print("⚠️ ChromeDriver não encontrado no sistema, tentando webdriver-manager...")
                service = Service(ChromeDriverManager().install())
        else:
            # Windows/Mac - usar webdriver-manager
            print("💻 Detectado ambiente local (Windows/Mac)")
            service = Service(ChromeDriverManager().install())
        
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 60)
    
    def _screenshot(self, nome):
        """Salva screenshot se habilitado"""
        if self.salvar_evidencias and self.driver:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            caminho = self.dir_screenshots / f"{timestamp}_{nome}.png"
            self.driver.save_screenshot(str(caminho))
            print(f"📸 Screenshot salvo: {nome}")
    
    def emitir_gnre(self, usuario, senha, dados, callback_progresso=None):
        """
        Emite GNRE automaticamente SEM LOGIN
        
        Args:
            usuario (str): NÃO USADO - mantido por compatibilidade
            senha (str): NÃO USADO - mantido por compatibilidade
            dados (dict): Dados extraídos da NF-e
            callback_progresso (callable): Função para atualizar progresso
        
        Returns:
            dict: Resultado da emissão
        """
        try:
            if not self.driver:
                self._inicializar_driver()
            
            # Etapa 1: Acessar página de emissão diretamente
            if callback_progresso:
                callback_progresso("Acessando formulário GNRE...", 0.1)
            
            print(f"🌐 Acessando: {self.url_emissao}")
            self.driver.get(self.url_emissao)
            print("⏳ Aguardando página carregar completamente...")
            time.sleep(2)  # Aguardar mais tempo para página carregar
            self._screenshot("01_formulario_inicial")
            
            # Etapa 2: Preencher formulário
            if callback_progresso:
                callback_progresso("Preenchendo formulário...", 0.3)
            
            print("✍️ Preenchendo dados do formulário...")
            self._preencher_formulario(dados)
            self._screenshot("02_formulario_preenchido")
            
            # Etapa 3: Validar formulário
            if callback_progresso:
                callback_progresso("Validando dados...", 0.5)
            
            print("🔍 Validando formulário...")
            self._validar_formulario()
            self._screenshot("03_formulario_validado")
            
            # Etapa 4: Baixar PDF
            if callback_progresso:
                callback_progresso("Baixando PDF...", 0.7)
            
            print("📥 Baixando PDF...")
            pdf_path = self._baixar_pdf(dados['numero_nfe'])
            self._screenshot("04_pdf_baixado")
            
            # Etapa 5: Clicar em "Nova GNRE" para próxima
            if callback_progresso:
                callback_progresso("Preparando para próxima GNRE...", 0.9)
            
            print("🔄 Clicando em Nova GNRE...")
            self._nova_gnre()
            
            if callback_progresso:
                callback_progresso("Concluído!", 1.0)
            
            print("✅ GNRE emitida com sucesso!")
            
            return {
                'sucesso': True,
                'arquivo_pdf': pdf_path,
                'numero_gnre': 'Gerado',
                'protocolo': None
            }
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            self._screenshot("erro")
            import traceback
            traceback.print_exc()
            return {
                'sucesso': False,
                'mensagem': str(e)
            }
    
    def _preencher_formulario(self, dados):
        """
        Preenche o formulário de emissão GNRE
        Campos corretos do formulário real
        """
        try:
            # Aguardar formulário carregar completamente
            print("⏳ Aguardando página carregar...")
            time.sleep(2)
            
            # 1. UF Favorecida (Destino) - aguardar o select estar disponível
            print(f"  📍 Procurando campo UF Favorecida...")
            try:
                # Aguardar até o select estar presente e visível
                select_element = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "siglaUf"))
                )
                print(f"  ✅ Campo UF encontrado!")
                
                # Aguardar um pouco mais para garantir que está pronto
                time.sleep(2)
                
                # Criar o Select e selecionar
                select_uf = Select(select_element)
                print(f"  📍 Selecionando UF Favorecida: {dados['uf_destino']}")
                select_uf.select_by_value(dados['uf_destino'])
                print(f"  ✅ UF {dados['uf_destino']} selecionada!")
                time.sleep(2)  # Aguardar carregar opções dependentes
                
            except Exception as e:
                print(f"  ❌ Erro ao selecionar UF: {str(e)}")
                # Tentar encontrar o elemento de outra forma
                print("  🔄 Tentando localizar por ID...")
                try:
                    select_element = self.driver.find_element(By.ID, "ufFavorecida")
                    select_uf = Select(select_element)
                    select_uf.select_by_value(dados['uf_destino'])
                    time.sleep(3)
                except Exception as e2:
                    print(f"  ❌ Falha na segunda tentativa: {str(e2)}")
                    raise Exception(f"Não foi possível selecionar UF Favorecida: {str(e)}")
            
            # 2. Aguardar opção GNRE Simples aparecer e selecionar
            print("  📋 Aguardando opção GNRE Simples aparecer...")
            try:
                opt_gnre_simples = self.wait.until(
                    EC.visibility_of_element_located((By.ID, "optGnreSimples"))
                )
                print("  ✅ Opção GNRE Simples encontrada!")
                time.sleep(1)
                opt_gnre_simples.click()
                print("  ✅ GNRE Simples selecionada!")
                time.sleep(2)
            except Exception as e:
                print(f"  ⚠️ Opção GNRE Simples não encontrada ou já selecionada: {str(e)}")
                time.sleep(1)
            
            # 3. Contribuinte: Não Inscrito
            print("  👤 Selecionando Contribuinte: Não Inscrito...")
            try:
                opt_nao_inscrito = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "optNaoInscrito"))
                )
                opt_nao_inscrito.click()
                print("  ✅ Não Inscrito selecionado!")
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠️ Erro ao selecionar Não Inscrito: {str(e)}")
                time.sleep(1)
            
            # 4. Tipo: CNPJ
            print("  🏢 Selecionando Tipo: CNPJ...")
            try:
                tipo_cnpj = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "tipoCNPJ"))
                )
                tipo_cnpj.click()
                print("  ✅ Tipo CNPJ selecionado!")
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠️ Erro ao selecionar tipo CNPJ: {str(e)}")
                time.sleep(1)
            
            # 5. CNPJ do Emitente (apenas números, sem formatação)
            cnpj_original = dados['cnpj_emitente']
            cnpj_limpo = ''.join(filter(str.isdigit, cnpj_original))
            
            # Validação
            if len(cnpj_limpo) != 14:
                raise Exception(f"CNPJ inválido: {cnpj_limpo} (tamanho: {len(cnpj_limpo)}, esperado: 14)")
            
            print(f"  🔢 CNPJ original: {cnpj_original}")
            print(f"  🔢 CNPJ limpo: {cnpj_limpo} (tamanho: {len(cnpj_limpo)})")
            
            try:
                campo_cnpj = self.wait.until(
                    EC.presence_of_element_located((By.ID, "documentoEmitente"))
                )
                
                # Método 1: Tentar com JavaScript diretamente
                print("  🔧 Tentando preencher com JavaScript...")
                try:
                    self.driver.execute_script(
                        f"arguments[0].value = '{cnpj_limpo}';"
                        "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));"
                        "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                        campo_cnpj
                    )
                    time.sleep(0.5)
                    valor_js = campo_cnpj.get_attribute('value')
                    print(f"  ✅ JavaScript: valor = {valor_js}")
                except Exception as e:
                    print(f"  ⚠️ JavaScript falhou: {str(e)}")
                
                # Verificar o que está no campo
                valor_atual = campo_cnpj.get_attribute('value')
                print(f"  🔍 Valor atual no campo: {valor_atual}")
                
                # Se ainda não está correto, tentar método tradicional
                if valor_atual != cnpj_limpo:
                    print("  🔄 Tentando método tradicional...")
                    campo_cnpj.clear()
                    time.sleep(0.3)
                    
                    # Enviar caracter por caracter (mais lento mas mais confiável)
                    for digito in cnpj_limpo:
                        campo_cnpj.send_keys(digito)
                        time.sleep(0.05)
                    
                    time.sleep(0.5)
                    valor_final = campo_cnpj.get_attribute('value')
                    print(f"  🔍 Valor final: {valor_final}")
                
                # Verificação final
                valor_preenchido = campo_cnpj.get_attribute('value')
                if valor_preenchido != cnpj_limpo:
                    print(f"  ⚠️⚠️⚠️ ATENÇÃO: CNPJ INCORRETO NO CAMPO! ⚠️⚠️⚠️")
                    print(f"     Esperado: {cnpj_limpo}")
                    print(f"     No campo: {valor_preenchido}")
                    print(f"     O site pode estar modificando o valor!")
                else:
                    print(f"  ✅ CNPJ correto no campo: {valor_preenchido}")
                
                time.sleep(0.5)
            except Exception as e:
                print(f"  ❌ Erro ao preencher CNPJ: {str(e)}")
            
            # 6. Razão Social
            razao_social = dados.get('razao_social', '')
            print(f"  🏭 Preenchendo Razão Social: {razao_social}")
            try:
                campo_razao = self.wait.until(
                    EC.presence_of_element_located((By.ID, "razaoSocialEmitente"))
                )
                campo_razao.clear()
                campo_razao.send_keys(razao_social)
                print("✅ Razão Social preenchida!")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Erro ao preencher Razão Social: {str(e)}")
            
            # 7. Endereço
            endereco = dados.get('endereco_emitente', '')
            print(f"  📍 Preenchendo Endereço: {endereco}")
            try:
                # Tentar primeiro por NAME
                try:
                    campo_endereco = self.wait.until(
                        EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.enderecoEmitente"))
                    )
                    print("  ✅ Campo endereço encontrado por NAME")
                except:
                    # Se falhar, tentar por ID
                    campo_endereco = self.wait.until(
                        EC.presence_of_element_located((By.ID, "enderecoEmitente"))
                    )
                    print("  ✅ Campo endereço encontrado por ID")
                
                campo_endereco.clear()
                time.sleep(0.3)
                campo_endereco.send_keys(endereco)
                print("  ✅ Endereço preenchido!")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Erro ao preencher Endereço: {str(e)}")
            
            # 8. UF Emitente
            uf_emitente = dados.get('uf_emitente', 'CE')
            print(f"  🗺️ Selecionando UF Emitente: {uf_emitente}")
            try:
                select_uf_emit = Select(self.wait.until(
                    EC.presence_of_element_located((By.ID, "ufEmitente"))
                ))
                select_uf_emit.select_by_value(uf_emitente)
                print("  ✅ UF Emitente selecionada!")
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠️ Erro ao selecionar UF Emitente: {str(e)}")
            
            # 9. Município Emitente (select by visible text)
            municipio = dados.get('municipio_emitente', '')
            print(f"  🏙️ Selecionando Município: {municipio}")
            try:
                select_municipio = Select(self.wait.until(
                    EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.municipioEmitente"))
                ))
                
                # Tentar selecionar pelo nome do município (como aparece no XML)
                try:
                    select_municipio.select_by_visible_text(municipio.upper())
                    print(f"  ✅ Município selecionado: {municipio.upper()}")
                except:
                    # Tentar sem uppercase
                    try:
                        select_municipio.select_by_visible_text(municipio)
                        print(f"  ✅ Município selecionado: {municipio}")
                    except:
                        # Tentar capitalize (Primeira letra maiúscula)
                        select_municipio.select_by_visible_text(municipio.capitalize())
                        print(f"  ✅ Município selecionado: {municipio.capitalize()}")
                
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Erro ao selecionar Município: {str(e)}")
                print(f"     Tentando buscar município '{municipio}' nas opções disponíveis...")
                try:
                    # Mostrar opções disponíveis para debug
                    select_municipio = Select(self.driver.find_element(By.NAME, "gnre.dadosGnre.municipioEmitente"))
                    opcoes = [opt.text for opt in select_municipio.options[:5]]  # Primeiras 5 opções
                    print(f"     Primeiras opções: {opcoes}")
                except:
                    pass
            
            # 10. CEP Emitente (apenas números, sem formatação)
            cep = dados.get('cep_emitente', '')
            cep_limpo = ''.join(filter(str.isdigit, cep))
            print(f"  📮 Preenchendo CEP: {cep_limpo} (apenas números)")
            try:
                campo_cep = self.wait.until(
                    EC.presence_of_element_located((By.ID, "cepEmitente"))
                )
                campo_cep.clear()
                campo_cep.send_keys(cep_limpo)
                print("  ✅ CEP preenchido!")
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠️ Erro ao preencher CEP: {str(e)}")
            
            # 11. Receita (100102 - ICMS DIFAL)
            print(f"  💰 Selecionando Código Receita: 100102")
            try:
                select_receita = Select(self.wait.until(
                    EC.presence_of_element_located((By.ID, "receita"))
                ))
                select_receita.select_by_value("100102")
                print("  ✅ Receita selecionada!")
                time.sleep(2)
            except Exception as e:
                print(f"  ⚠️ Erro ao selecionar Receita: {str(e)}")
            
            # 12. Documento de Origem: Avulsa (value="01")
            print(f"  📄 Selecionando Documento de Origem: Avulsa")
            try:
                select_doc_origem = Select(self.wait.until(
                    EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.itens[0].documentoOrigem.tipo"))
                ))
                select_doc_origem.select_by_value("01")
                print("  ✅ Documento de Origem: Avulsa selecionado!")
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠️ Erro ao selecionar Documento de Origem: {str(e)}")
            
            # 13. Número do Documento (número da NF-e)
            numero_nfe = dados.get('numero_nfe', '')
            print(f"  🔢 Preenchendo Número do Documento: {numero_nfe}")
            try:
                campo_num_doc = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.itens[0].documentoOrigem.numero"))
                )
                campo_num_doc.clear()
                campo_num_doc.send_keys(numero_nfe)
                print(f"  ✅ Número do Documento preenchido: {numero_nfe}")
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠️ Erro ao preencher Número do Documento: {str(e)}")
            
            # 14. Mês de Referência (mês atual)
            mes_atual = datetime.now().strftime('%m')  # 01 a 12
            ano_atual = datetime.now().strftime('%Y')  # 2025
            
            print(f"  📅 Selecionando Mês de Referência: {mes_atual}/{ano_atual}")
            try:
                select_mes = Select(self.wait.until(
                    EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.itens[0].mesReferencia"))
                ))
                select_mes.select_by_value(mes_atual)
                print(f"  ✅ Mês de Referência selecionado: {mes_atual}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Erro ao selecionar Mês de Referência: {str(e)}")
            
            # 15. Ano de Referência (ano atual)
            print(f"  📅 Selecionando Ano de Referência: {ano_atual}")
            try:
                select_ano = Select(self.wait.until(
                    EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.itens[0].anoReferencia"))
                ))
                select_ano.select_by_value(ano_atual)
                print(f"  ✅ Ano de Referência selecionado: {ano_atual}")
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠️ Erro ao selecionar Ano de Referência: {str(e)}")
            
            # 16. Data de Vencimento com regras de negócio
            data_vencimento_dt = calcular_data_vencimento()
            data_vencimento = data_vencimento_dt.strftime('%d/%m/%Y')  # Formato com barras: dd/mm/yyyy
            hora_atual = datetime.now().hour
            
            print(f"  📅 Calculando Data de Vencimento...")
            print(f"     Hora atual: {hora_atual}:00")
            if hora_atual >= 13:
                print(f"     ⏰ Após 13h: vencimento para próximo dia útil")
            else:
                print(f"     ⏰ Antes das 13h: vencimento para hoje")
            print(f"     📆 Data calculada: {data_vencimento}")
            
            try:
                campo_vencimento = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.itens[0].dataVencimento"))
                )
                campo_vencimento.clear()
                time.sleep(0.5)
                
                # Enviar data caractere por caractere para evitar problemas de formatação
                for char in data_vencimento:
                    campo_vencimento.send_keys(char)
                    time.sleep(0.05)
                
                # Verificar valor no campo
                time.sleep(0.3)
                valor_campo = campo_vencimento.get_attribute('value')
                print(f"  ✅ Data de Vencimento preenchida: {valor_campo}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Erro ao preencher Data de Vencimento: {str(e)}")
            
            # 17. Valor do ICMS DIFAL (vICMSUFDest do XML)
            valor_icms = dados.get('valor_icms', '0.00')
            # Formatar valor: remover separadores e usar ponto como decimal
            try:
                valor_float = float(valor_icms)
                valor_formatado = f"{valor_float:.2f}".replace('.', ',')  # Formato brasileiro
            except:
                valor_formatado = str(valor_icms).replace('.', ',')
            
            print(f"  💰 Preenchendo Valor: R$ {valor_formatado}")
            try:
                campo_valor = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.itens[0].valores[0].valor"))
                )
                campo_valor.clear()
                time.sleep(0.3)
                campo_valor.send_keys(valor_formatado)
                print(f"  ✅ Valor preenchido: R$ {valor_formatado}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Erro ao preencher Valor: {str(e)}")
            
            # 18. Destinatário: Não Inscrito
            print(f"  👤 Selecionando Destinatário: Não Inscrito")
            try:
                opt_nao_inscrito_dest = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "optNaoInscritoDest"))
                )
                opt_nao_inscrito_dest.click()
                print("  ✅ Destinatário Não Inscrito selecionado!")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Erro ao selecionar Destinatário Não Inscrito: {str(e)}")
            
            # 19. Tipo de Documento Destinatário: CPF
            print(f"  🆔 Selecionando Tipo: CPF do Destinatário")
            try:
                tipo_cpf_dest = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "tipoCPFDest"))
                )
                tipo_cpf_dest.click()
                print("  ✅ Tipo CPF selecionado para Destinatário!")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Erro ao selecionar tipo CPF Destinatário: {str(e)}")
            
            # 20. CPF do Destinatário (apenas números)
            cpf_dest = dados.get('documento_destinatario', '')
            cpf_limpo = ''.join(filter(str.isdigit, cpf_dest))
            
            if len(cpf_limpo) == 11:  # Validar CPF
                print(f"  🔢 Preenchendo CPF Destinatário: {cpf_limpo}")
                try:
                    # Campo correto para CPF do destinatário
                    campo_cpf_dest = self.wait.until(
                        EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.itens[0].destinatarioCpf"))
                    )
                    
                    # Limpar campo
                    campo_cpf_dest.clear()
                    time.sleep(0.5)
                    
                    # Usar JavaScript para preencher
                    self.driver.execute_script(
                        f"arguments[0].value = '{cpf_limpo}';"
                        "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));"
                        "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                        campo_cpf_dest
                    )
                    time.sleep(0.5)
                    
                    # Verificar se foi preenchido
                    valor_cpf = campo_cpf_dest.get_attribute('value')
                    print(f"  ✅ CPF Destinatário preenchido: {valor_cpf}")
                    
                    if valor_cpf != cpf_limpo:
                        print(f"  ⚠️ Tentando preencher novamente...")
                        campo_cpf_dest.clear()
                        time.sleep(0.3)
                        for digito in cpf_limpo:
                            campo_cpf_dest.send_keys(digito)
                            time.sleep(0.05)
                        print(f"  ✅ CPF preenchido (método alternativo)")
                    
                    time.sleep(1)
                except Exception as e:
                    print(f"  ⚠️ Erro ao preencher CPF Destinatário: {str(e)}")
            else:
                print(f"  ⚠️ CPF inválido ou não encontrado: {cpf_dest}")
            
            # 21. Razão Social (Nome) do Destinatário
            nome_dest = dados.get('nome_destinatario', '')
            print(f"  👤 Preenchendo Nome Destinatário: {nome_dest}")
            try:
                campo_nome_dest = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.itens[0].razaoSocialDestinatario"))
                )
                campo_nome_dest.clear()
                campo_nome_dest.send_keys(nome_dest)
                print(f"  ✅ Nome Destinatário preenchido: {nome_dest}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Erro ao preencher Nome Destinatário: {str(e)}")
            
            # 22. Município do Destinatário
            municipio_dest = dados.get('municipio_destinatario', '')
            print(f"  🏙️ Selecionando Município Destinatário: {municipio_dest}")
            try:
                select_mun_dest = Select(self.wait.until(
                    EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.itens[0].municipioDestinatario"))
                ))
                
                # Tentar selecionar pelo nome do município
                try:
                    select_mun_dest.select_by_visible_text(municipio_dest.upper())
                    print(f"  ✅ Município Destinatário selecionado: {municipio_dest.upper()}")
                except:
                    try:
                        select_mun_dest.select_by_visible_text(municipio_dest)
                        print(f"  ✅ Município Destinatário selecionado: {municipio_dest}")
                    except:
                        select_mun_dest.select_by_visible_text(municipio_dest.capitalize())
                        print(f"  ✅ Município Destinatário selecionado: {municipio_dest.capitalize()}")
                
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Erro ao selecionar Município Destinatário: {str(e)}")
            
            # 23. Campo Adicional - Chave NF-e Referenciada
            chave_ref = dados.get('chave_nfe_referenciada', '')
            if chave_ref:
                print(f"  📋 Preenchendo Campo Adicional (Chave NF-e Ref): {chave_ref}")
                try:
                    campo_adicional = self.wait.until(
                        EC.presence_of_element_located((By.ID, "campoAdicional00"))
                    )
                    campo_adicional.clear()
                    campo_adicional.send_keys(chave_ref)
                    print(f"  ✅ Campo Adicional preenchido: {chave_ref}")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"  ⚠️ Erro ao preencher Campo Adicional: {str(e)}")
            else:
                print(f"  ℹ️ Sem chave NF-e referenciada para preencher")
            
            # 24. Data de Pagamento (mesma regra e data do vencimento)
            data_pagamento_dt = calcular_data_vencimento()
            data_pagamento_str = data_pagamento_dt.strftime('%d/%m/%Y')  # Formato com barras: dd/mm/yyyy
            
            print(f"  📅 Preenchendo Data de Pagamento: {data_pagamento_str}")
            try:
                campo_data_pagamento = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.dataPagamento"))
                )
                campo_data_pagamento.clear()
                time.sleep(0.5)
                
                # Enviar data caractere por caractere para evitar problemas de formatação
                for char in data_pagamento_str:
                    campo_data_pagamento.send_keys(char)
                    time.sleep(0.05)
                
                # Verificar valor no campo
                time.sleep(0.3)
                valor_campo_pag = campo_data_pagamento.get_attribute('value')
                print(f"  ✅ Data de Pagamento preenchida: {valor_campo_pag}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Erro ao preencher Data de Pagamento: {str(e)}")
            
            print("✅ Formulário preenchido com sucesso!")
            
        except Exception as e:
            raise Exception(f"Erro ao preencher formulário: {str(e)}")
    
    def _validar_formulario(self):
        """Clica no botão Validar"""
        try:
            print("⚙️ Clicando em Validar...")
            btn_validar = self.wait.until(
                EC.element_to_be_clickable((By.NAME, "btnValidar"))
            )
            btn_validar.click()
            print("⏳ Aguardando validação...")
            time.sleep(5)
            
            # Verificar se foi redirecionado para página de resultado
            if "resultado" in self.driver.current_url:
                print("✅ Redirecionado para página de resultado")
            else:
                print(f"ℹ️ URL atual: {self.driver.current_url}")
            
        except Exception as e:
            raise Exception(f"Erro ao validar formulário: {str(e)}")
    
    def _gerar_gnre(self):
        """Função mantida por compatibilidade - não é mais usada"""
        return {
            'numero_gnre': 'Validado',
            'protocolo': None
        }
    
    def _baixar_pdf(self, numero_nfe):
        """Baixa o PDF da GNRE após validação na página de resultado"""
        try:
            print("📥 Procurando botão de download do PDF na página de resultado...")
            
            # Aguardar a página de resultado carregar
            time.sleep(1.5)
            
            # Procurar botão btnBaixar (NAME)
            try:
                btn_baixar = self.wait.until(
                    EC.element_to_be_clickable((By.NAME, "btnBaixar"))
                )
                print("  ✅ Botão Baixar encontrado (NAME=btnBaixar)")
                btn_baixar.click()
                print("  ✅ Download do PDF iniciado!")
                print(f"  📁 Salvando em: {self.dir_downloads}")
                time.sleep(5)  # Aguardar download completar
            except Exception as e:
                print(f"  ⚠️ Botão btnBaixar não encontrado: {str(e)}")
                print("  🔄 Tentando outros localizadores...")
                
                # Fallback: tentar outros localizadores
                botoes_download = [
                    (By.XPATH, "//button[contains(text(), 'Baixar')]"),
                    (By.XPATH, "//a[contains(text(), 'Baixar')]"),
                    (By.XPATH, "//input[@value='Baixar']"),
                    (By.ID, "btnBaixar"),
                    (By.XPATH, "//button[contains(@class, 'baixar')]"),
                ]
                
                btn_encontrado = False
                for locator in botoes_download:
                    try:
                        btn = self.wait.until(EC.element_to_be_clickable(locator))
                        print(f"  ✅ Botão encontrado: {locator}")
                        btn.click()
                        btn_encontrado = True
                        break
                    except:
                        continue
                
                if not btn_encontrado:
                    print("  ⚠️ Nenhum botão de download encontrado")
                    return None
                
                time.sleep(5)
            
            # Procurar arquivo PDF mais recente na pasta Downloads
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            nome_pdf_esperado = f"GNRE_{numero_nfe}_{timestamp}.pdf"
            
            # Procurar PDFs recentes na pasta Downloads do usuário
            print(f"  🔍 Procurando PDF em: {self.dir_downloads}")
            arquivos = list(self.dir_downloads.glob("*.pdf"))
            
            if arquivos:
                # Pegar o mais recente (baixado nos últimos 30 segundos)
                arquivo_mais_recente = max(arquivos, key=os.path.getctime)
                tempo_arquivo = os.path.getctime(arquivo_mais_recente)
                tempo_atual = time.time()
                
                # Verificar se foi baixado recentemente (últimos 30 segundos)
                if (tempo_atual - tempo_arquivo) < 30:
                    print(f"  ✅ PDF encontrado: {arquivo_mais_recente.name}")
                    print(f"  📁 Localização: {arquivo_mais_recente}")
                    return str(arquivo_mais_recente)
                else:
                    print(f"  ⚠️ PDF encontrado mas muito antigo: {arquivo_mais_recente.name}")
            
            print("  ⚠️ PDF não encontrado na pasta Downloads")
            print(f"  💡 Verifique manualmente em: {self.dir_downloads}")
            return None
            
        except Exception as e:
            print(f"⚠️ Erro ao baixar PDF: {str(e)}")
            return None
    
    def _nova_gnre(self):
        """Clica no botão 'Nova GNRE' (btnNova) para processar próxima"""
        try:
            print("🔄 Procurando botão Nova GNRE...")
            
            # Aguardar um pouco após download
            time.sleep(1)
            
            # Procurar botão btnNova (NAME) - específico da página de resultado
            try:
                btn_nova = self.wait.until(
                    EC.element_to_be_clickable((By.NAME, "btnNova"))
                )
                print("  ✅ Botão Nova encontrado (NAME=btnNova)")
                btn_nova.click()
                print("  ✅ Clicou em Nova GNRE!")
                time.sleep(2)  # Aguardar carregar novo formulário
                
                # Verificar se voltou para página de emissão
                if "guia/index" in self.driver.current_url:
                    print("  ✅ Retornou para formulário de emissão")
                else:
                    print(f"  ℹ️ URL atual: {self.driver.current_url}")
                    
            except Exception as e:
                print(f"  ⚠️ Botão btnNova não encontrado: {str(e)}")
                print("  🔄 Tentando recarregar página de emissão...")
                self.driver.get(self.url_emissao)
                time.sleep(2)
                
        except Exception as e:
            print(f"⚠️ Erro ao iniciar nova GNRE: {str(e)}")
            # Tentar recarregar página como fallback
            try:
                print("  🔄 Tentando recarregar página de emissão...")
                self.driver.get(self.url_emissao)
                time.sleep(3)
            except:
                pass
    
    def fechar(self):
        """Fecha o driver"""
        if self.driver:
            print("🔚 Fechando navegador...")
            self.driver.quit()
            self.driver = None