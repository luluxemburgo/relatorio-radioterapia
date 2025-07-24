import streamlit as st
from datetime import date
from textwrap import wrap
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
import os
import re

def gerar_pdf(dados):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- Logotipo ---
    logo_path = "IRMEV.jpg"
    if os.path.exists(logo_path):
        c.drawImage(ImageReader(logo_path), 50, height - 100, width=100, preserveAspectRatio=True)

    # --- Cabeçalho da clínica ---
    c.setFont("Helvetica-Bold", 12)
    c.drawString(160, height - 60, "Dr. Fernando José de Almeida")
    c.setFont("Helvetica", 10)
    c.drawString(160, height - 75, "Rua Bernardino de Campos, 145 - Centro")
    c.drawString(160, height - 90, "Ribeirão Preto (SP) - 14015-130 | Tel: (16) 3236-0105")

    # --- Título ---
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 130, "RELATÓRIO DE ALTA - RADIOTERAPIA")

    # --- Conteúdo ---
    c.setFont("Helvetica", 12)
    y = height - 160
    line_height = 18
    max_width_chars = 100

    def draw_multiline(label, text, y):
        x_start = 50
        max_width = 500
        line_height = 18
        bottom_margin = 50

        label_font = "Helvetica-Bold"
        text_font = "Helvetica"
        font_size = 12

        # Verifica se precisa pular página
        if y < bottom_margin + 3 * line_height:
            c.showPage()
            y = A4[1] - 100

        # Desenha o rótulo
        c.setFont(label_font, font_size)
        label_width = c.stringWidth(f"{label}:", label_font, font_size)
        c.drawString(x_start, y, f"{label}:")
        c.setFont(text_font, font_size)

        # Prepara o texto completo
        full_text = text.strip().replace("\n", " ")
        words = full_text.split(" ")
        current_line = ""
        line_indent = x_start + label_width + 5  # alinhamento da primeira linha após o label
        normal_indent = x_start + 10  # indentação das linhas seguintes

        # Primeira linha usa line_indent, as demais usam normal_indent
        first_line = True
        while words:
            word = words.pop(0)
            test_line = current_line + (" " if current_line else "") + word
            test_width = c.stringWidth(test_line, text_font, font_size)
            indent = line_indent if first_line else normal_indent
            if test_width <= (max_width - (indent - x_start)):
                current_line = test_line
            else:
                c.drawString(indent, y, current_line)
                y -= line_height
                current_line = word
                first_line = False

                # Quebra de página se necessário
                if y < bottom_margin + line_height:
                    c.showPage()
                    y = A4[1] - 100
    
        # Última linha
        if current_line:
            indent = line_indent if first_line else normal_indent
            c.drawString(indent, y, current_line)
            y -= line_height

        return y - 10


    # Ordem personalizada
    y = draw_multiline("Paciente", dados["Paciente"], y)
    y = draw_multiline("Neoplasia", dados["Neoplasia"], y)
    y = draw_multiline("Diagnóstico / Estadiamento", dados["Diagnóstico / Estadiamento"], y)
    y = draw_multiline("Recomendações", dados["Recomendações"], y)
    y = draw_multiline("Volume Alvo", dados["Volume Alvo"], y)
    y = draw_multiline("Dose Total (cGy)", dados["Dose Total"], y)
    y = draw_multiline("Fracionamento", dados["Fracionamento"], y)
    y = draw_multiline("Sistema de Planejamento e Simulação", dados["Sistema de Planejamento e Simulação"], y)
    y = draw_multiline("Dose em órgãos de Risco", dados["Dose em órgãos de Risco"], y)
    y = draw_multiline("Acelerador Linear", dados["Acelerador Linear"], y)
    y = draw_multiline("Feixe de Radiação", dados["Feixe de Radiação"], y)
    y = draw_multiline("Toxicidades Agudas", dados["Toxicidades Agudas"], y)
    y = draw_multiline("Local da radioterapia", dados["Local da radioterapia"], y)
    y = draw_multiline("Tipo de tratamento", dados["Tipo de tratamento"], y)


    # Início e término na mesma linha
    # Início e término com cabeçalho em negrito
    text_obj = c.beginText()
    text_obj.setTextOrigin(50, y)
    text_obj.setFont("Helvetica-Bold", 12)
    text_obj.textOut("Início: ")
    text_obj.setFont("Helvetica", 12)
    text_obj.textOut(f"{dados['Início']}    ")
    text_obj.setFont("Helvetica-Bold", 12)
    text_obj.textOut("Término: ")
    text_obj.setFont("Helvetica", 12)
    text_obj.textLine(dados["Término"])
    c.drawText(text_obj)

    y -= line_height * 2  # pular duas linhas

    # Descritivo final
    y = draw_multiline("Observações", dados["Descricao"], y)

    # Médico responsável
    c.setFont("Helvetica-Bold", 12)
    if y < 70:
        c.showPage()
        y = A4[1] - 100
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Médico Responsável: {dados['Médico Responsável']}")



    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# === Recomendações padrão por tipo de Neoplasia ===
recomendacoes_padrao = {
    "Canal anal": "Tratado com radioterapia combinada à quimioterapia (fluorouracil e mitomicina), sendo cirurgia reservada para casos de recidiva ou persistência tumoral.",
    "Colo de útero": "Tratado com radioterapia pélvica associada à quimioterapia com cisplatina, podendo incluir cirurgia (histerectomia radical) em casos selecionados.",
    "Colo/Retal": "Tratamento inclui ressecção cirúrgica (colectomia ou ressecção anterior do reto), seguido de quimioterapia adjuvante (FOLFOX ou CAPOX) e radioterapia nos casos de tumor de reto localmente avançado.",
    "Endométrio": "Tratado com histerectomia total com salpingo-ooforectomia bilateral, linfadenectomia e, conforme risco, radioterapia e/ou quimioterapia adjuvante.",
    "Estômago": "Tratamento envolve gastrectomia subtotal ou total com linfadenectomia, associado à quimioterapia perioperatória (esquemas como FLOT).", 
    "Linfoma": "Quimioterapia com esquema R-CHOP, podendo incluir radioterapia consolidativa dependendo do estágio e resposta ao tratamento.", 
    "Mama": "Tratado com cirurgia (setorectomia ou mastectomia), quimioterapia (neoadjuvante ou adjuvante), radioterapia e hormonioterapia, conforme perfil molecular.",
    "Pele": "Tratamento cirúrgico (exérese ampla com margens) e, em casos selecionados, radioterapia ou terapias tópicas. Em caso de melanoma, imunoterapia pode ser indicada.",
    "Pulmão": "Tratamento varia de acordo com o estágio, incluindo cirurgia (lobectomia), quimioterapia, radioterapia e terapias-alvo (em casos com mutações EGFR, ALK, etc.) ou imunoterapia.",
    "Próstata": "Tratamento pode incluir prostatectomia radical, radioterapia com ou sem bloqueio hormonal, conforme risco e estágio da doença.",
    "Sistema Nervoso Central": "Ressecção cirúrgica máxima possível, seguida de radioterapia com quimioterapia concomitante com temozolomida, conforme protocolo de Stupp.",
    "Outro": ""
}

Diagnostico_padrao = {
    "Canal anal": "Diagnóstico: Carcinoma epidermóide de canal anal, confirmado por biópsia incisional.\n\nEstadiamento: Estágio clínico determinado por exames de imagem (ressonância magnética de pelve e tomografia abdominal/pélvica) conforme classificação TNM.",
    "Colo de útero": "Diagnóstico: Carcinoma escamoso invasivo do colo uterino, confirmado por biópsia dirigida e exame anatomopatológico.\n\nEstadiamento: Classificação FIGO/TNM baseada em ressonância magnética pélvica e exames clínicos.",
    "Colo/Retal": "Diagnóstico: Adenocarcinoma de cólon ou reto, identificado em colonoscopia com biópsia e confirmação histológica.\n\nEstadiamento: Determinado por tomografia de abdome e pelve, e ressonância magnética retal (para tumores de reto), conforme TNM.",
    "Endométrio": "Diagnóstico: Adenocarcinoma endometrioide do endométrio, confirmado por biópsia endometrial ou curetagem uterina.\n\nEstadiamento: Estágio clínico definido por exame de imagem (ressonância magnética pélvica) e avaliação intraoperatória.",
    "Estômago": "Diagnóstico: Adenocarcinoma gástrico, confirmado por endoscopia digestiva alta com biópsia e histopatologia.\n\nEstadiamento: Realizado por tomografia de tórax e abdome, e ultrassonografia endoscópica quando disponível.", 
    "Linfoma": "Diagnóstico: Linfoma não-Hodgkin de células B (por exemplo, difuso de grandes células B), diagnosticado por biópsia excisional de linfonodo e imuno-histoquímica.\n\nEstadiamento: Estágio definido por PET-CT e exames laboratoriais conforme classificação de Ann Arbor.", 
    "Mama": "Diagnóstico: Carcinoma ductal invasivo de mama, confirmado por biópsia com imuno-histoquímica (receptores hormonais e HER2).\n\nEstadiamento: Definido conforme classificação TNM por exames clínicos e de imagem (mamografia, ultrassonografia e/ou ressonância magnética).",
    "Pele": "Diagnóstico: Carcinoma basocelular (ou espinocelular), diagnosticado por biópsia excisional da lesão cutânea.\n\nEstadiamento: Estágio clínico definido pela profundidade e extensão local da lesão, com TC ou RM em casos avançados.",
    "Pulmão": "Diagnóstico: Adenocarcinoma de pulmão (ou carcinoma de células não pequenas), diagnosticado por biópsia transbrônquica ou punção guiada por TC.\n\nEstadiamento: Estágio clínico definido por tomografia, PET-CT e broncoscopia com mediastinoscopia, conforme classificação TNM.",
    "Próstata": "Diagnóstico: Adenocarcinoma de próstata, diagnosticado por biópsia transretal guiada por ultrassonografia, com PSA elevado e toque retal suspeito.\n\nEstadiamento: Avaliação com ressonância magnética de próstata e cintilografia óssea, conforme classificação TNM.",
    "Sistema Nervoso Central": "Diagnóstico: Glioblastoma multiforme (ou outro glioma), diagnosticado por imagem (ressonância magnética com contraste) e biópsia estereotáxica ou ressecção cirúrgica.\n\nEstadiamento: Não se aplica TNM; avaliação baseada em grau histológico pela OMS.",
    "Outro": ""
}

# === Estado inicial ===
if "tumor_tipo" not in st.session_state:
    st.session_state.tumor_tipo = "Canal anal"
if "recomendacoes" not in st.session_state:
    st.session_state.recomendacoes = recomendacoes_padrao["Canal anal"]
if "diagnostico" not in st.session_state:
    st.session_state.diagnostico = Diagnostico_padrao["Canal anal"]    
if "tumor_customizado" not in st.session_state:
    st.session_state.tumor_customizado = ""

# === Atualiza diagnóstico e recomendação automática ===
def atualizar_recomendacoes_e_diagnostico():
    st.session_state.recomendacoes = recomendacoes_padrao.get(st.session_state.tumor_tipo, "")
    st.session_state.diagnostico = Diagnostico_padrao.get(st.session_state.tumor_tipo, "")
    if st.session_state.tumor_tipo != "Outro":
        st.session_state.tumor_customizado = ""



# === Cabeçalho com logo ===
col1, col2 = st.columns([1, 3])
with col1:
    if os.path.exists("IRMEV.jpg"):
        st.image("IRMEV.jpg", width=120)
with col2:
    st.markdown(
        """
        ### Dr. Fernando José de Almeida  
        Clínica IRMEV  
        Rua Bernardino de Campos, 145 - Centro  
        Ribeirão Preto (SP) - 14015-130  
        📞 (16) 3236-0105
        """,
        unsafe_allow_html=True
    )
st.markdown("---")

# === Estilo para datas e radios em colunas ===
st.markdown("""
    <style>
    div[data-baseweb="radio"] > div {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.5rem;
    }
    .data-formatada {
        font-size: 0.9em;
        color: #444;
        margin-top: 0.4em;
    }
    </style>
""", unsafe_allow_html=True)

# === Título ===
st.title("Relatório de Alta - Radioterapia")

# === Formulário ===
#nome = st.text_input("Nome do paciente")
nome = st.text_input("Nome do paciente", placeholder="Ex: Ana Paula da Silva")


# Neoplasia
Neoplasia = list(recomendacoes_padrao.keys())
st.radio("Neoplasia", options=Neoplasia, key="tumor_tipo", on_change=atualizar_recomendacoes_e_diagnostico)



if st.session_state.tumor_tipo == "Outro":
    st.text_input("Digite o tipo de Neoplasia", key="tumor_customizado")


# Diagnóstico
diagnostico = st.text_area("Diagnóstico / Estadiamento", key="diagnostico", height=200)


# Volume Alvo
volume = st.text_input("Volume Alvo")

# Dose Total
col_dt1, col_dt2 = st.columns([1, 0.3])
with col_dt1:
    dose_total = st.text_input("Dose Total")
with col_dt2:
    st.markdown("<p style='margin-top:2em;'>cGy</p>", unsafe_allow_html=True)



# Fracionamento
col_f1, col_f2, col_d1, col_d2 = st.columns([1, 0.5, 1, 0.5])

with col_f1:
    fracoes = st.text_input("Número de frações")
with col_f2:
    st.markdown("<p style='margin-top:2em;'>frações</p>", unsafe_allow_html=True)

with col_d1:
    dose_por_fracao = st.text_input("Dose por fração")
with col_d2:
    st.markdown("<p style='margin-top:2em;'>cGy</p>", unsafe_allow_html=True)


# Sistema de Planejamento e Simulação
sistema = st.text_input("Sistema de Planejamento e Simulação", value="Varian Eclipse")

# Dose em órgãos de Risco
doseorgao = st.text_input("Dose em órgãos de Risco", value="Todos constrains respeitados")

# Linear Utilizado
linear = st.selectbox("Acelerador Linear Utilizado", ["Unique", "Primus", "Mevatron"])

# Feixe de Radiação
feixe = st.text_input("Feixe de Radiação", value="6MV")


# Toxicidades Agudas Apresentadas
toxicidade = st.text_input("Toxicidades Agudas Apresentadas")

# Datas com formatação visual
col1, col2 = st.columns([1, 1.5])
with col1:
    inicio = st.date_input("Início do Tratamento", key="data_inicio")
with col2:
    st.markdown(f"<div class='data-formatada'>📅 Início: {inicio.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)

col3, col4 = st.columns([1, 1.5])
with col3:
    fim = st.date_input("Fim do Tratamento", value=date.today(), key="data_fim")
with col4:
    st.markdown(f"<div class='data-formatada'>📅 Término: {fim.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)

# Local
local = st.text_input("Local da radioterapia")

# Tipo de tratamento
tipo = st.selectbox("Tipo de tratamento", ["Conformacional", "IMRT/VMAT", "Radiocirurgia", "Radioterapia Estereotáxica"])




# Recomendações automáticas
st.text_area("Recomendações médicas", key="recomendacoes", height=150)

# Botão
if st.button("Gerar PDF"):
    tumor_nome = (
        st.session_state.tumor_customizado
        if st.session_state.tumor_tipo == "Outro"
        else st.session_state.tumor_tipo
    )

    dados = {
        "Paciente": nome,
        "Neoplasia": tumor_nome,
        "Diagnóstico / Estadiamento": diagnostico,
        "Volume Alvo": volume,
        "Dose Total": f"{dose_total} cGy",
        "Fracionamento": f"{fracoes} frações de {dose_por_fracao} cGy",
        "Sistema de Planejamento e Simulação": sistema,
        "Dose em órgãos de Risco": doseorgao,
        "Acelerador Linear": linear,
        "Feixe de Radiação": feixe,
        "Toxicidades Agudas": toxicidade,
        "Local da radioterapia": local,
        "Tipo de tratamento": tipo,
        "Início": inicio.strftime("%d/%m/%Y"),
        "Término": fim.strftime("%d/%m/%Y"),
        "Recomendações": st.session_state.recomendacoes,
        "Descricao": "O Planejamento detalhado (fusões, contornos, curvas de isodose, DVH, DRR, QA) encontra-se em nossos arquivos e a disposição do paciente e colegas médicos.",
        "Médico Responsável": "Dr. Fernando José de Almeida"
    }


    pdf = gerar_pdf(dados)
    nome_arquivo_base = f"relatorio_{nome.replace(' ', '_')}_{fim.strftime('%Y%m%d')}.pdf"
    nome_arquivo = re.sub(r'[^\w\-_.]', '_', nome_arquivo_base)  # remove acentos e símbolos

    st.session_state["pdf"] = pdf
    st.session_state["nome_arquivo"] = nome_arquivo
    st.session_state["pdf_gerado"] = True


# === Mostra o botão de download após gerar ===
if st.session_state.get("pdf_gerado", False):
    st.success("✅ Relatório gerado com sucesso!")
    st.download_button(
        label="📄 Clique aqui para baixar o relatório em PDF",
        data=st.session_state["pdf"],
        file_name=st.session_state["nome_arquivo"],
        mime="application/pdf"
    )





