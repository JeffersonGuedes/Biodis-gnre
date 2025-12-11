"""
Sistema de Conversão e Emissão de GNRE via XML
Aplicação Streamlit para processar XMLs de NF-e e emitir GNREs automaticamente
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
from datetime import datetime
import os
from typing import List, Dict

from utils.xml_parser import extrair_dados_nfe
from utils.gnre_bot import GNREBot


# Configuração da página
st.set_page_config(
    page_title="Sistema de Emissão GNRE",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)


def inicializar_sessao():
    """Inicializa variáveis de sessão"""
    if 'processados' not in st.session_state:
        st.session_state.processados = []
    if 'em_processamento' not in st.session_state:
        st.session_state.em_processamento = False
    if 'credenciais_salvas' not in st.session_state:
        st.session_state.credenciais_salvas = False


def salvar_xml_temporario(uploaded_file):
    """Salva arquivo XML em pasta temporária"""
    try:
        # Criar diretório temp se não existir
        temp_dir = Path("temp_xmls")
        temp_dir.mkdir(exist_ok=True)
        
        # Salvar arquivo
        file_path = temp_dir / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return file_path
    except Exception as e:
        st.error(f"Erro ao salvar arquivo {uploaded_file.name}: {str(e)}")
        return None


def processar_xml(file_path: Path) -> Dict:
    """
    Processa um arquivo XML e extrai os dados
    
    Returns:
        dict: Dados extraídos ou informações de erro
    """
    try:
        dados = extrair_dados_nfe(str(file_path))
        
        if dados is None:
            return {
                'arquivo': file_path.name,
                'status': 'erro',
                'mensagem': 'Não foi possível extrair dados do XML ou não há DIFAL'
            }
        
        return {
            'arquivo': file_path.name,
            'status': 'ok',
            'dados': dados,
            'mensagem': 'Dados extraídos com sucesso'
        }
    except Exception as e:
        return {
            'arquivo': file_path.name,
            'status': 'erro',
            'mensagem': f'Erro ao processar: {str(e)}'
        }


def exibir_sidebar():
    """Exibe menu lateral com configurações"""
    with st.sidebar:
        st.title("⚙️ Configurações")
        
        st.markdown("### ℹ️ Modo de Operação")
        st.info("""
        **Sem Login Necessário!**
        
        O sistema acessa diretamente o formulário de emissão da GNRE:
        
        `gnre.pe.gov.br:444/gnre/v/guia/index`
        
        Não é necessário fornecer credenciais.
        """)
        
        st.markdown("---")
        st.markdown("### Opções de Execução")
        
        headless = st.checkbox(
            "🕶️ Modo Headless (Navegador Invisível)",
            value=False,
            help="✅ DESMARCADO (Padrão Local): Você verá o navegador trabalhando\n❌ MARCADO: Navegador roda invisível (mais rápido, obrigatório no Streamlit Cloud)"
        )
        
        evidencias = st.checkbox(
            "📸 Salvar Screenshots",
            value=True,
            help="Salva capturas de tela durante o processo para debug"
        )
        
        # Informação sobre ambiente
        import sys
        if sys.platform.startswith('linux'):
            st.info("🐧 **Streamlit Cloud detectado**: Modo headless ativado automaticamente")
        
        st.session_state.opcao_headless = headless
        st.session_state.opcao_evidencias = evidencias
        
        st.markdown("---")
        
        # Informações
        st.markdown("### 📊 Informações")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("XMLs Processados", len(st.session_state.processados))
        with col2:
            sucesso = sum(1 for p in st.session_state.processados if p.get('status') == 'ok')
            st.metric("Sucesso", sucesso)


def exibir_tabela_dados(dados_extraidos: List[Dict]):
    """Exibe tabela com dados extraídos dos XMLs"""
    if not dados_extraidos:
        return
    
    st.markdown("### 📋 Dados Extraídos dos XMLs")
    
    # Preparar dados para tabela
    tabela = []
    for item in dados_extraidos:
        if item['status'] == 'ok':
            dados = item['dados']
            tabela.append({
                'Arquivo': item['arquivo'],
                'NF-e': dados.get('numero_nfe', '-'),
                'UF Destino': dados.get('uf_destino', '-'),
                'CNPJ': dados.get('cnpj_emitente', '-'),
                'Valor ICMS': f"R$ {float(dados.get('valor_icms', 0)):.2f}",
                'Data Emissão': dados.get('data_emissao', '-'),
                'Status': '✅ OK'
            })
        else:
            tabela.append({
                'Arquivo': item['arquivo'],
                'NF-e': '-',
                'UF Destino': '-',
                'CNPJ': '-',
                'Valor ICMS': '-',
                'Data Emissão': '-',
                'Status': f"❌ {item['mensagem']}"
            })
    
    df = pd.DataFrame(tabela)
    st.dataframe(
        df, 
        use_container_width=True,  # Ocupar toda largura disponível
        hide_index=True,
        height=600  # Altura aumentada para desktop
    )
    
    return df


def processar_emissao_gnre(dados_extraidos: List[Dict], usuario: str, senha: str):
    """
    Processa a emissão de GNRE para todos os XMLs válidos
    (usuario e senha não são usados - mantidos por compatibilidade)
    """
    # Filtrar apenas dados válidos
    dados_validos = [item for item in dados_extraidos if item['status'] == 'ok']
    
    if not dados_validos:
        st.warning("⚠️ Nenhum XML válido para processar")
        return
    
    st.markdown("### 🤖 Processando Emissões GNRE")
    
    # Container para logs em tempo real
    log_container = st.expander("📋 Ver Logs Detalhados", expanded=True)
    
    # Configurações
    headless = st.session_state.get('opcao_headless', True)
    evidencias = st.session_state.get('opcao_evidencias', True)
    
    # Inicializar bot
    bot = GNREBot(headless=headless, salvar_evidencias=evidencias)
    
    # Barra de progresso
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    resultados = []
    total = len(dados_validos)
    
    try:
        for idx, item in enumerate(dados_validos):
            dados = item['dados']
            arquivo = item['arquivo']
            
            status_text.text(f"Processando {idx + 1}/{total}: {arquivo}")
            
            # Lista para coletar logs
            logs_processo = []
            
            # Callback para atualizar progresso E mostrar logs
            def callback_progresso(msg, pct):
                progress_bar.progress((idx + pct) / total)
                status_text.text(f"{arquivo}: {msg}")
                logs_processo.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
                # Atualizar logs no container
                with log_container:
                    st.text('\n'.join(logs_processo[-20:]))  # Últimas 20 linhas
            
            # Emitir GNRE
            resultado = bot.emitir_gnre(usuario, senha, dados, callback_progresso)
            
            resultados.append({
                'arquivo': arquivo,
                'nfe': dados['numero_nfe'],
                **resultado
            })
            
            # Atualizar progresso
            progress_bar.progress((idx + 1) / total)
        
        status_text.text("✅ Processamento concluído!")
        
        # Exibir resultados
        exibir_resultados_emissao(resultados)
        
    except Exception as e:
        st.error(f"❌ Erro durante o processamento: {str(e)}")
        with log_container:
            st.error(f"Stacktrace completo: {str(e)}")
    finally:
        bot.fechar()


def exibir_resultados_emissao(resultados: List[Dict]):
    """Exibe os resultados das emissões"""
    st.markdown("### 📊 Resultados da Emissão")
    
    # Preparar dados
    tabela = []
    for r in resultados:
        # Formatar PDF path
        pdf_info = r.get('arquivo_pdf', '-')
        if pdf_info and pdf_info not in ['-', 'None']:
            # Se contém "erro_validacao", mostrar mensagem de erro
            if 'GNRE_erro_validacao' in pdf_info:
                # Extrair mensagem após os dois pontos
                if ':' in pdf_info:
                    pdf_display = '❌ ' + pdf_info.split(':', 1)[1].strip()
                else:
                    pdf_display = '❌ Erro na validação'
            elif 'streamlit_cloud' in pdf_info or 'site_gnre' in pdf_info or 'site' in pdf_info:
                pdf_display = '✅ Gerado no site'
            else:
                # Pegar só o nome do arquivo
                pdf_display = Path(pdf_info).name if pdf_info else '-'
        else:
            pdf_display = '-'
        
        tabela.append({
            'Arquivo': r['arquivo'],
            'NF-e': r['nfe'],
            'Status': '✅ Sucesso' if r['sucesso'] else '❌ Erro',
            'Número GNRE': r.get('numero_gnre', '-'),
            'PDF': pdf_display,
            'Mensagem': r.get('mensagem', 'OK')
        })
    
    df = pd.DataFrame(tabela)
    st.dataframe(
        df, 
        use_container_width=True,  # Ocupar toda largura disponível
        hide_index=True,
        height=600,  # Altura aumentada para desktop
        width=1000
    )

    
    
    # Estatísticas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Processado", len(resultados))
    with col2:
        sucesso = sum(1 for r in resultados if r['sucesso'])
        st.metric("Sucesso", sucesso, delta_color="normal")
    with col3:
        erros = sum(1 for r in resultados if not r['sucesso'])
        st.metric("Erros", erros, delta_color="inverse")
    
    # Botão para baixar screenshots se houver erros
    import sys
    if sys.platform.startswith('linux'):  # Render.com
        st.markdown("---")
        st.markdown("### 📸 Screenshots e Logs (Render.com)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Verificar se existe pasta de screenshots
            screenshots_dir = Path("screenshots")
            if screenshots_dir.exists():
                screenshots = list(screenshots_dir.glob("*.png"))
                if screenshots:
                    st.success(f"✅ {len(screenshots)} screenshot(s) disponível(is)")
                    # Mostrar últimas 3 screenshots
                    screenshots_recentes = sorted(screenshots, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
                    for img in screenshots_recentes:
                        st.image(str(img), caption=img.name, width=300)
                else:
                    st.warning("⚠️ Nenhum screenshot salvo")
            else:
                st.info("ℹ️ Pasta de screenshots não encontrada")
        
        with col2:
            # Verificar logs do sistema
            st.info("""
            **Como ver logs no Render:**
            1. Acesse o Dashboard do Render
            2. Clique no seu serviço
            3. Vá em **Logs** (menu lateral)
            4. Procure por linhas com ❌ ou ⚠️
            """)
    
    # Salvar em session state
    st.session_state.processados.extend(resultados)


def main():
    """Função principal da aplicação"""
    inicializar_sessao()
    
    # Título
    st.title("📄 Sistema de Emissão GNRE")
    st.markdown("**Processe XMLs de NF-e e emita GNREs automaticamente**")
    st.markdown("---")
    
    # Sidebar
    exibir_sidebar()
    
    # Upload de arquivos
    st.markdown("### 📤 Upload de XMLs")
    uploaded_files = st.file_uploader(
        "Selecione um ou mais arquivos XML de NF-e",
        type=['xml'],
        accept_multiple_files=True,
        help="Arraste os arquivos ou clique para selecionar"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)")
        
        # Botão para processar XMLs
        col1, col2 = st.columns([1, 4])
        with col1:
            processar = st.button("🔍 Processar XMLs")
        
        if processar:
            with st.spinner("Processando XMLs..."):
                # Salvar arquivos temporariamente
                arquivos_salvos = []
                for uploaded_file in uploaded_files:
                    file_path = salvar_xml_temporario(uploaded_file)
                    if file_path:
                        arquivos_salvos.append(file_path)
                
                # Processar XMLs
                dados_extraidos = []
                for file_path in arquivos_salvos:
                    resultado = processar_xml(file_path)
                    dados_extraidos.append(resultado)
                
                # Armazenar em session state
                st.session_state.dados_extraidos = dados_extraidos
                
                # Exibir tabela
                exibir_tabela_dados(dados_extraidos)
        
        # Se já processou, mostrar botão de emissão
        if 'dados_extraidos' in st.session_state and st.session_state.dados_extraidos:
            st.markdown("---")
            
            st.info("""
            💡 **Dica**: Desabilite o "Modo Headless" nas configurações para ver o navegador 
            preenchendo os formulários automaticamente!
            """)
            
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("🚀 Emitir GNREs"):
                    processar_emissao_gnre(
                        st.session_state.dados_extraidos,
                        None,  # Não usado
                        None   # Não usado
                    )
            
            with col2:
                if st.button("🔄 Limpar"):
                    st.session_state.dados_extraidos = []
                    st.rerun()
    
    else:
        st.info("👆 Faça upload de um ou mais arquivos XML para começar")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            Sistema de Emissão GNRE - Biodis Industrial LTDA<br>
            Desenvolvido para automação de processos fiscais
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
