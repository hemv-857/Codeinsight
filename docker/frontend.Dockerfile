FROM node:24-alpine

WORKDIR /app

COPY package.json package-lock.json ./
COPY frontend/package.json ./frontend/package.json
RUN npm ci

COPY tsconfig.base.json ./
COPY frontend ./frontend

ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL} \
    NEXT_TELEMETRY_DISABLED=1

RUN npm run build --workspace @codeinsight/frontend

WORKDIR /app/frontend

EXPOSE 3000

CMD ["npm", "run", "start"]
