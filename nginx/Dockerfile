# nginx/Dockerfile
# Use the official Nginx image from Docker Hub
FROM nginx:1.25-alpine

# Remove the default Nginx configuration file
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom Nginx configuration file from the nginx directory to the container
COPY nginx.conf /etc/nginx/conf.d/
