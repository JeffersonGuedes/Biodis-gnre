"""
Parser de XML para extração de dados da NF-e
"""

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


NS_NFE = 'http://www.portalfiscal.inf.br/nfe'
NSMAP = {'nfe': NS_NFE}


def extrair_dados_nfe(caminho_xml: str) -> Optional[Dict]:
    """
    Extrai todos os campos obrigatórios da NF-e para emissão da GNRE
    
    Args:
        caminho_xml (str): Caminho para o arquivo XML da NF-e
    
    Returns:
        dict: Dicionário com os dados extraídos ou None em caso de erro
    """
    try:
        tree = etree.parse(caminho_xml)
        root = tree.getroot()
        
        # Localizar elementos principais
        nfe = root.find('.//nfe:NFe', namespaces=NSMAP)
        if nfe is None:
            print(f"⚠️ Elemento NFe não encontrado no XML")
            return None
        
        infNFe = nfe.find('nfe:infNFe', namespaces=NSMAP)
        if infNFe is None:
            print(f"⚠️ Elemento infNFe não encontrado no XML")
            return None
        
        # Extrair elementos
        emit = infNFe.find('nfe:emit', namespaces=NSMAP)
        dest = infNFe.find('nfe:dest', namespaces=NSMAP)
        total = infNFe.find('.//nfe:ICMSTot', namespaces=NSMAP)
        ide = infNFe.find('nfe:ide', namespaces=NSMAP)
        
        if not all([elem is not None for elem in [emit, dest, total, ide]]):
            print(f"⚠️ Elementos obrigatórios ausentes no XML")
            return None
        
        # Dados do emitente
        cnpj_emit = _get_text(emit, 'nfe:CNPJ')
        # Garantir que CNPJ está correto (apenas números)
        if cnpj_emit:
            cnpj_emit = ''.join(filter(str.isdigit, cnpj_emit))
            print(f"  🔢 CNPJ Emitente extraído: {cnpj_emit}")
            # Formatar para exibição
            if len(cnpj_emit) == 14:
                cnpj_formatado = f"{cnpj_emit[:2]}.{cnpj_emit[2:5]}.{cnpj_emit[5:8]}/{cnpj_emit[8:12]}-{cnpj_emit[12:]}"
                print(f"  📋 CNPJ Formatado: {cnpj_formatado}")
        
        ie_emit = _get_text(emit, 'nfe:IE')
        uf_emit = _get_text(emit, './/nfe:UF')
        razao_social = _get_text(emit, 'nfe:xNome')
        
        # Endereço do emitente
        endereco_emit = emit.find('nfe:enderEmit', namespaces=NSMAP)
        logradouro = _get_text(endereco_emit, 'nfe:xLgr') if endereco_emit is not None else ''
        numero = _get_text(endereco_emit, 'nfe:nro') if endereco_emit is not None else ''
        complemento = _get_text(endereco_emit, 'nfe:xCpl') if endereco_emit is not None else ''
        bairro = _get_text(endereco_emit, 'nfe:xBairro') if endereco_emit is not None else ''
        municipio_emit = _get_text(endereco_emit, 'nfe:xMun') if endereco_emit is not None else ''
        cep_emit = _get_text(endereco_emit, 'nfe:CEP') if endereco_emit is not None else ''
        
        # Montar endereço completo (sem complemento - removido BIODIS)
        partes_endereco = [logradouro, numero]
        endereco_completo = ', '.join(filter(None, partes_endereco))
        
        # Dados do destinatário
        uf_dest = _get_text(dest, './/nfe:UF')
        nome_dest = _get_text(dest, 'nfe:xNome')
        municipio_dest = _get_text(dest, './/nfe:xMun')
        
        # Verificar se é CPF ou CNPJ
        cpf_dest = _get_text(dest, 'nfe:CPF')
        cnpj_dest = _get_text(dest, 'nfe:CNPJ')
        doc_dest = cnpj_dest if cnpj_dest else cpf_dest
        
        # Dados do ICMS DIFAL
        valor_icms = _get_text(total, 'nfe:vICMSUFDest')
        valor_nf = _get_text(total, 'nfe:vNF')
        
        # Dados da NF-e
        numero_nfe = _get_text(ide, 'nfe:nNF')
        serie_nfe = _get_text(ide, 'nfe:serie')
        dhEmi = _get_text(ide, 'nfe:dhEmi')
        chave_nfe = infNFe.get('Id', '').replace('NFe', '') if infNFe.get('Id') else None
        
        # Chave NF-e Referenciada (se existir)
        ref_nfe = _get_text(ide, './/nfe:refNFe')
        if not ref_nfe:
            # Tentar buscar de outra forma
            try:
                nfref = ide.find('.//nfe:NFref', namespaces=NSMAP)
                if nfref is not None:
                    ref_nfe = _get_text(nfref, 'nfe:refNFe')
            except:
                ref_nfe = None
        
        # Processar data de emissão
        data_emissao = None
        if dhEmi:
            try:
                # Formato: 2025-11-01T03:31:25-03:00
                data_emissao = dhEmi.split('T')[0]
            except:
                data_emissao = None
        
        # Verificar se há valor a recolher
        if not valor_icms or float(valor_icms) == 0:
            print(f"⚠️ Não há DIFAL a recolher (valor ICMS UF Destino = {valor_icms})")
            return None
        
        # Validar campos obrigatórios
        campos_obrigatorios = {
            'uf_destino': uf_dest,
            'cnpj_emitente': cnpj_emit,
            'ie_emitente': ie_emit,
            'numero_nfe': numero_nfe,
            'data_emissao': data_emissao,
            'valor_icms': valor_icms
        }
        
        campos_faltando = [k for k, v in campos_obrigatorios.items() if not v]
        if campos_faltando:
            print(f"⚠️ Campos obrigatórios ausentes: {', '.join(campos_faltando)}")
            return None
        
        # Montar dicionário de dados
        dados = {
            # Campos obrigatórios para GNRE
            'uf_destino': uf_dest,                     # c01_UfFavorecida
            'codigo_receita': '100102',                # c02_receita (ICMS DIFAL)
            'cnpj_emitente': cnpj_emit,                # c03_idContribuinteEmitente
            'tipo_documento': '2',                     # c04_tipoDocumentoOrigem (NF-e = 2)
            'numero_nfe': numero_nfe,                  # c05_numeroDocumento
            'data_emissao': data_emissao,              # c06_dataEmissao
            'valor_icms': valor_icms,                  # c10_valorPrincipal
            'data_vencimento': data_emissao,           # c14_dataVencimento (igual emissão)
            'ie_emitente': ie_emit,                    # c17_inscricaoEstadual
            
            # Campos adicionais
            'uf_emitente': uf_emit,
            'razao_social': razao_social,
            'nome_destinatario': nome_dest,
            'municipio_destinatario': municipio_dest,
            'documento_destinatario': doc_dest,
            'chave_nfe': chave_nfe,
            'chave_nfe_referenciada': ref_nfe,
            'serie_nfe': serie_nfe,
            'valor_nf': valor_nf,
            
            # Dados de endereço do emitente
            'endereco_emitente': endereco_completo,
            'bairro_emitente': bairro,
            'municipio_emitente': municipio_emit,
            'cep_emitente': cep_emit,
        }
        
        return dados
        
    except Exception as e:
        print(f"❌ Erro ao extrair dados do XML: {e}")
        return None


def processar_multiplos_xmls(arquivos: List[str]) -> List[Dict]:
    """
    Processa múltiplos arquivos XML
    
    Args:
        arquivos: Lista de caminhos para arquivos XML
    
    Returns:
        Lista de dicionários com dados extraídos
    """
    resultados = []
    
    for arquivo in arquivos:
        nome_arquivo = Path(arquivo).name
        print(f"\n📄 Processando: {nome_arquivo}")
        
        dados = extrair_dados_nfe(arquivo)
        
        if dados:
            resultados.append({
                'arquivo': nome_arquivo,
                'status': 'sucesso',
                'dados': dados
            })
            print(f"✅ {nome_arquivo}: Dados extraídos com sucesso")
        else:
            resultados.append({
                'arquivo': nome_arquivo,
                'status': 'erro',
                'dados': None,
                'mensagem': 'Não foi possível extrair dados ou não há DIFAL'
            })
            print(f"❌ {nome_arquivo}: Falha na extração")
    
    return resultados


def validar_xml_nfe(caminho_xml: str) -> tuple[bool, str]:
    """
    Valida se o arquivo é um XML de NF-e válido
    
    Args:
        caminho_xml: Caminho para o arquivo XML
    
    Returns:
        tuple: (válido, mensagem)
    """
    try:
        # Verificar se arquivo existe
        if not Path(caminho_xml).exists():
            return False, "Arquivo não encontrado"
        
        # Tentar fazer parse do XML
        tree = etree.parse(caminho_xml)
        root = tree.getroot()
        
        # Verificar namespace
        if NS_NFE not in str(root.tag):
            return False, "Não é um XML de NF-e (namespace incorreto)"
        
        # Verificar elemento NFe
        nfe = root.find('.//nfe:NFe', namespaces=NSMAP)
        if nfe is None:
            return False, "Elemento NFe não encontrado"
        
        return True, "XML válido"
        
    except etree.ParseError as e:
        return False, f"Erro ao fazer parse do XML: {str(e)}"
    except Exception as e:
        return False, f"Erro na validação: {str(e)}"


def _get_text(element, xpath: str) -> Optional[str]:
    """
    Helper para extrair texto de um elemento XML
    
    Args:
        element: Elemento XML
        xpath: Caminho XPath
    
    Returns:
        Texto do elemento ou None
    """
    try:
        elem = element.find(xpath, namespaces=NSMAP)
        return elem.text if elem is not None else None
    except:
        return None


def formatar_dados_para_visualizacao(dados: Dict) -> Dict:
    """
    Formata dados extraídos para exibição
    
    Args:
        dados: Dicionário com dados extraídos
    
    Returns:
        Dicionário formatado
    """
    try:
        valor_icms = float(dados.get('valor_icms', 0))
        valor_nf = float(dados.get('valor_nf', 0))
        
        return {
            'NF-e': dados.get('numero_nfe', '-'),
            'Série': dados.get('serie_nfe', '-'),
            'Data Emissão': dados.get('data_emissao', '-'),
            'Emitente': dados.get('razao_social', '-'),
            'CNPJ Emitente': dados.get('cnpj_emitente', '-'),
            'IE Emitente': dados.get('ie_emitente', '-'),
            'UF Emitente': dados.get('uf_emitente', '-'),
            'Destinatário': dados.get('nome_destinatario', '-'),
            'UF Destino': dados.get('uf_destino', '-'),
            'Valor NF': f"R$ {valor_nf:,.2f}",
            'Valor ICMS DIFAL': f"R$ {valor_icms:,.2f}",
            'Chave NF-e': dados.get('chave_nfe', '-'),
        }
    except Exception as e:
        print(f"Erro ao formatar dados: {e}")
        return dados