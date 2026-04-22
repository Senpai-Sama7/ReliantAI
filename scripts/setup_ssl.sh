#!/bin/bash

# ReliantAI - SSL Certificate Setup Script
# Generates self-signed certificates for local production testing

SSL_DIR="./nginx/ssl"
CERT_FILE="$SSL_DIR/cert.pem"
KEY_FILE="$SSL_DIR/key.pem"

mkdir -p "$SSL_DIR"

if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "SSL certificates already exist in $SSL_DIR."
    exit 0
fi

echo "Generating self-signed SSL certificates..."
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_FILE" -out "$CERT_FILE" \
    -subj "/C=US/ST=Texas/L=Houston/O=ReliantAI/CN=reliantai.io"

if [ $? -eq 0 ]; then
    echo "Successfully generated SSL certificates:"
    echo "  Cert: $CERT_FILE"
    echo "  Key: $KEY_FILE"
    chmod 600 "$KEY_FILE"
else
    echo "Error: Failed to generate SSL certificates!"
    exit 1
fi
