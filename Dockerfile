FROM node:22-bookworm-slim
WORKDIR /app
COPY package.json ./
RUN npm install --no-audit --no-fund
COPY public ./public
COPY src ./src
COPY wrangler.docker.jsonc ./wrangler.docker.jsonc
EXPOSE 3000
CMD ["./node_modules/.bin/wrangler","dev","--config","wrangler.docker.jsonc","--local","--ip","0.0.0.0","--port","3000","--persist-to","/data"]
