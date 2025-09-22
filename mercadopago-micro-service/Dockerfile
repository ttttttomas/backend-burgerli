FROM node:20-alpine

RUN apk add --no-cache git

WORKDIR /app

ENV MP_TOKEN=APP_USR-1213563575706940-041714-f44c15cc6c7cf0a8a755150305750475-2393129299

COPY package*.json ./
RUN npm install --omit=optional

COPY . .

EXPOSE 3000

CMD ["node", "index.js"]