# Dockerfile multi-architecture
FROM python:3.11-slim

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Création du répertoire de travail
WORKDIR /app

# Copie des fichiers
COPY requirements.txt .
COPY nmea_server.py .
COPY templates/ templates/
COPY cert.pem key.pem ./

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Exposition du port
EXPOSE 5000

# Variables d'environnement
ENV PYTHONPATH=/app
ENV FLASK_ENV=production

# Commande de démarrage
CMD ["python", "nmea_server.py"]
