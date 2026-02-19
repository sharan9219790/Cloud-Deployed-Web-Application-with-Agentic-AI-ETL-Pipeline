FROM nginx:stable-alpine
# Remove default nginx static files
RUN rm -rf /usr/share/nginx/html/*
# Copy local site files into nginx html folder
COPY . /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
