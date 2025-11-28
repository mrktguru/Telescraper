# Deployment Guide - Telegram Parser Web App

## Prerequisites

1. Ubuntu/Debian server with root access
2. Python 3.10+
3. Domain `tgparser.mrktgu.ru` pointing to server IP
4. Telegram API credentials in `.env` file

## Step 1: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and required packages
sudo apt install python3 python3-pip python3-venv nginx certbot python3-certbot-nginx -y

# Install web dependencies
cd /home/user/Telescraper
pip3 install -r requirements_web.txt
```

## Step 2: Configure Environment

```bash
# Ensure .env file exists and is configured
cat .env

# Should contain:
# TELEGRAM_API_ID=your_api_id
# TELEGRAM_API_HASH=your_api_hash
# TELEGRAM_PHONE=+your_phone
# SECRET_KEY=generate_random_secret_key_here
```

Generate secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Add to .env:
```bash
echo "SECRET_KEY=generated_key_here" >> .env
```

## Step 3: Initialize Database

```bash
# Create data directory
mkdir -p data/output

# Test web app (creates database)
python3 web_app.py
# Press Ctrl+C after it starts

# Check database was created
ls -la data/app.db
```

## Step 4: Setup Systemd Service

```bash
# Copy service file
sudo cp deployment/tgparser.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable tgparser

# Start service
sudo systemctl start tgparser

# Check status
sudo systemctl status tgparser

# View logs
sudo journalctl -u tgparser -f
```

## Step 5: Configure Nginx

```bash
# Copy nginx config
sudo cp deployment/nginx.conf /etc/nginx/sites-available/tgparser.conf

# Create symlink
sudo ln -s /etc/nginx/sites-available/tgparser.conf /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check nginx status
sudo systemctl status nginx
```

## Step 6: Setup DNS

Configure your DNS provider to point `tgparser.mrktgu.ru` to your server IP:

```
A Record: tgparser.mrktgu.ru -> YOUR_SERVER_IP
```

Wait for DNS propagation (can take up to 24 hours, usually 5-10 minutes).

Test DNS:
```bash
nslookup tgparser.mrktgu.ru
# Should return your server IP
```

## Step 7: Setup SSL (HTTPS)

After DNS is configured:

```bash
# Obtain SSL certificate
sudo certbot --nginx -d tgparser.mrktgu.ru

# Follow prompts:
# - Enter email
# - Agree to terms
# - Choose redirect HTTP to HTTPS (option 2)

# Test auto-renewal
sudo certbot renew --dry-run

# Check certificate
sudo certbot certificates
```

Certbot will automatically update nginx config with SSL.

## Step 8: Create Admin User

```bash
# Open Python shell
python3

# Run:
from database import Database
db = Database('data/app.db')
db.create_user('your-email@example.com', 'your-password')
exit()
```

## Step 9: Test Application

Open browser and visit:
- HTTP: `http://tgparser.mrktgu.ru`
- HTTPS (after SSL): `https://tgparser.mrktgu.ru`

Login with created credentials and test parsing.

## Useful Commands

### Service Management
```bash
# Restart service
sudo systemctl restart tgparser

# Stop service
sudo systemctl stop tgparser

# View logs
sudo journalctl -u tgparser -f

# View last 100 lines
sudo journalctl -u tgparser -n 100
```

### Nginx Management
```bash
# Test config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Restart nginx
sudo systemctl restart nginx

# View error log
sudo tail -f /var/log/nginx/tgparser_error.log

# View access log
sudo tail -f /var/log/nginx/tgparser_access.log
```

### Update Application
```bash
# Pull latest code
cd /home/user/Telescraper
git pull

# Update dependencies
pip3 install -r requirements_web.txt

# Restart service
sudo systemctl restart tgparser
```

### Backup
```bash
# Backup database
cp data/app.db data/app.db.backup.$(date +%Y%m%d)

# Backup results
tar -czf output_backup_$(date +%Y%m%d).tar.gz data/output/
```

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u tgparser -n 50

# Check permissions
ls -la /home/user/Telescraper

# Test manually
cd /home/user/Telescraper
python3 web_app.py
```

### Nginx 502 Bad Gateway
```bash
# Check if service is running
sudo systemctl status tgparser

# Check if port 8000 is listening
sudo netstat -tlnp | grep 8000

# Check nginx error log
sudo tail -f /var/log/nginx/tgparser_error.log
```

### SSL Certificate Issues
```bash
# Renew certificate manually
sudo certbot renew

# Check certificate expiry
sudo certbot certificates

# Remove and reinstall
sudo certbot delete --cert-name tgparser.mrktgu.ru
sudo certbot --nginx -d tgparser.mrktgu.ru
```

### Database Issues
```bash
# Check database exists
ls -la data/app.db

# Reinitialize (WARNING: deletes all data)
rm data/app.db
python3 web_app.py
# Press Ctrl+C after it starts
```

## Security Recommendations

1. **Change SECRET_KEY**: Generate strong random secret key
2. **Firewall**: Configure UFW to only allow ports 22, 80, 443
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
3. **Fail2ban**: Install to prevent brute force attacks
   ```bash
   sudo apt install fail2ban -y
   ```
4. **Regular Updates**: Keep system and packages updated
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
5. **Backups**: Schedule regular database backups

## Support

For issues, check:
- Service logs: `sudo journalctl -u tgparser -f`
- Nginx logs: `sudo tail -f /var/log/nginx/tgparser_error.log`
- Application manually: `python3 web_app.py`

---

**Deployment completed!** 🎉

Access your app at: `https://tgparser.mrktgu.ru`
