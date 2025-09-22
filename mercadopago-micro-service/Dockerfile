FROM node:20-alpine

RUN apk add --no-cache git

WORKDIR /app

ENV MP_TOKEN=APP_USR-1245805099959721-092216-8d9bbff3225c00e35623a6456aa5e68d-2530688137

COPY package*.json ./
RUN npm install --omit=optional

COPY . .

EXPOSE 3000

CMD ["node", "index.js"]