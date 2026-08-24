FROM node:20-alpine AS build
WORKDIR /build
COPY package.json ./
RUN npm install
COPY . .
ARG VITE_GATEWAY_API_URL
ARG VITE_DECKING_ENGINE_API_URL
ENV VITE_GATEWAY_API_URL=$VITE_GATEWAY_API_URL
ENV VITE_DECKING_ENGINE_API_URL=$VITE_DECKING_ENGINE_API_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /build/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
