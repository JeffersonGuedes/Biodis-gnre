"""
Bot de automação para emissão de GNRE no portal
BLINDADO CONTRA ERROS "ELEMENT NOT INTERACTABLE" - VERSÃO STREAMLIT CLOUD
"""

import time
import os
import sys
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# ==============================================================================
# CONSTANTES E DATAS
# ==============================================================================

FERIADOS_2025 = [datetime(2025, 1, 1), datetime(2025, 2, 24), datetime(2025, 2, 25), datetime(2025, 4, 18), datetime(2025, 4, 21), datetime(2025, 5, 1), datetime(2025, 6, 19), datetime(2025, 9, 7), datetime(2025, 10, 12), datetime(2025, 11, 2), datetime(2025, 11, 15), datetime(2025, 12, 25)]
FERIADOS_2026 = [datetime(2026, 1, 1), datetime(2026, 2, 16), datetime(2026, 2, 17), datetime(2026, 4, 3), datetime(2026, 4, 21), datetime(2026, 5, 1), datetime(2026, 6, 4), datetime(2026, 9, 7), datetime(2026, 10, 12), datetime(2026, 11, 2), datetime(2026, 11, 15), datetime(2026, 12, 25)]
FERIADOS = FERIADOS_2025 + FERIADOS_2026

def calcular_data_vencimento():
    agora = datetime.now()
    if agora.hour >= 13:
        data = agora + timedelta(days=1)
    else:
        data = agora
    return ajustar_para_dia_util(data)

def ajustar_para_dia_util(data):
    data_sem_hora = data.replace(hour=0, minute=0, second=0, microsecond=0)
    for _ in range(10):
        if data_sem_hora.weekday() >= 5 or eh_feriado(data_sem_hora):
            data_sem_hora += timedelta(days=1 if data_sem_hora.weekday() < 6 else (7 - data_sem_hora.weekday()))
            continue
        break
    return data_sem_hora

def eh_feriado(data):
    return data.replace(hour=0, minute=0, second=0, microsecond=0) in FERIADOS

# ==============================================================================
# CLASSE DO BOT BLINDADO
# ==============================================================================

class GNREBot:
    def __init__(self, headless=False, salvar_evidencias=True):
        self.headless = headless
        self.salvar_evidencias = salvar_evidencias
        self.driver = None
        self.wait = None
        self.url_emissao = "https://www.gnre.pe.gov.br:444/gnre/v/guia/index"
        
        self.dir_outputs = Path("outputs")
        self.dir_screenshots = Path("screenshots")
        self.dir_downloads = Path.home() / "Downloads"
        
        self.dir_outputs.mkdir(exist_ok=True)
        self.dir_screenshots.mkdir(exist_ok=True)

    def _inicializar_driver(self):
        print("🚀 Inicializando driver...")
        options = webdriver.ChromeOptions()
        is_linux = sys.platform.startswith('linux')
        
        if self.headless or is_linux:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--ignore-certificate-errors')
        
        prefs = {
            "download.default_directory": str(self.dir_downloads.absolute()),
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            if is_linux:
                print("🐧 Linux Cloud Detectado")
                options.binary_location = "/usr/bin/chromium"
                service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
            else:
                service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 60)  # AUMENTADO para Cloud
            print("✅ Driver OK")
        except Exception as e:
            raise Exception(f"Erro driver: {e}")

    def _clicar_seguro(self, locator_tuple=None, element=None, nome_elemento="elemento", max_tentativas=3):
        """Tenta clicar com múltiplas estratégias e retries"""
        for tentativa in range(max_tentativas):
            try:
                # 1. Obter elemento
                if element is None:
                    try:
                        element = self.wait.until(EC.element_to_be_clickable(locator_tuple))
                    except TimeoutException:
                        element = self.wait.until(EC.presence_of_element_located(locator_tuple))
                
                # 2. Verificar se está habilitado (para radios/checkboxes)
                if element.tag_name in ['input']:
                    for _ in range(15):  # Esperar até 7.5s
                        if element.is_enabled() and element.is_displayed():
                            break
                        time.sleep(0.5)
                
                # 3. Forçar visibilidade
                try:
                    self.driver.execute_script("""
                        arguments[0].style.display = 'block';
                        arguments[0].style.visibility = 'visible';
                        arguments[0].style.opacity = '1';
                        arguments[0].disabled = false;
                    """, element)
                except:
                    pass
                
                # 4. Scroll
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", element)
                    time.sleep(1)
                except:
                    pass

                # 5. TENTATIVA 1: JavaScript Click (mais confiável)
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    time.sleep(0.5)
                    print(f"  ✅ {nome_elemento} OK (JS)")
                    return True
                except Exception as e_js:
                    if tentativa < max_tentativas - 1:
                        print(f"  ⚠️ JS falhou tentativa {tentativa+1}: {e_js}")

                # 6. TENTATIVA 2: Click normal
                try:
                    element.click()
                    time.sleep(0.5)
                    print(f"  ✅ {nome_elemento} OK (normal)")
                    return True
                except Exception as e_click:
                    if tentativa < max_tentativas - 1:
                        print(f"  ⚠️ Click falhou tentativa {tentativa+1}: {e_click}")

                # 7. TENTATIVA 3: ActionChains
                try:
                    actions = ActionChains(self.driver)
                    actions.move_to_element(element).pause(0.5).click().perform()
                    time.sleep(0.5)
                    print(f"  ✅ {nome_elemento} OK (ActionChains)")
                    return True
                except Exception as e_action:
                    if tentativa < max_tentativas - 1:
                        print(f"  ⚠️ ActionChains falhou tentativa {tentativa+1}: {e_action}")

                # Se chegou aqui e não é a última tentativa, aguardar e re-localizar elemento
                if tentativa < max_tentativas - 1:
                    print(f"  🔄 Aguardando antes de tentar novamente...")
                    time.sleep(2)
                    element = None  # Forçar re-localização

            except Exception as e:
                if tentativa < max_tentativas - 1:
                    print(f"  ⚠️ Tentativa {tentativa+1} falhou: {str(e)}")
                    time.sleep(2)
                else:
                    print(f"  ❌ TODAS tentativas falharam para {nome_elemento}: {str(e)}")
                    self._screenshot(f"erro_clique_{nome_elemento}")
                    raise Exception(f"Impossível interagir com {nome_elemento} após {max_tentativas} tentativas: {str(e)}")
        
        return False

    def _aguardar_loading(self):
        time.sleep(1.5)

    def _screenshot(self, nome):
        if self.salvar_evidencias and self.driver:
            caminho = self.dir_screenshots / f"{datetime.now().strftime('%H%M%S')}_{nome}.png"
            try:
                self.driver.save_screenshot(str(caminho))
            except:
                pass

    def emitir_gnre(self, usuario, senha, dados, callback_progresso=None):
        try:
            if not self.driver:
                self._inicializar_driver()
            
            if callback_progresso:
                callback_progresso("Acessando...", 0.1)
            self.driver.get(self.url_emissao)
            self._aguardar_loading()
            
            if callback_progresso:
                callback_progresso("Preenchendo...", 0.3)
            self._preencher_formulario(dados)
            self._screenshot("01_preenchido")
            
            if callback_progresso:
                callback_progresso("Validando...", 0.5)
            self._validar_formulario()
            self._screenshot("02_validado")
            
            if callback_progresso:
                callback_progresso("Baixando...", 0.8)
            pdf = self._baixar_pdf(dados['numero_nfe'])
            
            self._nova_gnre()
            if callback_progresso:
                callback_progresso("Fim!", 1.0)
            
            return {'sucesso': True, 'arquivo_pdf': pdf}
            
        except Exception as e:
            print(f"❌ Erro Geral: {e}")
            self._screenshot("erro_fatal")
            return {'sucesso': False, 'mensagem': str(e)}

    def _preencher_formulario(self, dados):
        """Preenchimento Otimizado com _clicar_seguro"""
        try:
            # 1. UF Favorecida
            print(f"📍 UF Destino: {dados['uf_destino']}")
            elem_uf = self.wait.until(EC.presence_of_element_located((By.NAME, "siglaUf")))
            Select(elem_uf).select_by_value(dados['uf_destino'])
            print(f"  📍 Aguardando AJAX carregar municípios...")
            time.sleep(3.5)  # AUMENTADO: AJAX da UF

            # 2. GNRE Simples (Radio)
            print("📄 Aguardando radio GNRE Simples...")
            time.sleep(1)
            radio_simples = self.wait.until(EC.element_to_be_clickable((By.ID, "optGnreSimples")))
            self._clicar_seguro(element=radio_simples, nome_elemento="Radio Simples", max_tentativas=3)
            time.sleep(1.5)

            # 3. Contribuinte: Não Inscrito (Radio)
            print("👤 Aguardando radio Não Inscrito...")
            time.sleep(1)
            radio_nao_inscrito = self.wait.until(EC.element_to_be_clickable((By.ID, "optNaoInscrito")))
            self._clicar_seguro(element=radio_nao_inscrito, nome_elemento="Radio Nao Inscrito", max_tentativas=3)
            time.sleep(1.5)
            
            # 4. Tipo Doc: CNPJ (Radio)
            print("🏢 Aguardando radio CNPJ...")
            time.sleep(1)
            radio_cnpj = self.wait.until(EC.element_to_be_clickable((By.ID, "tipoCNPJ")))
            self._clicar_seguro(element=radio_cnpj, nome_elemento="Radio CNPJ", max_tentativas=3)
            time.sleep(1.5)

            # 5. CNPJ Emitente
            cnpj = ''.join(filter(str.isdigit, dados['cnpj_emitente']))
            elem_cnpj = self.wait.until(EC.visibility_of_element_located((By.ID, "documentoEmitente")))
            elem_cnpj.clear()
            elem_cnpj.send_keys(cnpj)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", elem_cnpj)
            time.sleep(1)

            # 6. Razão Social
            self.driver.find_element(By.ID, "razaoSocialEmitente").send_keys(dados.get('razao_social', ''))

            # 7. Endereço
            try:
                elem_end = self.driver.find_element(By.ID, "enderecoEmitente")
            except:
                elem_end = self.driver.find_element(By.NAME, "gnre.dadosGnre.enderecoEmitente")
            elem_end.send_keys(dados.get('endereco_emitente', ''))

            # 8. UF Emitente
            Select(self.driver.find_element(By.ID, "ufEmitente")).select_by_value(dados.get('uf_emitente', 'CE'))
            time.sleep(1)

            # 9. Município Emitente
            try:
                mun = dados.get('municipio_emitente', '').upper()
                Select(self.driver.find_element(By.NAME, "gnre.dadosGnre.municipioEmitente")).select_by_visible_text(mun)
            except:
                pass

            # 10. CEP
            self.driver.find_element(By.ID, "cepEmitente").send_keys(''.join(filter(str.isdigit, dados.get('cep_emitente', ''))))

            # 11. Receita 100102
            print(f"  💰 Selecionando Receita 100102...")
            Select(self.driver.find_element(By.ID, "receita")).select_by_value("100102")
            print(f"  💰 Aguardando AJAX carregar campos da receita...")
            time.sleep(3.5)  # AUMENTADO: AJAX da Receita

            # 12. Doc Origem
            elem_doc = self.wait.until(EC.presence_of_element_located((By.NAME, "gnre.dadosGnre.itens[0].documentoOrigem.tipo")))
            Select(elem_doc).select_by_value("01")

            # 13. Número Doc
            self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].documentoOrigem.numero").send_keys(dados.get('numero_nfe', ''))

            # 14/15 Data Ref
            mes, ano = datetime.now().strftime('%m'), datetime.now().strftime('%Y')
            Select(self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].mesReferencia")).select_by_value(mes)
            Select(self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].anoReferencia")).select_by_value(ano)

            # 16. Vencimento
            venc = calcular_data_vencimento().strftime('%d/%m/%Y')
            self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].dataVencimento").send_keys(venc)

            # 17. Valor
            valor = str(dados.get('valor_icms', '0.00')).replace('.', ',')
            elem_valor = self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].valores[0].valor")
            elem_valor.clear()
            time.sleep(0.5)
            elem_valor.send_keys(valor)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", elem_valor)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('blur'));", elem_valor)
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('input'));", elem_valor)
            print(f"  💰 Valor preenchido: {valor} - Aguardando habilitar campos...")
            time.sleep(3.5)  # AUMENTADO: Aguardar processamento completo

            # 18. Destinatário Não Inscrito (ESPERA ULTRA-LONGA)
            print("👤 Aguardando formulário processar valor e habilitar Destinatário...")
            
            # Espera extra para garantir que AJAX terminou
            time.sleep(2)
            
            # Localizar elemento
            radio_dest = self.wait.until(EC.presence_of_element_located((By.ID, "optNaoInscritoDest")))
            
            # Loop de verificação AUMENTADO
            habilitado = False
            for tentativa in range(20):  # 20 tentativas = 10 segundos
                try:
                    if radio_dest.is_enabled() and radio_dest.is_displayed():
                        # Verificar também se não está readonly
                        readonly = self.driver.execute_script("return arguments[0].readOnly || arguments[0].disabled;", radio_dest)
                        if not readonly:
                            habilitado = True
                            print(f"  ✅ Destinatário habilitado após {tentativa * 0.5}s")
                            break
                except:
                    pass
                time.sleep(0.5)
            
            if not habilitado:
                print("  ⚠️ Destinatário pode não estar habilitado, tentando mesmo assim...")
            
            print("👤 Selecionando Destinatário Não Inscrito...")
            self._clicar_seguro(element=radio_dest, nome_elemento="Radio Destinatário", max_tentativas=5)
            time.sleep(2)
            
            # 19. CPF Destinatário (ESPERA EXTRA)
            print("👤 Aguardando radio CPF habilitar...")
            time.sleep(1.5)
            
            radio_cpf = self.wait.until(EC.presence_of_element_located((By.ID, "tipoCPFDest")))
            
            # Loop de verificação
            for tentativa in range(20):
                try:
                    if radio_cpf.is_enabled() and radio_cpf.is_displayed():
                        readonly = self.driver.execute_script("return arguments[0].readOnly || arguments[0].disabled;", radio_cpf)
                        if not readonly:
                            print(f"  ✅ Radio CPF habilitado após {tentativa * 0.5}s")
                            break
                except:
                    pass
                time.sleep(0.5)
            
            print("👤 Selecionando CPF...")
            self._clicar_seguro(element=radio_cpf, nome_elemento="Radio CPF", max_tentativas=5)
            time.sleep(1.5)

            # 20. CPF
            cpf_dest = ''.join(filter(str.isdigit, dados.get('documento_destinatario', '')))
            self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].destinatarioCpf").send_keys(cpf_dest)

            # 21. Nome Destinatário
            self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].razaoSocialDestinatario").send_keys(dados.get('nome_destinatario', ''))

            # 22. Município Destino
            try:
                mun_dest = dados.get('municipio_destinatario', '').upper()
                Select(self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].municipioDestinatario")).select_by_visible_text(mun_dest)
            except:
                pass

            # 23. Campo Adicional
            if dados.get('chave_nfe_referenciada'):
                try:
                    self.driver.find_element(By.ID, "campoAdicional00").send_keys(dados['chave_nfe_referenciada'])
                except:
                    pass

            # 24. Pagamento
            self.driver.find_element(By.NAME, "gnre.dadosGnre.dataPagamento").send_keys(venc)

            print("✅ Formulário preenchido")

        except Exception as e:
            self._screenshot("erro_preenchimento")
            raise Exception(f"Erro preenchimento: {e}")

    def _validar_formulario(self):
        print("⚙️ Validando...")
        self._clicar_seguro(locator_tuple=(By.NAME, "btnValidar"), nome_elemento="Botão Validar")
        time.sleep(5)
        
        erros = self.driver.find_elements(By.CLASS_NAME, "erro")
        if erros:
            msgs = [e.text for e in erros if e.text.strip()]
            if msgs:
                raise Exception(f"Erro Validação: {', '.join(msgs)}")

    def _baixar_pdf(self, nfe):
        try:
            try:
                self._clicar_seguro(locator_tuple=(By.NAME, "btnBaixar"), nome_elemento="Botão Baixar")
            except:
                print("Botão baixar não encontrado...")

            nome_final = self.dir_downloads / f"GNRE_{nfe}.pdf"
            for _ in range(20):
                arquivos = list(self.dir_downloads.glob("*.pdf"))
                if arquivos:
                    recente = max(arquivos, key=os.path.getctime)
                    if (time.time() - os.path.getctime(recente)) < 20:
                        shutil.move(str(recente), str(nome_final))
                        return str(nome_final)
                time.sleep(1)
            return None
        except Exception as e:
            print(f"Erro download: {e}")
            return None

    def _nova_gnre(self):
        try:
            self.driver.get(self.url_emissao)
        except:
            pass

    def fechar(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
