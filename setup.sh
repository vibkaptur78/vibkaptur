#!/bin/sh
mkdir -p /opt/vibk
cat > /opt/vibk/d.sh <<'SH'
curl -sL https://raw.githubusercontent.com/vibkaptur78/vibkaptur/main/index.html -o /tmp/n.html
head -c 20 /tmp/n.html | grep -qi doctype && cp /tmp/n.html /var/www/vibkaptur/public/index.html
SH
printf '* * * * * root sh /opt/vibk/d.sh\n' > /etc/cron.d/vibk
chmod 644 /etc/cron.d/vibk
(service cron restart || systemctl restart cron) 2>/dev/null
sh /opt/vibk/d.sh
echo "VIBKAPTUR auto-deploy OK"
