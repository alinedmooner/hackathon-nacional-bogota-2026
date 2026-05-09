FROM node:20-alpine

WORKDIR /app


COPY package.json package-lock.json* ./

RUN npm ci

COPY . .

ARG BACKEND_URL=https://gludsitohackathon5back.glud.org
RUN sed -i "s|__BACKEND_URL__|${BACKEND_URL}|g" /app/src/assets/env.js

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

EXPOSE 4200

ENTRYPOINT ["/entrypoint.sh"]
CMD ["npm", "run", "start", "--", "--host", "0.0.0.0", "--port", "4200", "--disable-host-check"]