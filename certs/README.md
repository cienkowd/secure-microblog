# TLS certificates

Not committed. Generate a self-signed pair for local use:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/key.key -out certs/certificate.crt -subj "/CN=localhost"
```
