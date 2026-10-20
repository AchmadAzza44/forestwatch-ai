# Tahap build: kompilasi React/Vite
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# URL API dipakai browser pengguna, bukan container; sesuaikan bila backend tidak di localhost:8000.
ARG VITE_API_URL=http://localhost:8000/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Tahap layanan: nginx menyajikan berkas statis pada port 80
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
