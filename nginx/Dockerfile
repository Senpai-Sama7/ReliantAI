FROM nginx:alpine

# nginx:alpine base image defaults to USER nginx; switch to root for system operations
USER root

# Install curl for health checks
RUN apk add --no-cache curl

# Copy configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy SSL certificates (in production, mount these as secrets)
COPY ssl/cert.pem /etc/nginx/ssl/cert.pem
COPY ssl/key.pem /etc/nginx/ssl/key.pem

# Create directories
RUN mkdir -p /var/log/nginx /var/cache/nginx /etc/nginx/ssl
RUN chown -R nginx:nginx /var/log/nginx /var/cache/nginx /etc/nginx/ssl /etc/nginx/conf.d

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/nginx-health || exit 1

# Start nginx (master process must run as root to bind port 80)
CMD ["nginx", "-g", "daemon off;"]
