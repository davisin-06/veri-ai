# VeriAI — Detector de Conteúdo Gerado por IA

VeriAI é uma aplicação web capaz de analisar vídeos de plataformas como YouTube, TikTok e Instagram e determinar se o conteúdo foi gerado ou manipulado por inteligência artificial.

## Demonstração

O sistema analisa o vídeo em quatro canais independentes:

- **Frames de vídeo** — analisa cada frame com modelo ViT treinado para detecção de deepfake
- **Áudio** — detecta vozes sintéticas geradas por ferramentas de TTS
- **Consistência entre frames** — identifica transições artificialmente suaves típicas de vídeos de IA
- **Metadados técnicos** — analisa padrões de bitrate e FPS suspeitos

## Funcionalidades

- Análise de vídeos por link (YouTube, TikTok, Instagram)
- Análise de arquivos de vídeo locais (MP4, MOV, AVI, MKV)
- Análise de arquivos de áudio (MP3, WAV, OGG, M4A, FLAC)
- Interface web com tema escuro
- Resultado com porcentagem de probabilidade de ser IA
- Scores separados de vídeo e áudio

## Tecnologias

**Back-end:**
- Python 3.x
- Flask
- Hugging Face Transformers
- yt-dlp
- OpenCV
- librosa

**Front-end:**
- HTML5
- CSS3
- JavaScript

**Modelos de IA:**
- `prithivMLmods/Deep-Fake-Detector-v2-Model` — detecção de deepfake em frames
- `MelodyMachine/Deepfake-audio-detection-V2` — detecção de áudio sintético

## Requisitos

- Python 3.10+
- ffmpeg (inclua os arquivos `ffmpeg.exe`, `ffprobe.exe` e `ffplay.exe` na pasta do projeto)

## Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/veri-ai.git
cd veri-ai

# Crie um ambiente virtual
python -m venv .venv

# Ative o ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

## Como usar

1. Baixe o ffmpeg em https://www.gyan.dev/ffmpeg/builds/ e coloque os arquivos `.exe` na pasta do projeto
2. Edite a variável `PASTA_PROJETO` no `app.py` com o caminho da sua pasta
3. Inicie o servidor:

```bash
python app.py
```

4. Acesse no navegador:

```
http://127.0.0.1:5000
```

## Estrutura do projeto

```
veri-ai/
├── app.py          # Servidor Flask com toda a lógica de análise
├── index.html      # Interface web
├── style.css       # Estilo visual
├── script.js       # Lógica do front-end
├── requirements.txt
└── README.md
```

## Limitações

- O sistema foi otimizado para detectar deepfakes de conteúdo com rosto humano
- Vídeos de alta qualidade profissional podem gerar falsos positivos
- Deepfakes muito realistas podem não ser detectados
- O modelo de áudio pode ter resultados inconsistentes em vídeos sem voz humana

## Aviso

VeriAI é uma prova de conceito desenvolvida para fins educacionais. Os resultados não devem ser usados como única fonte de verificação. Sempre verifique os resultados com outras fontes.

## Licença

MIT License — sinta-se livre para usar, modificar e distribuir.

## Autor

Desenvolvido como projeto para concurso escolar.
