"""
Bot de automação para emissão de GNRE no portal
SEM LOGIN - Acesso direto ao formulário de emissão
COMPATÍVEL COM STREAMLIT CLOUD (LINUX) E WINDOWS
"""

import time
import os
import sys
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Gerenciador de Drivers
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# ==============================================================================
# CONSTANTES E FERIADOS
# ==============================================================================

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

# ==============================================================================
# FUNÇÕES AUXILIARES DE DATA
# ==============================================================================

def calcular_data_vencimento():
    """Calcula data de vencimento com regras de negócio."""
    agora = datetime.now()
    hora_atual = agora.hour
    
    # Regra 1: Definir data base
    if hora_atual >= 13:
        # Depois das 13h: dia posterior
        data_vencimento = agora + timedelta(days=1)
    else:
        # Antes das 13h: dia atual
        data_vencimento = agora
    
    # Regra 2: Ajustar para próximo dia útil
    data_vencimento = ajustar_para_dia_util(data_vencimento)
    return data_vencimento

def ajustar_para_dia_util(data):
    """Ajusta data para o próximo dia útil (segunda a sexta, exceto feriados)"""
    data_sem_hora = data.replace(hour=0, minute=0, second=0, microsecond=0)
    max_tentativas = 10
    tentativas = 0
    
    while tentativas < max_tentativas:
        dia_semana = data_sem_hora.weekday()  # 0=segunda, 6=domingo
        
        # Verificar se é sábado (5) ou domingo (6)
        if dia_semana >= 5:
            dias_ate_segunda = 7 - dia_semana
            data_sem_hora = data_sem_hora + timedelta(days=dias_ate_segunda)
            tentativas += 1
            continue
        
        # Verificar se é feriado
        if eh_feriado(data_sem_hora):
            data_sem_hora = data_sem_hora + timedelta(days=1)
            tentativas += 1
            continue
        
        break
    
    return data_sem_hora

def eh_feriado(data):
    data_sem_hora = data.replace(hour=0, minute=0, second=0, microsecond=0)
    return data_sem_hora in FERIADOS

# ==============================================================================
# CLASSE PRINCIPAL DO BOT
# ==============================================================================

class GNREBot:
    """
    Bot para automação de emissão de GNRE (SEM LOGIN)
    """
    
    def __init__(self, headless=False, salvar_evidencias=True):
        self.headless = headless
        self.salvar_evidencias = salvar_evidencias
        self.driver = None
        self.wait = None
        self.url_emissao = "https://www.gnre.pe.gov.br:444/gnre/v/guia/index"
        
        # Criar diretórios locais no projeto
        self.dir_outputs = Path("outputs")
        self.dir_screenshots = Path("screenshots")
        self.dir_downloads = Path("downloads_temp") # Pasta local temporária
        
        self.dir_outputs.mkdir(exist_ok=True)
        self.dir_screenshots.mkdir(exist_ok=True)
        self.dir_downloads.mkdir(exist_ok=True)
        
        print(f"📁 Pasta de Downloads configurada: {self.dir_downloads.absolute()}")
    
    def _inicializar_driver(self):
        """Inicializa o driver do Selenium com configuração Robustas para Cloud"""
        print("🚀 Inicializando driver...")
        options = webdriver.ChromeOptions()
        
        # Detectar se está rodando no Streamlit Cloud (Linux)
        is_linux = sys.platform.startswith('linux')
        
        # --- Configurações Obrigatórias para Cloud e Estabilidade ---
        if self.headless or is_linux:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-extensions')
        
        # Configurar download para pasta local do projeto
        prefs = {
            "download.default_directory": str(self.dir_downloads.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            if is_linux:
                print("🐧 Detectado ambiente Linux (Streamlit Cloud)")
                options.binary_location = "/usr/bin/chromium"
                service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
            else:
                print("💻 Detectado ambiente local (Windows/Mac)")
                service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 60)
            print("✅ Driver iniciado com sucesso!")

        except Exception as e:
            print(f"❌ Erro fatal ao iniciar o driver: {str(e)}")
            if not is_linux:
                # Tentar fallback básico
                try:
                    self.driver = webdriver.Chrome(options=options)
                    self.wait = WebDriverWait(self.driver, 60)
                except Exception as e2:
                    raise e
            else:
                raise e
    
    def _screenshot(self, nome):
        """Salva screenshot se habilitado"""
        if self.salvar_evidencias and self.driver:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            caminho = self.dir_screenshots / f"{timestamp}_{nome}.png"
            try:
                self.driver.save_screenshot(str(caminho))
                print(f"📸 Screenshot salvo: {nome}")
            except Exception as e:
                print(f"⚠️ Erro ao salvar screenshot: {e}")
    
    def emitir_gnre(self, usuario, senha, dados, callback_progresso=None):
        try:
            if not self.driver:
                self._inicializar_driver()
            
            if callback_progresso: callback_progresso("Acessando formulário GNRE...", 0.1)
            print(f"🌐 Acessando: {self.url_emissao}")
            self.driver.get(self.url_emissao)
            time.sleep(2)
            self._screenshot("01_formulario_inicial")
            
            if callback_progresso: callback_progresso("Preenchendo formulário...", 0.3)
            print("✍️ Preenchendo dados...")
            self._preencher_formulario(dados)
            self._screenshot("02_formulario_preenchido")
            
            if callback_progresso: callback_progresso("Validando dados...", 0.5)
            print("🔍 Validando formulário...")
            self._validar_formulario()
            self._screenshot("03_formulario_validado")
            
            if callback_progresso: callback_progresso("Baixando PDF...", 0.7)
            print("📥 Baixando PDF...")
            pdf_path = self._baixar_pdf(dados['numero_nfe'])
            self._screenshot("04_pdf_baixado")
            
            if callback_progresso: callback_progresso("Preparando próxima...", 0.9)
            print("🔄 Resetando para Nova GNRE...")
            self._nova_gnre()
            
            if callback_progresso: callback_progresso("Concluído!", 1.0)
            
            return {
                'sucesso': True,
                'arquivo_pdf': pdf_path,
                'numero_gnre': 'Gerado',
                'protocolo': None
            }
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            self._screenshot("erro_fatal")
            return {
                'sucesso': False,
                'mensagem': str(e)
            }

    def _preencher_formulario(self, dados):
        try:
            print("⏳ Aguardando página carregar...")
            time.sleep(2)
            
            # 1. UF Favorecida
            print(f"  📍 Selecionando UF: {dados['uf_destino']}")
            select_uf = Select(self.wait.until(EC.presence_of_element_located((By.NAME, "siglaUf"))))
            select_uf.select_by_value(dados['uf_destino'])
            time.sleep(2)

            # 2. GNRE Simples
            try:
                opt = self.wait.until(EC.visibility_of_element_located((By.ID, "optGnreSimples")))
                opt.click()
            except: pass

            # 3. Contribuinte: Não Inscrito
            self.wait.until(EC.element_to_be_clickable((By.ID, "optNaoInscrito"))).click()
            time.sleep(1)

            # 4. Tipo: CNPJ
            self.wait.until(EC.element_to_be_clickable((By.ID, "tipoCNPJ"))).click()
            
            # 5. CNPJ Emitente
            cnpj_limpo = ''.join(filter(str.isdigit, dados['cnpj_emitente']))
            campo_cnpj = self.wait.until(EC.presence_of_element_located((By.ID, "documentoEmitente")))
            campo_cnpj.clear()
            campo_cnpj.send_keys(cnpj_limpo)
            # Forçar change event via JS
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", campo_cnpj)
            time.sleep(1)

            # 6. Razão Social
            campo_razao = self.wait.until(EC.presence_of_element_located((By.ID, "razaoSocialEmitente")))
            campo_razao.clear()
            campo_razao.send_keys(dados.get('razao_social', ''))

            # 7. Endereço
            try:
                campo_end = self.driver.find_element(By.NAME, "gnre.dadosGnre.enderecoEmitente")
            except:
                campo_end = self.driver.find_element(By.ID, "enderecoEmitente")
            campo_end.clear()
            campo_end.send_keys(dados.get('endereco_emitente', ''))

            # 8. UF Emitente
            Select(self.driver.find_element(By.ID, "ufEmitente")).select_by_value(dados.get('uf_emitente', 'CE'))
            time.sleep(1)

            # 9. Município Emitente
            mun = dados.get('municipio_emitente', '')
            try:
                Select(self.driver.find_element(By.NAME, "gnre.dadosGnre.municipioEmitente")).select_by_visible_text(mun.upper())
            except:
                try:
                    Select(self.driver.find_element(By.NAME, "gnre.dadosGnre.municipioEmitente")).select_by_visible_text(mun)
                except:
                    pass

            # 10. CEP
            campo_cep = self.driver.find_element(By.ID, "cepEmitente")
            campo_cep.clear()
            campo_cep.send_keys(''.join(filter(str.isdigit, dados.get('cep_emitente', ''))))

            # 11. Receita 100102
            Select(self.driver.find_element(By.ID, "receita")).select_by_value("100102")
            time.sleep(2)

            # 12. Doc Origem
            Select(self.wait.until(EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.itens[0].documentoOrigem.tipo")))).select_by_value("01")

            # 13. Número Doc
            self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].documentoOrigem.numero").send_keys(dados.get('numero_nfe', ''))

            # 14/15. Mês/Ano
            mes = datetime.now().strftime('%m')
            ano = datetime.now().strftime('%Y')
            Select(self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].mesReferencia")).select_by_value(mes)
            Select(self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].anoReferencia")).select_by_value(ano)

            # 16. Vencimento
            vencimento = calcular_data_vencimento().strftime('%d/%m/%Y')
            campo_venc = self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].dataVencimento")
            campo_venc.clear()
            campo_venc.send_keys(vencimento)

            # 17. Valor
            valor = str(dados.get('valor_icms', '0.00')).replace('.', ',')
            campo_val = self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].valores[0].valor")
            campo_val.clear()
            campo_val.send_keys(valor)

            # 18. Destinatário Não Inscrito
            self.driver.find_element(By.ID, "optNaoInscritoDest").click()
            time.sleep(0.5)
            self.driver.find_element(By.ID, "tipoCPFDest").click()

            # 19/20. CPF e Nome Destinatário
            cpf_dest = ''.join(filter(str.isdigit, dados.get('documento_destinatario', '')))
            self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].destinatarioCpf").send_keys(cpf_dest)
            self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].razaoSocialDestinatario").send_keys(dados.get('nome_destinatario', ''))

            # 21. Município Destinatário
            mun_dest = dados.get('municipio_destinatario', '')
            sel_mun_dest = Select(self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].municipioDestinatario"))
            try:
                sel_mun_dest.select_by_visible_text(mun_dest.upper())
            except:
                sel_mun_dest.select_by_visible_text(mun_dest)

            # 22. Campo Adicional
            if dados.get('chave_nfe_referenciada'):
                self.driver.find_element(By.ID, "campoAdicional00").send_keys(dados['chave_nfe_referenciada'])

            # 23. Pagamento
            self.driver.find_element(By.NAME, "gnre.dadosGnre.dataPagamento").send_keys(vencimento)
            
            print("✅ Formulário preenchido!")

        except Exception as e:
            raise Exception(f"Erro ao preencher: {str(e)}")

    def _validar_formulario(self):
        try:
            print("⚙️ Clicando em Validar...")
            # CORREÇÃO AQUI: Mudado de _salvar_evidencia para _screenshot
            self._screenshot("05_antes_validar")
            
            btn = self.wait.until(EC.element_to_be_clickable((By.NAME, "btnValidar")))
            btn.click()
            
            time.sleep(5)
            # CORREÇÃO AQUI TAMBÉM
            self._screenshot("06_apos_validar")
            
            if "resultado" in self.driver.current_url:
                print("✅ Validação OK (Redirecionado)")
                return
                
            # Verificar erros
            try:
                erros = self.driver.find_elements(By.CLASS_NAME, "erro")
                if erros:
                    msgs = [e.text for e in erros if e.text.strip()]
                    raise Exception(f"Erros no formulário: {', '.join(msgs)}")
            except NoSuchElementException:
                pass
                
        except Exception as e:
            # CORREÇÃO FINAL
            self._screenshot("erro_validacao")
            raise Exception(f"Falha na validação: {str(e)}")

    def _baixar_pdf(self, numero_nfe):
        """Baixa o PDF - Lógica Otimizada"""
        try:
            is_linux = sys.platform.startswith('linux')
            
            wait_curto = WebDriverWait(self.driver, 10)
            btn_baixar = wait_curto.until(EC.presence_of_element_located((By.NAME, "btnBaixar")))
            
            pdf_url = None
            if btn_baixar.tag_name == 'a':
                pdf_url = btn_baixar.get_attribute('href')
            else:
                onclick = btn_baixar.get_attribute('onclick')
                if onclick and 'window.open' in onclick:
                    import re
                    match = re.search(r"window\.open\(['\"]([^'\"]+)['\"]", onclick)
                    if match: pdf_url = match.group(1)

            nome_arquivo = f"GNRE_{numero_nfe}_{datetime.now().strftime('%H%M%S')}.pdf"
            caminho_final = self.dir_downloads / nome_arquivo

            # ESTRATÉGIA 1: Download via Requests
            if pdf_url:
                try:
                    import requests
                    if pdf_url.startswith('/'):
                        base = self.driver.current_url.split('/gnre')[0]
                        pdf_url = base + pdf_url
                    
                    cookies = {c['name']: c['value'] for c in self.driver.get_cookies()}
                    print(f"📥 Baixando via URL direta: {pdf_url}")
                    
                    resp = requests.get(pdf_url, cookies=cookies, timeout=30, verify=False)
                    if resp.status_code == 200:
                        with open(caminho_final, 'wb') as f:
                            f.write(resp.content)
                        return str(caminho_final)
                except Exception as e:
                    print(f"⚠️ Falha no download direto: {e}")

            # ESTRATÉGIA 2: Clique no botão
            print("🖱️ Clicando para baixar...")
            try:
                btn_baixar.click()
            except:
                self.driver.execute_script("arguments[0].click();", btn_baixar)
            
            # Monitorar pasta
            tempo_limite = 20
            inicio = time.time()
            while time.time() - inicio < tempo_limite:
                arquivos = list(self.dir_downloads.glob("*.pdf"))
                if arquivos:
                    recente = max(arquivos, key=os.path.getctime)
                    if (time.time() - os.path.getctime(recente)) < 20:
                        shutil.move(str(recente), str(caminho_final))
                        return str(caminho_final)
                time.sleep(1)
            
            return None

        except Exception as e:
            print(f"❌ Erro no download: {e}")
            return None

    def _nova_gnre(self):
        try:
            self.driver.get(self.url_emissao)
            time.sleep(1)
        except: pass

    def fechar(self):
        if self.driver:
            try:
                self.driver.quit()
            except: pass
            self.driver = None