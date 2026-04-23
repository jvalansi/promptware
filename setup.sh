#!/bin/bash
# Deploy Promptware on a fresh Ubuntu 22.04 VPS.
# Run as root or with sudo.
set -e

DEPLOY_DIR=/opt/promptware
VENV=$DEPLOY_DIR/venv
ROUTELLM_PORT=18080
GATEWAY_PORT=8000

# ── 1. System deps ────────────────────────────────────────────────────────────
apt-get update -y
apt-get install -y python3.11 python3.11-venv nginx certbot python3-certbot-nginx git

# ── 2. Clone / update repo ────────────────────────────────────────────────────
if [ -d "$DEPLOY_DIR/.git" ]; then
  git -C "$DEPLOY_DIR" pull
else
  git clone https://github.com/jvalansi/promptware.git "$DEPLOY_DIR"
fi

# ── 3. Python venv ────────────────────────────────────────────────────────────
python3.11 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install -r "$DEPLOY_DIR/requirements.txt"

# ── 4. RouteLLM systemd service ───────────────────────────────────────────────
cat > /etc/systemd/system/routellm.service << EOF
[Unit]
Description=RouteLLM server
After=network.target

[Service]
WorkingDirectory=$DEPLOY_DIR
EnvironmentFile=$DEPLOY_DIR/.env
ExecStart=$VENV/bin/python -m routellm.openai_server \
  --routers mf \
  --strong-model gpt-4o \
  --weak-model gpt-4o-mini \
  --port $ROUTELLM_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# ── 5. Gateway systemd service ────────────────────────────────────────────────
cat > /etc/systemd/system/promptware-gateway.service << EOF
[Unit]
Description=Promptware auth gateway
After=network.target routellm.service

[Service]
WorkingDirectory=$DEPLOY_DIR
EnvironmentFile=$DEPLOY_DIR/.env
Environment=ROUTELLM_URL=http://localhost:$ROUTELLM_PORT
ExecStart=$VENV/bin/uvicorn gateway.main:app --host 127.0.0.1 --port $GATEWAY_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# ── 6. Daily summary cron ─────────────────────────────────────────────────────
echo "0 8 * * * root $VENV/bin/python $DEPLOY_DIR/scripts/daily_summary.py" \
  > /etc/cron.d/promptware-summary

# ── 7. nginx ──────────────────────────────────────────────────────────────────
cp "$DEPLOY_DIR/nginx.conf" /etc/nginx/sites-available/promptware
ln -sf /etc/nginx/sites-available/promptware /etc/nginx/sites-enabled/promptware
rm -f /etc/nginx/sites-enabled/default
nginx -t

# ── 8. Enable & start ─────────────────────────────────────────────────────────
systemctl daemon-reload
systemctl enable routellm promptware-gateway nginx
systemctl restart routellm promptware-gateway nginx

echo ""
echo "Done. Run certbot to issue SSL:"
echo "  certbot --nginx -d api.promptware.io"
echo ""
echo "Then add your customer keys to $DEPLOY_DIR/customers.json"
echo "and set SLACK_WEBHOOK_URL in $DEPLOY_DIR/.env for daily summaries."
