FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache bash

COPY package.json package-lock.json* ./

RUN npm ci

COPY . .

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

EXPOSE 4200

ENTRYPOINT ["/entrypoint.sh"]
CMD ["npm", "run", "start", "--", "--host", "0.0.0.0", "--port", "4200", "--proxy-config", "proxy.conf.json"]