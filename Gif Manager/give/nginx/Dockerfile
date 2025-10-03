FROM nginx:alpine

RUN rm -rf /etc/nginx/conf.d/* && \
    rm -rf /etc/nginx/nginx.conf

COPY nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /var/www/html && \
    mkdir -p /var/www/gifs &&\
    mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/www && \
    chmod -R 755 /var/www

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]