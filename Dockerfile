FROM python:3.10-slim

# Instala dependências do sistema incluindo ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /app

# Copia o requirements.txt primeiro (cache do Docker)
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto dos arquivos
COPY . .

# Cria a pasta temp para arquivos temporários
RUN mkdir -p temp

# Porta padrão do Hugging Face Spaces
EXPOSE 7860

# Variável de ambiente para a porta
ENV PORT=7860

# Inicia o servidor
CMD ["python", "app.py"]
