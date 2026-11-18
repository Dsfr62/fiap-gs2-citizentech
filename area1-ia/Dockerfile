# Imagem do servico de IA do Sereno (Area 1). Contexto de build: a raiz do repositorio,
# porque o treino usa o pipeline da Area 2 (docker-compose.yml faz isso).
FROM python:3.12-slim
WORKDIR /app

# Primeiro so as dependencias: enquanto o requirements nao muda, o Docker reaproveita esta camada.
COPY area1-ia/requirements.txt area1-ia/requirements.txt
RUN pip install --no-cache-dir -r area1-ia/requirements.txt

COPY area2-dados/ area2-dados/
COPY area1-ia/ area1-ia/

# O modelo e treinado aqui, na montagem da imagem: pipeline da Area 2 sem internet + treino com semente fixa.
RUN python area2-dados/pipeline.py --offline && python area1-ia/treinar.py

# Seguranca: o servico nao roda como root dentro do conteiner.
RUN useradd --system --uid 1001 sereno
USER sereno

EXPOSE 8001
ENV PORTA=8001
CMD ["python", "area1-ia/servico.py"]
