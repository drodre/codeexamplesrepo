FROM python:3.9-alpine

WORKDIR /app

RUN mkdir /app/gestion_medicamentos

# Copiar los archivos de requisitos primero para aprovechar el caché de Docker
COPY requirements.txt /app/gestion_medicamentos

# Instalar las dependencias
RUN cd gestion_medicamentos && pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY . /app/gestion_medicamentos

RUN cd /app
# Comando para ejecutar la aplicación
CMD ["uvicorn", "gestion_medicamentos.main_web:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
