import shutil

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
import yt_dlp, os, subprocess, json, time
from transformers import pipeline
from PIL import Image
import cv2, numpy as np
import librosa, soundfile as sf

# -----------------------------------------------
# CONFIGURAÇÃO DA PASTA DO PROJETO
# Defina a variável de ambiente VERIAI_PATH antes de rodar:
#
# Windows:
#   set VERIAI_PATH=C:\caminho\para\o\projeto
#
# Linux/Mac:
#   export VERIAI_PATH=/caminho/para/o/projeto
#
# Se não definir, usa a pasta onde o app.py está
# -----------------------------------------------
PASTA_PROJETO = os.environ.get("VERIAI_PATH", os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = PASTA_PROJETO
FFMPEG_BIN = shutil.which("ffmpeg") or os.path.join(BASE_DIR, "ffmpeg")
FFPROBE_BIN = shutil.which("ffprobe") or os.path.join(BASE_DIR, "ffprobe")

# Detecta o nome do executável do ffmpeg (Windows usa .exe, Linux/Mac não)
FFPROBE = os.path.join(PASTA_PROJETO, "ffprobe.exe") if os.name == "nt" else "ffprobe"
FFMPEG_LOCATION = PASTA_PROJETO if os.name == "nt" else None

ALLOWED_AUDIO = {"mp3", "wav", "ogg", "m4a", "flac"}

def extensao_permitida(filename, allowed):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed

app = Flask(__name__)
CORS(app)


# -----------------------------------------------
# ROTAS: serve o HTML e arquivos estáticos
# -----------------------------------------------
@app.route("/")
def index():
    return send_from_directory(os.path.join(PASTA_PROJETO, "www"), "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(os.path.join(PASTA_PROJETO, "www"), filename)


# -----------------------------------------------
# Carrega os modelos uma vez só ao iniciar
# -----------------------------------------------
print("Carregando modelos... (pode demorar na primeira vez)")

# Modelo de vídeo — labels: "Realism" e "Deepfake"
video_detector = pipeline(
    "image-classification",
    model="prithivMLmods/Deep-Fake-Detector-v2-Model"
)

# Modelo de áudio — labels: "fake" e "real"
audio_detector = pipeline(
    "audio-classification",
    model="MelodyMachine/Deepfake-audio-detection-V2"
)

print("Modelos prontos!")
print(f"Pasta do projeto: {PASTA_PROJETO}")


# -----------------------------------------------
# FUNÇÃO 1: Baixa o vídeo do link
# -----------------------------------------------
def download_video(url: str) -> str:
    caminho = os.path.join(PASTA_PROJETO, "video_analisado.mp4")

    if os.path.exists(caminho):
        os.remove(caminho)

    cookies_path = os.path.join(PASTA_PROJETO, "cookies.txt")
    opcoes = {
        "outtmpl": caminho.replace(".mp4", ".%(ext)s"),
        "format": "bestvideo[height<=480]+bestaudio/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "ffmpeg_location": os.path.dirname(FFMPEG_BIN) if FFMPEG_BIN else BASE_DIR,
        "socket_timeout": 30,
        "cookiefile": cookies_path if os.path.exists(cookies_path) else None,
    }

    if FFMPEG_LOCATION:
        opcoes["ffmpeg_location"] = FFMPEG_LOCATION

    with yt_dlp.YoutubeDL(opcoes) as ydl:
        ydl.download([url])

    return caminho


# -----------------------------------------------
# FUNÇÃO 2: Extrai frames do vídeo (2 por segundo)
# -----------------------------------------------
def extrair_frames(caminho: str, fps_alvo=2) -> list:
    cap = cv2.VideoCapture(caminho)

    if not cap.isOpened():
        return []

    fps_real = cap.get(cv2.CAP_PROP_FPS) or 24
    intervalo = max(1, int(fps_real / fps_alvo))

    frames = []
    count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if count % intervalo == 0 and count > fps_real * 2:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)
        count += 1

    cap.release()
    return frames[:30]


# -----------------------------------------------
# FUNÇÃO 3: Extrai o áudio do vídeo
# -----------------------------------------------
def extrair_audio(caminho_video: str) -> str:
    caminho_audio = os.path.join(PASTA_PROJETO, "audio_analisado.wav")

    if os.path.exists(caminho_audio):
        os.remove(caminho_audio)

    try:
        audio, sr = librosa.load(caminho_video, sr=16000, mono=True)
        audio = audio[:sr * 30]
        sf.write(caminho_audio, audio, sr)
        return caminho_audio
    except Exception as e:
        print(f"Erro ao extrair áudio: {e}")
        return None


# -----------------------------------------------
# FUNÇÃO 4: Converte áudio para WAV 16kHz
# -----------------------------------------------
def converter_audio(caminho_entrada: str) -> str:
    caminho_saida = os.path.join(PASTA_PROJETO, "audio_convertido.wav")

    if os.path.exists(caminho_saida):
        os.remove(caminho_saida)

    try:
        audio, sr = librosa.load(caminho_entrada, sr=16000, mono=True)
        audio = audio[:sr * 30]
        sf.write(caminho_saida, audio, sr)
        return caminho_saida
    except Exception as e:
        print(f"Erro ao converter áudio: {e}")
        return None


# -----------------------------------------------
# FUNÇÃO 5: Analisa um frame individual
# -----------------------------------------------
def analisar_frame_individual(frame):
    try:
        img = Image.fromarray(frame).resize((224, 224))
        resultado = video_detector(img)[0]
        label = resultado["label"].lower()
        score = resultado["score"]
        return score if "deepfake" in label else (1 - score)
    except Exception as e:
        print(f"Erro no frame: {e}")
        return None


# -----------------------------------------------
# FUNÇÃO 6: Analisa todos os frames em paralelo
# -----------------------------------------------
def analisar_frames(frames: list) -> float:
    if not frames:
        return 0.5

    with ThreadPoolExecutor(max_workers=4) as executor:
        resultados = list(executor.map(analisar_frame_individual, frames))

    scores = [r for r in resultados if r is not None]
    return float(np.mean(scores)) if scores else 0.5


# -----------------------------------------------
# FUNÇÃO 7: Analisa o áudio com IA
# -----------------------------------------------
def analisar_audio(caminho_audio: str) -> float:
    if not caminho_audio or not os.path.exists(caminho_audio):
        return 0.5

    try:
        resultado = audio_detector(caminho_audio)[0]
        label = resultado["label"].lower()
        score = resultado["score"]
        prob_ia = score if "fake" in label else (1 - score)
        return float(prob_ia)
    except Exception as e:
        print(f"Erro na análise de áudio: {e}")
        return 0.5


# -----------------------------------------------
# FUNÇÃO 8: Analisa consistência entre frames
# -----------------------------------------------
def analisar_consistencia(frames: list) -> float:
    if len(frames) < 2:
        return 0.5

    diferencas = []
    for i in range(1, len(frames)):
        diff = np.mean(np.abs(
            frames[i].astype(float) - frames[i-1].astype(float)
        ))
        diferencas.append(diff)

    variacao = np.std(diferencas)

    if variacao < 2.0:
        return 0.80
    elif variacao < 5.0:
        return 0.65
    elif variacao > 15.0:
        return 0.25
    else:
        return 0.50


# -----------------------------------------------
# FUNÇÃO 9: Analisa metadados técnicos
# -----------------------------------------------
def analisar_metadados(caminho_video: str) -> float:
    try:
        cmd = [
            FFPROBE,
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            caminho_video
        ]
        resultado = subprocess.run(cmd, capture_output=True, text=True)
        dados = json.loads(resultado.stdout)

        stream = dados["streams"][0]
        bitrate = int(stream.get("bit_rate", 0))
        fps_str = stream.get("r_frame_rate", "30/1").split("/")
        fps = int(fps_str[0]) / max(int(fps_str[1]), 1)

        score_suspeito = 0.5

        if bitrate > 0:
            if bitrate < 500000 or bitrate > 8000000:
                score_suspeito += 0.1

        if fps in [24.0, 30.0, 60.0]:
            score_suspeito += 0.1

        return min(score_suspeito, 1.0)
    except Exception as e:
        print(f"Erro nos metadados: {e}")
        return 0.5


# -----------------------------------------------
# FUNÇÃO 10: Detecta a qualidade do vídeo
# Vídeos de alta qualidade recebem limiar mais alto
# para evitar falsos positivos (sugestão do Gemini)
# -----------------------------------------------
def detectar_qualidade_video(caminho_video: str) -> str:
    try:
        cmd = [
            FFPROBE,
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            caminho_video
        ]
        resultado = subprocess.run(cmd, capture_output=True, text=True)
        dados = json.loads(resultado.stdout)

        stream = dados["streams"][0]
        altura  = int(stream.get("height", 0))
        bitrate = int(stream.get("bit_rate", 0))

        # Considera alta qualidade se:
        # - resolução 480p+ com bitrate alto (vídeo profissional comprimido)
        # - OU resolução 720p+ independente do bitrate
        if altura >= 720 or (altura >= 480 and bitrate > 1500000):
            return "alta"
        else:
            return "normal"
    except Exception as e:
        print(f"Erro ao detectar qualidade: {e}")
        return "normal"

# -----------------------------------------------
# FUNÇÃO 11: Calcula score final ponderado
# -----------------------------------------------
def calcular_score(score_video, score_audio, score_consistencia, score_metadados, tem_audio):
    if tem_audio:
        return (
            score_video        * 0.60 +
            score_audio        * 0.05 +
            score_consistencia * 0.25 +
            score_metadados    * 0.10
        )
    else:
        return (
            score_video        * 0.65 +
            score_consistencia * 0.25 +
            score_metadados    * 0.10
        )


# -----------------------------------------------
# ENDPOINT 1: analisa vídeo por link
# -----------------------------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    dados = request.get_json()

    if not dados or "url" not in dados:
        return jsonify({"erro": "Envie um JSON com o campo 'url'"}), 400

    url = dados["url"].strip()
    if not url:
        return jsonify({"erro": "URL não pode ser vazia"}), 400

    caminho_video = None
    caminho_audio = None

    try:
        caminho_video = download_video(url)
        frames        = extrair_frames(caminho_video)
        caminho_audio = extrair_audio(caminho_video)

        score_video        = analisar_frames(frames)
        score_audio        = analisar_audio(caminho_audio)
        score_consistencia = analisar_consistencia(frames)
        score_metadados    = analisar_metadados(caminho_video)
        qualidade          = detectar_qualidade_video(caminho_video)

        score_final    = calcular_score(score_video, score_audio, score_consistencia, score_metadados, caminho_audio is not None)
        porcentagem_ia = round(score_final * 100, 1)

        # Limiar dinâmico — vídeos de alta qualidade recebem limiar mais alto
        # para compensar o viés do modelo contra vídeos profissionais reais
        limiar = 72 if qualidade == "alta" else 65

        return jsonify({
            "probabilidade_ia":  porcentagem_ia,
            "e_ia":              porcentagem_ia > limiar,
            "confianca":         "alta" if abs(porcentagem_ia - 50) > 25 else "baixa",
            "frames_analisados": len(frames),
            "score_video":       round(score_video * 100, 1),
            "score_audio":       round(score_audio * 100, 1),
            "modo":              "video",
            "qualidade":         qualidade,
        })

    except Exception as e:
        return jsonify({"erro": f"Falha na análise: {str(e)}"}), 500

    finally:
        time.sleep(1)
        for arq in [caminho_video, caminho_audio]:
            if arq and os.path.exists(arq):
                try:
                    os.remove(arq)
                except Exception:
                    pass


# -----------------------------------------------
# ENDPOINT 2: analisa vídeo por arquivo MP4
# -----------------------------------------------
@app.route("/analyze-file", methods=["POST"])
def analyze_file():
    if "file" not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400

    arquivo = request.files["file"]
    if arquivo.filename == "":
        return jsonify({"erro": "Arquivo inválido"}), 400

    nome    = secure_filename(arquivo.filename)
    caminho = os.path.join(PASTA_PROJETO, nome)
    arquivo.save(caminho)

    caminho_audio = None

    try:
        frames        = extrair_frames(caminho)
        caminho_audio = extrair_audio(caminho)

        score_video        = analisar_frames(frames)
        score_audio        = analisar_audio(caminho_audio)
        score_consistencia = analisar_consistencia(frames)
        score_metadados    = analisar_metadados(caminho)
        qualidade          = detectar_qualidade_video(caminho)

        score_final    = calcular_score(score_video, score_audio, score_consistencia, score_metadados, caminho_audio is not None)
        porcentagem_ia = round(score_final * 100, 1)

        limiar = 72 if qualidade == "alta" else 65

        return jsonify({
            "probabilidade_ia":  porcentagem_ia,
            "e_ia":              porcentagem_ia > limiar,
            "confianca":         "alta" if abs(porcentagem_ia - 50) > 25 else "baixa",
            "frames_analisados": len(frames),
            "score_video":       round(score_video * 100, 1),
            "score_audio":       round(score_audio * 100, 1),
            "modo":              "video",
            "qualidade":         qualidade,
        })

    except Exception as e:
        return jsonify({"erro": f"Falha na análise: {str(e)}"}), 500

    finally:
        time.sleep(1)
        for arq in [caminho, caminho_audio]:
            if arq and os.path.exists(arq):
                try:
                    os.remove(arq)
                except Exception:
                    pass


# -----------------------------------------------
# ENDPOINT 3: analisa áudio direto
# -----------------------------------------------
@app.route("/analyze-audio", methods=["POST"])
def analyze_audio():
    if "file" not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400

    arquivo = request.files["file"]
    nome    = secure_filename(arquivo.filename)

    if not extensao_permitida(nome, ALLOWED_AUDIO):
        return jsonify({"erro": "Formato não suportado. Use MP3, WAV, OGG, M4A ou FLAC"}), 400

    caminho            = os.path.join(PASTA_PROJETO, nome)
    caminho_convertido = None

    arquivo.save(caminho)

    try:
        caminho_convertido = converter_audio(caminho)

        if not caminho_convertido:
            return jsonify({"erro": "Não foi possível processar o arquivo de áudio"}), 500

        score_audio    = analisar_audio(caminho_convertido)
        porcentagem_ia = round(score_audio * 100, 1)

        return jsonify({
            "probabilidade_ia":  porcentagem_ia,
            "e_ia":              porcentagem_ia > 65,
            "confianca":         "alta" if abs(porcentagem_ia - 50) > 25 else "baixa",
            "frames_analisados": 0,
            "score_video":       "N/A",
            "score_audio":       porcentagem_ia,
            "modo":              "audio",
        })

    except Exception as e:
        return jsonify({"erro": f"Falha na análise: {str(e)}"}), 500

    finally:
        for arq in [caminho, caminho_convertido]:
            if arq and os.path.exists(arq):
                try:
                    os.remove(arq)
                except Exception:
                    pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", debug=True, port=port)
