#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FoodLens IA - Analisador Nutricional Inteligente com Gemini Vision API
==================================================================
Este script inicializa a webcam do computador, exibe o vídeo em tempo real,
e permite capturar uma foto com a tecla ESPAÇO para enviar à IA do Gemini.
A IA analisa se o alimento é seguro para consumo humano, se é saudável,
e estima a tabela nutricional completa usando o modelo gemini-2.5-flash.
"""

import os
import sys
import json
import time
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types

# CONFIGURAÇÕES DE DEMONSTRAÇÃO:
# Se MODO_DEMONSTRACAO_CELULAR for True, a IA aceitará analisar fotos de alimentos
# sendo exibidos em telas de celulares ou outros monitores para facilidade de demonstração.
MODO_DEMONSTRACAO_CELULAR = True

def carregar_env():
    """Carrega variáveis de ambiente de um arquivo .env local se ele existir."""
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#"):
                    continue
                if "=" in linha:
                    chave, valor = linha.split("=", 1)
                    os.environ[chave.strip()] = valor.strip().strip("'\"")

carregar_env()

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("\n" + "="*70)
    print("AVISO: A variável de ambiente GEMINI_API_KEY não foi encontrada.")
    print("Para utilizar o sistema de IA, você precisa obter uma API Key no Google AI Studio:")
    print("👉 https://aistudio.google.com/")
    print("Em seguida, execute no terminal:")
    print("   export GEMINI_API_KEY=\"sua_chave_aqui\"")
    print("="*70 + "\n")
    API_KEY = input("Por favor, digite sua GEMINI_API_KEY para continuar (ou pressione Enter para sair): ").strip()
    if not API_KEY:
        print("Chave não informada. Encerrando programa.")
        sys.exit(1)

try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    print(f"Erro ao inicializar o cliente Gemini: {e}")
    sys.exit(1)

def obter_fonte(tamanho, negrito=False):
    """Carrega uma fonte de forma cross-platform inteligente (Linux, Windows, macOS)."""
    if negrito:
        opcoes = [
            "arialbd.ttf",              # Windows/Mac
            "Arial Bold.ttf",
            "LiberationSans-Bold.ttf",   # Linux
            "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf"
        ]
    else:
        opcoes = [
            "arial.ttf",                # Windows/Mac
            "Arial.ttf",
            "LiberationSans-Regular.ttf", # Linux
            "/usr/share/fonts/liberation-sans-fonts/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/Library/Fonts/Arial.ttf",
            "C:\\Windows\\Fonts\\arial.ttf"
        ]
        
    for opt in opcoes:
        try:
            return ImageFont.truetype(opt, tamanho)
        except Exception:
            continue
            
    try:
        return ImageFont.load_default()
    except Exception:
        return None

PROMPT_ANALISE = """
Analise a imagem deste alimento e retorne uma resposta estruturada em JSON no idioma Português (Brasil).
Você deve identificar o alimento com precisão, avaliar se ele é seguro para consumo humano (verificar se parece mofado, estragado, em decomposição, se é um objeto não comestível, etc.), avaliar a saudabilidade (se é saudável ou não, com uma nota de 0 a 100) e estimar as informações nutricionais por 100g.

SE A IMAGEM NÃO CONTIVER UM ALIMENTO:
Se o objeto principal na foto não for comestível/alimento (ex: celular, teclado, fones de ouvido, rosto de uma pessoa sem alimento, etc.), você deve retornar o JSON com a chave "erro_alimento" preenchida com uma mensagem explicativa em português (ex: "Nenhum alimento detectado na imagem. Por favor, aponte a câmera para um alimento comestível.") e deixar os outros campos nulos ou vazios.

O JSON retornado deve ter EXATAMENTE este formato:
{
  "erro_alimento": "Mensagem se não for um alimento, ou null se for um alimento válido",
  "modo_demonstracao": true/false, // Define como true se o alimento foi identificado através de uma tela de celular/tablet/monitor
  "nome": "Nome do alimento (ex: Maçã Gala, Pizza de Pepperoni)",
  "descricao": "Uma descrição breve do estado físico, frescor e aparência do alimento.",
  "seguro_consumo": {
    "seguro": true/false,
    "status": "Próprio para consumo / Impróprio para consumo / Atenção",
    "justificativa": "Explicação detalhada sobre o motivo da classificação de segurança."
  },
  "saudabilidade": {
    "status": "Saudável / Moderado / Não Saudável",
    "pontuacao": 85,
    "justificativa": "Explicação nutricional sobre a classificação de saudabilidade."
  },
  "caixa_delimitadora": {
    "ymin": 200, // Coordenada vertical superior (inteiro de 0 a 1000)
    "xmin": 400, // Coordenada horizontal esquerda (inteiro de 0 a 1000)
    "ymax": 600, // Coordenada vertical inferior (inteiro de 0 a 1000)
    "xmax": 800  // Coordenada horizontal direita (inteiro de 0 a 1000)
  },
  "nutricao_por_100g": {
    "calorias": 52,
    "carboidratos": 14.0,
    "proteinas": 0.3,
    "gorduras_totais": 0.2,
    "sodio": 1.0,
    "fibras": 2.4,
    "acucares": 10.0
  }
}
No campo "caixa_delimitadora", detecte a localização exata do alimento principal na imagem e forneça suas coordenadas delimitadoras normalizadas (inteiros de 0 a 1000, onde 0 é a extremidade superior/esquerda e 1000 é a extremidade inferior/direita).
Responda apenas com o objeto JSON estruturado. Não inclua blocos de código markdown (como ```json) ou qualquer outro texto explicativo fora do JSON.
"""

def analisar_imagem(pil_img):
    """Envia a imagem capturada para o Gemini e retorna (dados, erro_mensagem)."""
    try:
        prompt = PROMPT_ANALISE
        if MODO_DEMONSTRACAO_CELULAR:
            prompt += "\nATENÇÃO (MODO DEMONSTRAÇÃO ATIVO): Se a imagem contiver um celular, tablet ou tela exibindo a imagem de um alimento, ignore o fato de ser uma tela e analise o alimento exibido normalmente como se estivesse fisicamente presente. Defina o campo 'modo_demonstracao' como true."
        else:
            prompt += "\nATENÇÃO: Se a imagem contiver apenas um celular, tablet ou tela de monitor exibindo um alimento, considere como um objeto não comestível e retorne erro_alimento apropriado."

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[pil_img, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        dados = json.loads(response.text)
        
        if dados.get("erro_alimento"):
            return None, dados["erro_alimento"]
            
        return dados, None
    except json.JSONDecodeError as je:
        print("Erro ao decodificar a resposta JSON do modelo.")
        print(f"Resposta bruta: {response.text}")
        return None, "Erro na resposta da IA: Resposta mal formatada."
    except Exception as e:
        msg = str(e)
        print(f"Erro na comunicação com a API do Gemini: {msg}")
        
        if "503" in msg or "UNAVAILABLE" in msg or "high demand" in msg:
            erro_resumido = "Serviço indisponível ou sob alta demanda (Erro 503). Tente novamente mais tarde."
        elif "403" in msg or "API_KEY" in msg or "invalid" in msg:
            erro_resumido = "Chave de API inválida ou sem permissão (Erro 403)."
        elif "429" in msg or "quota" in msg or "Limit" in msg:
            erro_resumido = "Limite de requisições excedido (Erro 429). Aguarde um minuto."
        else:
            erro_resumido = f"Erro de comunicação: {msg[:80]}"
        return None, erro_resumido

def imprimir_resultado_terminal(dados):
    """Exibe os resultados da análise no terminal com formatação amigável."""
    if not dados:
        return
        
    print("\n" + "="*50)
    print("📊 RELATÓRIO DO FOODLENS IA - NUTRICIONISTA DIGITAL")
    print("="*50)
    print(f"🍎 Alimento: {dados.get('nome', 'Não identificado')}")
    print(f"📝 Descrição: {dados.get('descricao', '')}")
    
    seguro = dados.get('seguro_consumo', {})
    status_seguro = seguro.get('status', 'N/A')
    emoji_seguro = "✅" if seguro.get('seguro') else "❌"
    print(f"\n🛡️ Consumo Humano: {emoji_seguro} {status_seguro}")
    print(f"   Justificativa: {seguro.get('justificativa', '')}")
    
    saude = dados.get('saudabilidade', {})
    status_saude = saude.get('status', 'N/A')
    pontuacao = saude.get('pontuacao', 0)
    emoji_saude = "🟢" if "Saudável" in status_saude else ("🟡" if "Moderado" in status_saude else "🔴")
    print(f"\n🥗 Saudabilidade: {emoji_saude} {status_saude} (Nota: {pontuacao}/100)")
    print(f"   Justificativa: {saude.get('justificativa', '')}")
    
    nutri = dados.get('nutricao_por_100g', {})
    print(f"\n⚡ Tabela Nutricional Estimada (por 100g):")
    print(f"   - Calorias:      {nutri.get('calorias', 0)} kcal")
    print(f"   - Carboidratos:  {nutri.get('carboidratos', 0)} g")
    print(f"   - Açúcares:      {nutri.get('acucares', 0)} g")
    print(f"   - Proteínas:     {nutri.get('proteinas', 0)} g")
    print(f"   - Gorduras Tot:  {nutri.get('gorduras_totais', 0)} g")
    print(f"   - Fibras:        {nutri.get('fibras', 0)} g")
    print(f"   - Sódio:         {nutri.get('sodio', 0)} mg")
    print("="*50 + "\n")

def desenhar_textos_camera(frame):
    """Desenha as instruções iniciais na tela usando a fonte Arial/LiberationSans."""
    h, w, _ = frame.shape
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(img_pil)
    
    font_instrucao = obter_fonte(15, negrito=True)
    font_sair = obter_fonte(15, negrito=True)
    font_pequena = obter_fonte(11)
    
    draw.text((20, h - 35), "Pressione [ ESPAÇO ] para analisar o alimento", font=font_instrucao, fill=(0, 255, 0))
    draw.text((20, 20), "Q - Sair", font=font_sair, fill=(255, 0, 0))
    
    c_x, c_y = w // 2, h // 2
    r = 100  
    cor_mira = (100, 255, 100) 
    
    draw.line([(c_x - r, c_y - r), (c_x - r + 20, c_y - r)], fill=cor_mira, width=2)
    draw.line([(c_x - r, c_y - r), (c_x - r, c_y - r + 20)], fill=cor_mira, width=2)
    
    draw.line([(c_x + r, c_y - r), (c_x + r - 20, c_y - r)], fill=cor_mira, width=2)
    draw.line([(c_x + r, c_y - r), (c_x + r, c_y - r + 20)], fill=cor_mira, width=2)
    
    draw.line([(c_x - r, c_y + r), (c_x - r + 20, c_y + r)], fill=cor_mira, width=2)
    draw.line([(c_x - r, c_y + r), (c_x - r, c_y + r - 20)], fill=cor_mira, width=2)
    
    draw.line([(c_x + r, c_y + r), (c_x + r - 20, c_y + r)], fill=cor_mira, width=2)
    draw.line([(c_x + r, c_y + r), (c_x + r, c_y + r - 20)], fill=cor_mira, width=2)
    
    draw.text((c_x - 60, c_y + r + 10), "Enquadre o alimento aqui", font=font_pequena, fill=(200, 200, 200))
    
    frame_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return frame_bgr

def desenhar_tela_carregamento(frame_congelado):
    """Gera a tela de carregamento com fonte Arial/LiberationSans."""
    h, w, _ = frame_congelado.shape
    loading_frame = frame_congelado.copy()

    cv2.rectangle(loading_frame, (0, 0), (w, h), (0, 0, 0), -1)
    
    img_rgb = cv2.cvtColor(loading_frame, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(img_pil)
    
    font_titulo = obter_fonte(20, negrito=True)
    font_subtitulo = obter_fonte(14)
    
    draw.text((w//2 - 120, h//2 - 20), "ANALISANDO IMAGEM...", font=font_titulo, fill=(255, 255, 0))
    draw.text((w//2 - 140, h//2 + 20), "Por favor, aguarde a resposta da IA...", font=font_subtitulo, fill=(200, 200, 200))
    
    frame_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return frame_bgr

def desenhar_tela_erro(frame, mensagem_erro):
    """Cria uma imagem com o frame congelado e o relatório de erro desenhado usando a fonte Arial/LiberationSans."""
    h, w, _ = frame.shape
    overlay = frame.copy()
    
    cv2.rectangle(overlay, (0, 0), (320, h), (30, 30, 30), -1)
    
    alpha = 0.8
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(img_pil)
    
    font_titulo = obter_fonte(18, negrito=True)
    font_texto = obter_fonte(13)
    font_pequena = obter_fonte(11)
    
    draw.text((15, 20), "FALHA NA ANÁLISE", font=font_titulo, fill=(255, 0, 0))
    
    y_pos = 65
    palavras = mensagem_erro.split()
    linha_atual = ""
    for palavra in palavras:
        test_line = f"{linha_atual} {palavra}".strip()
        if len(test_line) > 30:
            draw.text((15, y_pos), linha_atual, font=font_texto, fill=(230, 230, 230))
            linha_atual = palavra
            y_pos += 22
        else:
            linha_atual = test_line
            
    if linha_atual:
        draw.text((15, y_pos), linha_atual, font=font_texto, fill=(230, 230, 230))
        y_pos += 22
        
    draw.text((15, y_pos + 15), "Dicas:", font=font_titulo, fill=(255, 255, 255))
    draw.text((15, y_pos + 45), "- Verifique sua conexão de rede", font=font_texto, fill=(200, 200, 200))
    draw.text((15, y_pos + 67), "- Confira a chave GEMINI_API_KEY no .env", font=font_texto, fill=(200, 200, 200))
    draw.text((15, y_pos + 89), "- Aguarde alguns instantes e tente denovo", font=font_texto, fill=(200, 200, 200))
    
    draw.text((15, h - 75), "[ ESPAÇO ] para voltar", font=font_pequena, fill=(100, 255, 100))
    draw.text((15, h - 29), "[ Q ] para Sair", font=font_pequena, fill=(100, 100, 255))
    
    frame_final = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return frame_final

def desenhar_overlay_resultado(frame, dados):
    """Cria uma imagem com o frame congelado e as informações de overlay desenhadas usando fontes TrueType (Arial/LiberationSans)."""
    if not dados:
        return frame
        
    h, w, _ = frame.shape
    overlay = frame.copy()
    
    cv2.rectangle(overlay, (0, 0), (320, h), (30, 30, 30), -1)
    
    alpha = 0.8
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(img_pil)
    
    font_titulo = obter_fonte(18, negrito=True)
    font_secao = obter_fonte(13, negrito=True)
    font_texto = obter_fonte(13)
    font_pequena = obter_fonte(11)
    
    nome = dados.get('nome', 'N/A')
    if len(nome) > 23:
        palavras = nome.split()
        linha1, linha2 = "", ""
        for pal in palavras:
            if len(linha1 + " " + pal) <= 23:
                linha1 = f"{linha1} {pal}".strip()
            else:
                linha2 = f"{linha2} {pal}".strip()
        draw.text((15, 12), linha1, font=font_titulo, fill=(255, 255, 255))
        if linha2:
            draw.text((15, 35), linha2, font=font_titulo, fill=(255, 255, 255))
    else:
        draw.text((15, 20), nome, font=font_titulo, fill=(255, 255, 255))
    
    seguro = dados.get('seguro_consumo', {})
    status_seguro = seguro.get('status', 'N/A')
    cor_seguro = (0, 255, 0) if seguro.get('seguro') else (255, 0, 0)
    draw.text((15, 60), f"Consumo: {status_seguro}", font=font_secao, fill=cor_seguro)
    
    saude = dados.get('saudabilidade', {})
    status_saude = saude.get('status', 'N/A')
    pontuacao = saude.get('pontuacao', 0)
    
    if "Não Saudável" in status_saude or "Impróprio" in status_saude or "Inseguro" in status_saude:
        cor_saude = (255, 0, 0)
    elif "Moderado" in status_saude:
        cor_saude = (255, 255, 0)
    else:
        cor_saude = (0, 255, 0)
        
    draw.text((15, 95), f"Saúde: {status_saude} ({pontuacao}/100)", font=font_secao, fill=cor_saude)
    
    nutri = dados.get('nutricao_por_100g', {})
    draw.text((15, 140), "Valores nutricionais aprox:", font=font_secao, fill=(200, 200, 200))
    draw.text((15, 170), f"- Calorias:      {nutri.get('calorias', 0)} kcal", font=font_texto, fill=(255, 255, 255))
    draw.text((15, 192), f"- Carboidratos:  {nutri.get('carboidratos', 0)} g", font=font_texto, fill=(255, 255, 255))
    draw.text((15, 214), f"- Açúcares:      {nutri.get('acucares', 0)} g", font=font_texto, fill=(255, 255, 255))
    draw.text((15, 236), f"- Proteínas:     {nutri.get('proteinas', 0)} g", font=font_texto, fill=(255, 255, 255))
    draw.text((15, 258), f"- Gorduras:      {nutri.get('gorduras_totais', 0)} g", font=font_texto, fill=(255, 255, 255))
    draw.text((15, 280), f"- Fibras:        {nutri.get('fibras', 0)} g", font=font_texto, fill=(255, 255, 255))
    draw.text((15, 302), f"- Sódio:         {nutri.get('sodio', 0)} mg", font=font_texto, fill=(255, 255, 255))
    
    draw.text((15, h - 75), "[ ESPAÇO ] para voltar", font=font_pequena, fill=(100, 255, 100))
    draw.text((15, h - 52), "[ S ] para Salvar Imagem", font=font_pequena, fill=(255, 255, 100))
    draw.text((15, h - 29), "[ Q ] para Sair", font=font_pequena, fill=(100, 100, 255))
    
    if dados.get('modo_demonstracao'):
        draw.rectangle([15, h - 105, 305, h - 85], fill=(255, 140, 0)) 
        draw.text((32, h - 102), "📱 DEMONSTRAÇÃO: CELULAR", font=font_pequena, fill=(255, 255, 255))
    
    caixa = dados.get('caixa_delimitadora', {})
    if caixa and all(k in caixa for k in ('ymin', 'xmin', 'ymax', 'xmax')):
        try:
            
            ymin_px = int(float(caixa['ymin']) * h / 1000)
            xmin_px = int(float(caixa['xmin']) * w / 1000)
            ymax_px = int(float(caixa['ymax']) * h / 1000)
            xmax_px = int(float(caixa['xmax']) * w / 1000)
            
            ymin_px = max(0, min(h - 1, ymin_px))
            xmin_px = max(0, min(w - 1, xmin_px))
            ymax_px = max(0, min(h - 1, ymax_px))
            xmax_px = max(0, min(w - 1, xmax_px))
            
            draw.rectangle([xmin_px, ymin_px, xmax_px, ymax_px], outline=(0, 255, 0), width=3)
            
            nome_etiqueta = dados.get('nome', 'Alimento')
            try:
                bbox = font_pequena.getbbox(nome_etiqueta)
                largura_texto = bbox[2] - bbox[0]
            except Exception:
                largura_texto = len(nome_etiqueta) * 7
            
            largura_etiqueta = largura_texto + 10
            max_largura = w - xmin_px - 5
            if largura_etiqueta > max_largura:
                largura_etiqueta = max_largura
                
            draw.rectangle([xmin_px, max(0, ymin_px - 20), xmin_px + largura_etiqueta, ymin_px], fill=(0, 255, 0))
            draw.text((xmin_px + 5, max(2, ymin_px - 17)), nome_etiqueta, font=font_pequena, fill=(0, 0, 0))
        except Exception as err:
            print(f"Erro ao desenhar caixa delimitadora: {err}")
            
    frame_final = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return frame_final

def main():
    print("Iniciando a webcam... aguarde.")
    
    cv2.namedWindow("FoodLens IA - Scanner Nutricional", cv2.WINDOW_AUTOSIZE)
    try:
        if hasattr(cv2, 'WINDOW_GUI_NORMAL'):
            cv2.destroyWindow("FoodLens IA - Scanner Nutricional")
            cv2.namedWindow("FoodLens IA - Scanner Nutricional", cv2.WINDOW_AUTOSIZE | cv2.WINDOW_GUI_NORMAL)
    except Exception:
        pass
        
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("\nERRO CRÍTICO: Não foi possível acessar a webcam local.")
        print("Dica: Se você estiver executando via WSL, SSH, contêiner Docker ou máquina virtual,")
        print("o acesso direto à webcam física geralmente não é suportado pelo OpenCV.")
        print("\nPara testar a IA sem webcam, coloque uma imagem com o nome 'teste.jpg' no diretório")
        print("e o script tentará analisá-la automaticamente.")
        
        if os.path.exists("teste.jpg"):
            print("Encontrada a imagem 'teste.jpg'. Iniciando análise...")
            try:
                img_pil = Image.open("teste.jpg")
                res, err = analisar_imagem(img_pil)
                if res:
                    imprimir_resultado_terminal(res)
                else:
                    print(f"Falha ao obter análise da imagem 'teste.jpg': {err}")
            except Exception as e:
                print(f"Erro ao ler imagem: {e}")
        else:
            print("Nenhuma imagem 'teste.jpg' encontrada no diretório para fallback.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("\n" + "="*50)
    print("INSTRUÇÕES:")
    print("  🎥 Aponte o alimento para a câmera")
    print("  ⌨️  Pressione [ ESPAÇO ] para escancear / analisar")
    print("  ⌨️  Pressione [ Q ] para fechar o sistema")
    print("="*50 + "\n")

    modo_analise = False
    modo_erro = False
    resultado_dados = None
    erro_analise = None
    frame_congelado = None

    while True:
        if not modo_analise and not modo_erro:
            ret, frame = cap.read()
            if not ret:
                print("Erro: Não foi possível ler o frame da webcam.")
                break
                
            frame = desenhar_textos_camera(frame)
            cv2.imshow("FoodLens IA - Scanner Nutricional", frame)
        elif modo_analise:
            display_frame = frame_congelado.copy()
            display_frame = desenhar_overlay_resultado(display_frame, resultado_dados)
            cv2.imshow("FoodLens IA - Scanner Nutricional", display_frame)
        elif modo_erro:
            display_frame = frame_congelado.copy()
            display_frame = desenhar_tela_erro(display_frame, erro_analise)
            cv2.imshow("FoodLens IA - Scanner Nutricional", display_frame)
        key = cv2.waitKey(30) & 0xFF
        
        if key == ord('q') or key == ord('Q'):
            break
            
        elif key == 32: 
            if modo_analise or modo_erro:
                modo_analise = False
                modo_erro = False
                resultado_dados = None
                erro_analise = None
                frame_congelado = None
            else:
                ret, frame_original = cap.read()
                if ret:
                    print("Capturando imagem e enviando para análise do Gemini...")
                    frame_congelado = frame_original.copy()
                    h, w, _ = frame_congelado.shape
                    
                    loading_frame = desenhar_tela_carregamento(frame_congelado)
                    cv2.imshow("FoodLens IA - Scanner Nutricional", loading_frame)
                    cv2.waitKey(100)
                    
                    img_rgb = cv2.cvtColor(frame_original, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(img_rgb)
                    
                    resultado_dados, erro_analise = analisar_imagem(pil_img)
                    
                    if resultado_dados:
                        imprimir_resultado_terminal(resultado_dados)
                        modo_analise = True
                        modo_erro = False
                    else:
                        print(f"Erro na análise: {erro_analise}")
                        modo_analise = False
                        modo_erro = True

        elif key == ord('s') or key == ord('S'):
            if modo_analise and resultado_dados is not None and frame_congelado is not None:
                img_salvar = frame_congelado.copy()
                img_salvar = desenhar_overlay_resultado(img_salvar, resultado_dados)
                
                nome_sugerido = resultado_dados.get('nome', 'Alimento')
                for char in ['/', '\\', '?', '*', ':', '|', '<', '>', '"']:
                    nome_sugerido = nome_sugerido.replace(char, '')
                nome_sugerido = nome_sugerido.strip().replace(' ', '_')
                nome_sugerido = f"Relatorio_{nome_sugerido}.png"
                
                import subprocess
                caminho_arquivo = None
                try:
                    cmd = [
                        "zenity",
                        "--file-selection",
                        "--save",
                        "--confirm-overwrite",
                        f"--filename={nome_sugerido}",
                        "--file-filter=Imagens PNG (*.png) | *.png",
                        "--title=Salvar Relatório Nutricional"
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        caminho_arquivo = result.stdout.strip()
                except Exception:
                    pass
                
                if not caminho_arquivo:
                    try:
                        import tkinter as tk
                        from tkinter import filedialog
                        root = tk.Tk()
                        root.withdraw()
                        caminho_arquivo = filedialog.asksaveasfilename(
                            initialfile=nome_sugerido,
                            defaultextension=".png",
                            filetypes=[("Imagens PNG", "*.png"), ("Todos os arquivos", "*.*")],
                            title="Salvar Relatório Nutricional"
                        )
                        root.destroy()
                    except Exception:
                        pass
                
                if not caminho_arquivo:
                    caminho_arquivo = nome_sugerido
                    print(f"\n⚠️ Interface de salvamento indisponível. Salvando automaticamente na pasta atual...")
                
                if caminho_arquivo:
                    try:
                        cv2.imwrite(caminho_arquivo, img_salvar)
                        print(f"\n💾 Relatório salvo com sucesso em: {caminho_arquivo}")
                    except Exception as err:
                        print(f"\n❌ Erro ao salvar o arquivo: {err}")
                else:
                    print("\n⚠️ Processo de salvar cancelado ou indisponível.")

    cap.release()
    cv2.destroyAllWindows()
    print("Sistema encerrado.")

if __name__ == "__main__":
    main()
