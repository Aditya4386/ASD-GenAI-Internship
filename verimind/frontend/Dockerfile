# Frontend Dockerfile — Multi-stage build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (clean install)
RUN npm ci

# Copy source
COPY . .

# Build the production bundle
# VITE_API_URL must be passed at build time via --build-arg or the
# environment, e.g.:  docker build --build-arg VITE_API_URL=https://...
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Production stage — nginx serves the static files
FROM nginx:alpine AS production

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Bug Fix #6 & #8: Expose port 80 (standard HTTP), not 5173
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]