FROM kong:3.5

# Copy declarative configuration
COPY kong.yml /usr/local/kong/declarative/kong.yml

# Set environment for declarative config
ENV KONG_DATABASE=off
ENV KONG_DECLARATIVE_CONFIG=/usr/local/kong/declarative/kong.yml
ENV KONG_PROXY_ACCESS_LOG=/dev/stdout
ENV KONG_ADMIN_ACCESS_LOG=/dev/stdout
ENV KONG_PROXY_ERROR_LOG=/dev/stderr
ENV KONG_ADMIN_ERROR_LOG=/dev/stderr

# Expose ports
EXPOSE 8000 8443 8001 8444

# Health check
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD kong health

CMD ["kong", "docker-start"]
