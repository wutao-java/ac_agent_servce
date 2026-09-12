# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS builder
WORKDIR /workspace

COPY package*.json ./
RUN npm ci --no-audit --no-fund --loglevel=warn

COPY . ./
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /workspace/dist /usr/share/nginx/html
EXPOSE 80
