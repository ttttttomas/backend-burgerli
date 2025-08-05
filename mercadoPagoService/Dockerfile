FROM node:20-alpine

RUN apk add --no-cache git

WORKDIR /app

COPY package*.json ./
RUN npm install --omit=optional

COPY . .

EXPOSE 3000

CMD ["node", "payment.controller.js"]