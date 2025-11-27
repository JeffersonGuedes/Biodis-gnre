"""
Validadores para dados de GNRE
"""

import re
from datetime import datetime
from typing import Optional, Tuple

try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree


# Códigos de UF válidos
UFS_VALIDAS = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]


# Códigos de receita GNRE mais comuns
CODIGOS_RECEITA = {
    '100102': 'ICMS DIFAL - Diferencial de Alíquota',
    '100099': 'ICMS Substituição Tributária',
    '100048': 'ICMS Comunicação',
    '100153': 'ICMS Antecipação',
}


def validar_cnpj(cnpj: str) -> Tuple[bool, str]:
    """
    Valida CNPJ
    
    Args:
        cnpj: CNPJ a validar
    
    Returns:
        tuple: (válido, mensagem)
    """
    if not cnpj:
        return False, "CNPJ não informado"
    
    # Remover caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    # Verificar tamanho
    if len(cnpj) != 14:
        return False, f"CNPJ deve ter 14 dígitos (fornecido: {len(cnpj)})"
    
    # Verificar se todos os dígitos são iguais
    if len(set(cnpj)) == 1:
        return False, "CNPJ inválido (todos os dígitos iguais)"
    
    # Validar dígitos verificadores
    try:
        # Primeiro dígito verificador
        soma = sum(int(cnpj[i]) * peso for i, peso in enumerate([5,4,3,2,9,8,7,6,5,4,3,2]))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if int(cnpj[12]) != digito1:
            return False, "CNPJ inválido (primeiro dígito verificador)"
        
        # Segundo dígito verificador
        soma = sum(int(cnpj[i]) * peso for i, peso in enumerate([6,5,4,3,2,9,8,7,6,5,4,3,2]))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        if int(cnpj[13]) != digito2:
            return False, "CNPJ inválido (segundo dígito verificador)"
        
        return True, "CNPJ válido"
        
    except Exception as e:
        return False, f"Erro ao validar CNPJ: {str(e)}"


def validar_cpf(cpf: str) -> Tuple[bool, str]:
    """
    Valida CPF
    
    Args:
        cpf: CPF a validar
    
    Returns:
        tuple: (válido, mensagem)
    """
    if not cpf:
        return False, "CPF não informado"
    
    # Remover caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verificar tamanho
    if len(cpf) != 11:
        return False, f"CPF deve ter 11 dígitos (fornecido: {len(cpf)})"
    
    # Verificar se todos os dígitos são iguais
    if len(set(cpf)) == 1:
        return False, "CPF inválido (todos os dígitos iguais)"
    
    # Validar dígitos verificadores
    try:
        # Primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if int(cpf[9]) != digito1:
            return False, "CPF inválido (primeiro dígito verificador)"
        
        # Segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        if int(cpf[10]) != digito2:
            return False, "CPF inválido (segundo dígito verificador)"
        
        return True, "CPF válido"
        
    except Exception as e:
        return False, f"Erro ao validar CPF: {str(e)}"


def validar_uf(uf: str) -> Tuple[bool, str]:
    """
    Valida código de UF
    
    Args:
        uf: Código da UF (2 letras)
    
    Returns:
        tuple: (válido, mensagem)
    """
    if not uf:
        return False, "UF não informada"
    
    uf = uf.upper().strip()
    
    if len(uf) != 2:
        return False, f"UF deve ter 2 caracteres (fornecido: '{uf}')"
    
    if uf not in UFS_VALIDAS:
        return False, f"UF inválida: '{uf}'"
    
    return True, "UF válida"


def validar_data(data_str: str, formato: str = "%Y-%m-%d") -> Tuple[bool, str]:
    """
    Valida formato de data
    
    Args:
        data_str: String com data
        formato: Formato esperado (padrão: YYYY-MM-DD)
    
    Returns:
        tuple: (válido, mensagem)
    """
    if not data_str:
        return False, "Data não informada"
    
    try:
        data = datetime.strptime(data_str, formato)
        
        # Verificar se data não é muito antiga ou futura
        hoje = datetime.now()
        anos_diff = abs((hoje - data).days / 365)
        
        if anos_diff > 10:
            return False, f"Data muito distante ({data_str})"
        
        return True, "Data válida"
        
    except ValueError:
        return False, f"Formato de data inválido (esperado: {formato})"
    except Exception as e:
        return False, f"Erro ao validar data: {str(e)}"


def validar_valor(valor_str: str, minimo: float = 0.01, maximo: float = 999999999.99) -> Tuple[bool, str]:
    """
    Valida valor monetário
    
    Args:
        valor_str: String com valor
        minimo: Valor mínimo permitido
        maximo: Valor máximo permitido
    
    Returns:
        tuple: (válido, mensagem)
    """
    if not valor_str:
        return False, "Valor não informado"
    
    try:
        # Substituir vírgula por ponto se necessário
        valor_str = str(valor_str).replace(',', '.')
        valor = float(valor_str)
        
        if valor < minimo:
            return False, f"Valor abaixo do mínimo permitido (R$ {minimo:.2f})"
        
        if valor > maximo:
            return False, f"Valor acima do máximo permitido (R$ {maximo:.2f})"
        
        return True, f"Valor válido: R$ {valor:.2f}"
        
    except ValueError:
        return False, f"Valor inválido: '{valor_str}'"
    except Exception as e:
        return False, f"Erro ao validar valor: {str(e)}"


def validar_codigo_receita(codigo: str) -> Tuple[bool, str]:
    """
    Valida código de receita GNRE
    
    Args:
        codigo: Código da receita
    
    Returns:
        tuple: (válido, mensagem)
    """
    if not codigo:
        return False, "Código de receita não informado"
    
    codigo = codigo.strip()
    
    if codigo in CODIGOS_RECEITA:
        return True, f"{codigo} - {CODIGOS_RECEITA[codigo]}"
    
    # Verificar formato básico (6 dígitos)
    if re.match(r'^\d{6}$', codigo):
        return True, f"Código de receita: {codigo}"
    
    return False, f"Código de receita inválido: '{codigo}'"


def validar_inscricao_estadual(ie: str, uf: str = None) -> Tuple[bool, str]:
    """
    Valida Inscrição Estadual
    
    Args:
        ie: Inscrição Estadual
        uf: UF (opcional, para validação específica)
    
    Returns:
        tuple: (válido, mensagem)
    """
    if not ie:
        return False, "Inscrição Estadual não informada"
    
    # Remover caracteres não alfanuméricos
    ie = re.sub(r'[^0-9A-Za-z]', '', ie)
    
    # Verificar se é "ISENTO"
    if ie.upper() == "ISENTO":
        return True, "IE: ISENTO"
    
    # Verificar tamanho mínimo
    if len(ie) < 8:
        return False, f"IE muito curta (mínimo 8 caracteres): '{ie}'"
    
    # Verificar se contém apenas dígitos
    if not re.match(r'^\d+$', ie):
        return False, f"IE deve conter apenas números: '{ie}'"
    
    return True, f"IE: {ie}"


def validar_xml_nfe(caminho_xml: str) -> dict:
    """
    Valida se o XML é uma NF-e válida
    
    Args:
        caminho_xml: Caminho para o arquivo XML
    
    Returns:
        dict: {'valido': bool, 'mensagem': str}
    """
    try:
        tree = etree.parse(caminho_xml)
        root = tree.getroot()
        
        # Verificar se é NF-e
        NS_NFE = 'http://www.portalfiscal.inf.br/nfe'
        nfe = root.find('.//{%s}NFe' % NS_NFE)
        
        if nfe is None:
            return {
                'valido': False,
                'mensagem': 'O arquivo não contém uma estrutura válida de NF-e'
            }
        
        return {
            'valido': True,
            'mensagem': 'XML válido'
        }
        
    except etree.XMLSyntaxError as e:
        return {
            'valido': False,
            'mensagem': f'Erro de sintaxe no XML: {str(e)}'
        }
    except Exception as e:
        return {
            'valido': False,
            'mensagem': f'Erro ao validar XML: {str(e)}'
        }


def validar_dados_gnre(dados: dict) -> Tuple[bool, list]:
    """
    Valida todos os dados necessários para emissão de GNRE
    
    Args:
        dados: Dicionário com dados a validar
    
    Returns:
        tuple: (válido, lista de erros)
    """
    erros = []
    
    # Validar UF destino
    valido, msg = validar_uf(dados.get('uf_destino', ''))
    if not valido:
        erros.append(f"UF Destino: {msg}")
    
    # Validar CNPJ emitente
    valido, msg = validar_cnpj(dados.get('cnpj_emitente', ''))
    if not valido:
        erros.append(f"CNPJ Emitente: {msg}")
    
    # Validar IE emitente
    valido, msg = validar_inscricao_estadual(dados.get('ie_emitente', ''))
    if not valido:
        erros.append(f"IE Emitente: {msg}")
    
    # Validar código de receita
    valido, msg = validar_codigo_receita(dados.get('codigo_receita', ''))
    if not valido:
        erros.append(f"Código Receita: {msg}")
    
    # Validar data de emissão
    valido, msg = validar_data(dados.get('data_emissao', ''))
    if not valido:
        erros.append(f"Data Emissão: {msg}")
    
    # Validar data de vencimento
    valido, msg = validar_data(dados.get('data_vencimento', ''))
    if not valido:
        erros.append(f"Data Vencimento: {msg}")
    
    # Validar valor
    valido, msg = validar_valor(dados.get('valor_icms', ''))
    if not valido:
        erros.append(f"Valor ICMS: {msg}")
    
    # Validar número da NF-e
    if not dados.get('numero_nfe'):
        erros.append("Número da NF-e não informado")
    
    return len(erros) == 0, erros


def formatar_cnpj(cnpj: str) -> str:
    """Formata CNPJ com máscara"""
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj) == 14:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return cnpj


def formatar_cpf(cpf: str) -> str:
    """Formata CPF com máscara"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf


def formatar_valor_monetario(valor) -> str:
    """Formata valor monetário"""
    try:
        valor_float = float(str(valor).replace(',', '.'))
        return f"R$ {valor_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return str(valor)