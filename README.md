# 🥗 FoodLens IA - Nutricionista Digital & Scanner Inteligente

O **FoodLens IA** é um sistema de scanner nutricional inteligente em tempo real que utiliza a webcam do computador e a API do **Google Gemini 2.5 Flash** (Vision) para identificar alimentos, analisar sua segurança para consumo, avaliar sua saudabilidade e estimar sua tabela nutricional.

A interface gráfica é construída em OpenCV combinada com a biblioteca Pillow para renderização nativa de fontes Arial (com suporte completo a acentos do português) e desenhos dinâmicos na tela.

---

## 🚀 Funcionalidades Principais

* **Foco e Mira Guia**: A tela ao vivo da câmera exibe uma mira de foco verde (`Enquadre o alimento aqui`) para facilitar o alinhamento.
* **Detecção 2D (Caixa Verde)**: A IA detecta a localização exata do alimento na imagem e a interface desenha um retângulo verde dinâmico com uma etiqueta com o nome do alimento diretamente sobre o objeto.
* **Tabela Nutricional Estimada (por 100g)**: Apresenta calorias, carboidratos, açúcares, proteínas, gorduras totais, fibras e sódio.
* **Avaliação de Segurança ("Consumo Humano")**: Verifica o frescor do alimento e se há sinais de mofo, podridão ou se é um objeto impróprio para consumo.
* **Grau de Saudabilidade**: Avalia a qualidade nutricional do alimento com notas de 0 a 100 e diferenciação de cores:
  * 🟢 **Saudável** (Verde)
  * 🟡 **Moderado** (Amarelo)
  * 🔴 **Não Saudável** (Vermelho - ex: refrigerantes, ultraprocessados)
* **Salvamento Nativo**: Ao congelar uma análise, você pode pressionar **`[ S ]`** para abrir a janela de salvamento nativa do sistema operacional (via Zenity) e salvar o relatório de imagem em PNG.
* **Tratamento de Erros e Não-Alimentos**: 
  * Se o Gemini estiver indisponível (Erro 503) ou a API Key for inválida, uma tela vermelha detalhada é exibida com dicas de solução.
  * Se você apontar para um objeto não comestível (como fones de ouvido ou rostos), o sistema avisa na tela que nenhum alimento foi detectado.
* **Modo Demonstração (Telas)**: Permite testar o app sem comida física por perto, aceitando fotos de comida mostradas na tela de um celular ou monitor.

---

## 📋 Requisitos do Sistema

### Requisitos Funcionais (RF)

* **RF01 - Captura de Vídeo em Tempo Real**: O sistema deve capturar e exibir continuamente o feed da webcam do usuário em uma janela gráfica.
* **RF02 - Mira de Alinhamento**: O sistema deve sobrepor uma guia de mira verde no centro do feed da câmera ao vivo para ajudar no enquadramento do alimento.
* **RF03 - Captura sob Demanda**: O sistema deve permitir ao usuário congelar e capturar o frame de vídeo atual ao pressionar a tecla `[ ESPAÇO ]`.
* **RF04 - Integração com IA (Gemini)**: O sistema deve enviar o frame capturado para análise da API do Gemini e processar a resposta estruturada em JSON.
* **RF05 - Identificação de Alimentos**: O sistema deve identificar o nome exato e uma descrição curta do estado físico do alimento na imagem.
* **RF06 - Avaliação de Segurança Alimentar**: O sistema deve analisar se o alimento é próprio ou impróprio para o consumo humano, justificando a decisão.
* **RF07 - Classificação de Saudabilidade**: O sistema deve classificar o alimento quanto à saudabilidade (Saudável, Moderado ou Não Saudável) e atribuir uma nota de 0 a 100.
* **RF08 - Estimativa Nutricional**: O sistema deve estimar a tabela nutricional aproximada do alimento por 100g (Calorias, Carboidratos, Açúcares, Proteínas, Gorduras Totais, Fibras e Sódio).
* **RF09 - Rastreamento Visual (Caixa Verde)**: O sistema deve desenhar um retângulo verde em volta do alimento identificado com uma etiqueta contendo o nome correspondente.
* **RF10 - Salvamento de Relatórios**: O sistema deve permitir salvar a tela final do relatório de imagem em PNG ao pressionar a tecla `[ S ]`.
* **RF11 - Exibição em Terminal**: O sistema deve espelhar os dados nutricionais detalhados formatados como tabela em modo texto no terminal.
* **RF12 - Tratamento Visual de Erros**: O sistema deve notificar o usuário com uma tela gráfica vermelha em caso de erros na chamada da API ou caso um objeto não comestível seja enquadrado.
* **RF13 - Modo de Demonstração (Celular)**: O sistema deve permitir configurar a aceitação de fotos de alimentos exibidas em telas de celulares ou monitores.

### Requisitos Não Funcionais (RNF)

* **RNF01 - Multiplataforma**: O código deve rodar sem modificações nos sistemas operacionais Linux, Windows e macOS.
* **RNF02 - Padronização Visual de Fontes**: Todo o texto renderizado na interface gráfica OpenCV/Pillow deve utilizar a fonte Arial (ou equivalentes do SO, como Liberation Sans) com suporte completo a acentos da língua portuguesa.
* **RNF03 - Desempenho e Latência**: A transmissão de vídeo em tempo real deve rodar fluida (taxa de quadros estável), e as ações de teclado devem ter tempo de resposta imediato.
* **RNF04 - Tolerância a Falhas e Resiliência**:
  * O sistema não deve travar nem encerrar a execução abruptamente em caso de erro da API (como erros 503, 429 ou 403), direcionando o usuário para a tela de aviso de falha.
  * O salvamento de arquivos deve tentar carregar o Zenity, ter fallback para o Tkinter (se Zenity for ausente) e, finalmente, auto-salvamento na pasta local para garantir a gravação do arquivo.
* **RNF05 - Segurança de API Keys**: O script não deve conter credenciais expostas no código, lendo a chave `GEMINI_API_KEY` a partir de um arquivo local de variáveis de ambiente `.env`.
* **RNF06 - Estruturação de Dados**: O tráfego de dados com a IA deve ser modelado no formato estrito JSON seguindo um esquema predefinido de campos.

---

## 🛠️ Pré-requisitos

Para rodar este projeto no Linux (Ubuntu/Debian e semelhantes), você precisará de:

1. **Python 3.10+** instalado.
2. Uma **Webcam física** conectada ao computador (o OpenCV tentará abrir o dispositivo `/dev/video0`).
3. O pacote de fontes **Liberation Sans** instalado no sistema (equivalente ao Arial no Linux, instalado por padrão na maioria das distribuições ou via `sudo apt install fonts-liberation`).
4. Utilitário **Zenity** instalado para abrir caixas de salvamento de arquivos nativas:
   ```bash
   sudo apt install zenity
   ```

---

## 📦 Instalação e Configuração

1. Acesse a pasta do projeto:
   ```bash
   cd /home/eduardo/Documentos/Projetos/Gordo
   ```

2. Crie e ative o ambiente virtual do Python:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Instale as dependências necessárias:
   ```bash
   pip install google-genai opencv-python numpy pillow
   ```

4. Crie um arquivo `.env` na raiz do projeto contendo a sua API Key do Gemini:
   ```env
   GEMINI_API_KEY="SUA_CHAVE_AQUI"
   ```
   *(Caso não tenha uma chave, obtenha gratuitamente no [Google AI Studio](https://aistudio.google.com/))*

---

## 🎮 Como Executar e Controlar

Para iniciar a aplicação, execute:
```bash
.venv/bin/python3 ia.py
```

### Controles do Teclado:

| Tecla | Ação |
| :--- | :--- |
| **`[ ESPAÇO ]`** | **Na câmera ao vivo:** Captura a foto e envia para a IA analisar.<br>**Na tela de resultados ou de erro:** Volta para a câmera em tempo real. |
| **`[ S ]`** | **Na tela de resultado:** Salva a imagem com o relatório desenhado (abre o diálogo do sistema). |
| **`[ Q ]`** | **A qualquer momento:** Encerra e fecha a aplicação de forma limpa. |

---

## 📱 Modo Demonstração (Imagens em Celular)

Se você estiver sem alimentos físicos para testar na webcam, é possível ativar o modo demonstração no arquivo `ia.py`:

1. Abra o arquivo `ia.py`.
2. Logo no início, localize a variável global:
   ```python
   MODO_DEMONSTRACAO_CELULAR = True
   ```
3. Defina-a como `True` (padrão) para aceitar fotos de alimentos mostradas em telas de smartphones ou monitores.
4. Quando a IA detectar que você está filmando a tela de um celular, ela aceitará o alimento e exibirá uma etiqueta de aviso laranja **`📱 DEMONSTRAÇÃO: CELULAR`** no canto inferior esquerdo do relatório.
5. Se definir como `False`, a IA rejeitará qualquer celular ou monitor, exibindo um erro de objeto não comestível.

---

## 💡 Monitoramento de Cotas e Limites (Erro 429)

Se você receber a mensagem de erro **`Limite de requisições excedido (Erro 429)`** na tela, significa que sua API Key atingiu os limites temporários da camada gratuita (**Free Tier**):
* **Limitação por Minuto**: Máximo de 15 requisições por minuto (RPM). Aguarde cerca de 30 segundos para o bloqueio expirar automaticamente.
* **Limitação Diária**: Limite diário de requisições (geralmente 20 chamadas/dia em projetos de demonstração não verificados).

### Como verificar quantas chamadas você já utilizou:

1. **Pelo Google AI Studio (Resumido)**:
   * Acesse o **[Google AI Studio](https://aistudio.google.com/)**.
   * Faça login e acesse a aba **"Library"** (Biblioteca) ou o painel de faturamento no menu lateral para visualizar as estatísticas básicas da sua chave.

2. **Pelo Google Cloud Console (Gráfico e Métricas Detalhadas)**:
   * Acesse o **[Google Cloud Console](https://console.cloud.google.com/)**.
   * No topo da página, selecione o projeto correspondente à sua API Key (geralmente nomeado como `Generative Language API` ou `aistudio-xxxx`).
   * Vá no menu lateral em **APIs e Serviços** > **Painel** (APIs & Services > Dashboard).
   * Clique em **Generative Language API** na listagem e mude para a aba **Cotas e limites do sistema** (Quotas & System Limits).
   * Você verá um gráfico mostrando exatamente o número de requisições realizadas no dia e a quantidade restante.
