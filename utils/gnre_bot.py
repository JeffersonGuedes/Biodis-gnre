"""
Bot de automação para emissão de GNRE no portal
BLINDADO CONTRA ERROS "ELEMENT NOT INTERACTABLE" - VERSÃO 2.0
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# ==============================================================================
# CONSTANTES E DATAS
# ==============================================================================

FERIADOS_2025 = [datetime(2025, 1, 1), datetime(2025, 2, 24), datetime(2025, 2, 25), datetime(2025, 4, 18), datetime(2025, 4, 21), datetime(2025, 5, 1), datetime(2025, 6, 19), datetime(2025, 9, 7), datetime(2025, 10, 12), datetime(2025, 11, 2), datetime(2025, 11, 15), datetime(2025, 12, 25)]
FERIADOS = FERIADOS_2025 

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
        self.dir_downloads = Path("downloads_temp")
        
        self.dir_outputs.mkdir(exist_ok=True)
        self.dir_screenshots.mkdir(exist_ok=True)
        self.dir_downloads.mkdir(exist_ok=True)

    def _inicializar_driver(self):
        print("🚀 Inicializando driver...")
        options = webdriver.ChromeOptions()
        is_linux = sys.platform.startswith('linux')
        
        if self.headless or is_linux:
            options.add_argument('--headless')
        
        # Argumentos cruciais para evitar erros de renderização
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
            self.wait = WebDriverWait(self.driver, 40)
            print("✅ Driver OK")
        except Exception as e:
            raise Exception(f"Erro driver: {e}")

    # --- NOVA LÓGICA DE CLIQUE MAIS AGRESSIVA ---
    def _clicar_seguro(self, locator_tuple=None, element=None, nome_elemento="elemento"):
        """
        Tenta clicar de 3 formas diferentes para garantir a interação
        """
        try:
            # 1. Obter o elemento se não foi passado
            if element is None:
                # Usar presence, pois element_to_be_clickable falha se o elemento estiver coberto
                element = self.wait.until(EC.presence_of_element_located(locator_tuple))
            
            # 2. Scroll para garantir que está na viewport
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)

            # 3. Tentativa Nuclear: JavaScript direto (Melhor para Headless)
            # Em headless, cliques normais falham muito em inputs escondidos/estilizados
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return # Se o JS funcionou, ótimo
            except Exception as e_js:
                print(f"  ⚠️ JS Click falhou para {nome_elemento}: {e_js}")

            # 4. Se JS falhou (raro), tenta clique normal ActionChains
            try:
                element.click()
            except Exception:
                # Última tentativa: ActionChains
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                actions.move_to_element(element).click().perform()

        except Exception as e:
            # Se tudo falhar, não crasha imediatamente, tenta seguir
            print(f"  ❌ Erro ao clicar em {nome_elemento}: {str(e)}")
            # Salva print para debug
            self._screenshot(f"erro_clique_{nome_elemento}")
            raise Exception(f"Impossível interagir com {nome_elemento}: {str(e)}")

    def _aguardar_loading(self):
        """Espera cega para garantir que animações terminaram"""
        time.sleep(1.5)

    def _screenshot(self, nome):
        if self.salvar_evidencias and self.driver:
            caminho = self.dir_screenshots / f"{datetime.now().strftime('%H%M%S')}_{nome}.png"
            try: self.driver.save_screenshot(str(caminho))
            except: pass

    def emitir_gnre(self, usuario, senha, dados, callback_progresso=None):
        try:
            if not self.driver: self._inicializar_driver()
            
            if callback_progresso: callback_progresso("Acessando...", 0.1)
            self.driver.get(self.url_emissao)
            self._aguardar_loading()
            
            if callback_progresso: callback_progresso("Preenchendo...", 0.3)
            self._preencher_formulario(dados)
            self._screenshot("01_preenchido")
            
            if callback_progresso: callback_progresso("Validando...", 0.5)
            self._validar_formulario()
            self._screenshot("02_validado")
            
            if callback_progresso: callback_progresso("Baixando...", 0.8)
            pdf = self._baixar_pdf(dados['numero_nfe'])
            
            self._nova_gnre()
            if callback_progresso: callback_progresso("Fim!", 1.0)
            
            return {'sucesso': True, 'arquivo_pdf': pdf}
            
        except Exception as e:
            print(f"❌ Erro Geral: {e}")
            self._screenshot("erro_fatal")
            return {'sucesso': False, 'mensagem': str(e)}

    def _preencher_formulario(self, dados):
        """Preenchimento Otimizado"""
        try:
            # 1. UF Favorecida
            print(f"📍 UF Destino: {dados['uf_destino']}")
            elem_uf = self.wait.until(EC.presence_of_element_located((By.NAME, "siglaUf")))
            Select(elem_uf).select_by_value(dados['uf_destino'])
            time.sleep(2.5) # AUMENTEI O TEMPO: Carregamento AJAX da UF demora

            # 2. GNRE Simples (Radio)
            # Tentar clicar no LABEL se o ID falhar, ou usar JS no ID
            try:
                radio_simples = self.driver.find_element(By.ID, "optGnreSimples")
                self._clicar_seguro(element=radio_simples, nome_elemento="Radio Simples")
            except: pass 

            # 3. Contribuinte: Não Inscrito (Radio)
            time.sleep(1)
            self._clicar_seguro(locator_tuple=(By.ID, "optNaoInscrito"), nome_elemento="Radio Nao Inscrito")
            
            # 4. Tipo Doc: CNPJ (Radio)
            time.sleep(0.5)
            self._clicar_seguro(locator_tuple=(By.ID, "tipoCNPJ"), nome_elemento="Radio CNPJ")

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
            try: elem_end = self.driver.find_element(By.ID, "enderecoEmitente")
            except: elem_end = self.driver.find_element(By.NAME, "gnre.dadosGnre.enderecoEmitente")
            elem_end.send_keys(dados.get('endereco_emitente', ''))

            # 8. UF Emitente
            Select(self.driver.find_element(By.ID, "ufEmitente")).select_by_value(dados.get('uf_emitente', 'CE'))
            time.sleep(1)

            # 9. Município Emitente
            try:
                mun = dados.get('municipio_emitente', '').upper()
                Select(self.driver.find_element(By.NAME, "gnre.dadosGnre.municipioEmitente")).select_by_visible_text(mun)
            except: pass

            # 10. CEP
            self.driver.find_element(By.ID, "cepEmitente").send_keys(''.join(filter(str.isdigit, dados.get('cep_emitente', ''))))

            # 11. Receita 100102
            Select(self.driver.find_element(By.ID, "receita")).select_by_value("100102")
            time.sleep(2.5) # AUMENTEI O TEMPO: Carregamento AJAX da Receita

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
            elem_valor.send_keys(valor)
            # Forçar update do valor
            self.driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", elem_valor)
            time.sleep(1) # Esperar o site processar o valor para habilitar o destinatário

            # 18. Destinatário Não Inscrito (O PONTO DE ERRO)
            print("👤 Selecionando Destinatário...")
            self._clicar_seguro(locator_tuple=(By.ID, "optNaoInscritoDest"), nome_elemento="Radio Destinatário Nao Inscrito")
            
            time.sleep(1)
            self._clicar_seguro(locator_tuple=(By.ID, "tipoCPFDest"), nome_elemento="Radio CPF Destinatário")

            # 19. CPF Destinatário
            cpf_dest = ''.join(filter(str.isdigit, dados.get('documento_destinatario', '')))
            self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].destinatarioCpf").send_keys(cpf_dest)

            # 20. Nome Destinatário
            self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].razaoSocialDestinatario").send_keys(dados.get('nome_destinatario', ''))

            # 21. Município Destino
            try:
                mun_dest = dados.get('municipio_destinatario', '').upper()
                Select(self.driver.find_element(By.NAME, "gnre.dadosGnre.itens[0].municipioDestinatario")).select_by_visible_text(mun_dest)
            except: pass

            # 22. Campo Adicional
            if dados.get('chave_nfe_referenciada'):
                try: self.driver.find_element(By.ID, "campoAdicional00").send_keys(dados['chave_nfe_referenciada'])
                except: pass

            # 23. Pagamento
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
            if msgs: raise Exception(f"Erro Validação: {', '.join(msgs)}")

    def _baixar_pdf(self, nfe):
        try:
            try:
                self._clicar_seguro(locator_tuple=(By.NAME, "btnBaixar"), nome_elemento="Botão Baixar")
            except: 
                print("Botão baixar não encontrado, tentando url direta...")

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
        try: self.driver.get(self.url_emissao)
        except: pass

    def fechar(self):
        if self.driver:
            self.driver.quit()
            self.driver = None