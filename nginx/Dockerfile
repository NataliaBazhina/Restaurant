FROM nginx:1.25-alpine

RUN mkdir -p /app/staticfiles && \
    mkdir -p /app/media && \
    chmod -R 755 /app

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]