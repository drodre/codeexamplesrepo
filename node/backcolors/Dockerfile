# Fase 1: Construcción de la aplicación
FROM node:18-alpine AS builder

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar los archivos necesarios para instalar las dependencias
COPY package.json package-lock.json ./

# Instalar las dependencias en modo producción
RUN npm ci --only=production

# Copiar el resto del código fuente
COPY . .

# Fase 2: Imagen final (liviana)
FROM node:18-alpine

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar solo los archivos necesarios desde la fase de construcción
COPY --from=builder /app /app

# Exponer el puerto en el que corre la aplicación (ajusta según tu aplicación)
EXPOSE 5000

# Comando para iniciar la aplicación
CMD ["node", "index.js"]

