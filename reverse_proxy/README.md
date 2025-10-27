# Worship Flow — Reverse Proxy/Self Hosting

We utilized Cloudflare tunnels and a reverse proxy to securely self host our web application without port forwarding.

1. Install dependencies (Ubuntu):
   - sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
   - curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
   - curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
   - chmod o+r /usr/share/keyrings/caddy-stable-archive-keyring.gpg /etc/apt/sources.list.d/caddy-stable.list
   - sudo apt update && sudo apt install caddy
   - sudo apt install gunicorn

2. Double check files:
   - Make sure you have built the staic react files for production
   - Make sure Django has correct settings for security

3. Setup Cloudflare tunnel:
   - Use Cloudflare website to create a tunnel linked to a domain you own.
   - Utilize Cloudflare provided terminal command to setup launching the terminal on server startup.

4. Start the reverse proxy and backend services:
   - Run the script "start_services.sh"

## Notes
- The production webserver is designed to be run behind a reverse proxy such as Nginx.
- 
