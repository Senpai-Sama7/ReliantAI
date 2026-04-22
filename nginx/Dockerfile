FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Copy configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy SSL certificates (in production, mount these as secrets)
COPY ssl/cert.pem /etc/nginx/ssl/cert.pem
COPY ssl/key.pem /etc/nginx/ssl/key.pem

# Copy dashboard files
COPY dashboard/ /usr/share/nginx/html/dashboard/

# Create directories
RUN mkdir -p /var/log/nginx /var/cache/nginx /etc/nginx/ssl

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/nginx-health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
