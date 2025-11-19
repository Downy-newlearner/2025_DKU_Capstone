# syntax=docker/dockerfile:1

## Build stage: compile React application
FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies (cached when package manifests do not change)
COPY package.json package-lock.json ./
RUN npm ci

# Copy remaining sources
COPY . .

# Build arguments (can be overridden at build time)
ARG REACT_APP_API_BASE_URL=http://3.35.87.73:8080
ARG REACT_APP_API_TIMEOUT=10000
ARG REACT_APP_PROXY_PATH=/api2
ARG REACT_APP_PROXY_TARGET=http://3.35.87.73:8080

# Expose args to React build
ENV REACT_APP_API_BASE_URL=${REACT_APP_API_BASE_URL}
ENV REACT_APP_API_TIMEOUT=${REACT_APP_API_TIMEOUT}
ENV REACT_APP_PROXY_PATH=${REACT_APP_PROXY_PATH}
ENV REACT_APP_PROXY_TARGET=${REACT_APP_PROXY_TARGET}

RUN npm run build

## Runtime stage: serve with Nginx
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

