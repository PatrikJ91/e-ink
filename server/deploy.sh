#!/usr/bin/env bash
# Deploy the server to the Pi and restart it.
#
#   server/deploy.sh [layout]     layout: bands (default) | classic
#
# Copies server/*.py, requirements.txt and the icon font (never the Pi-only
# secrets calendar.url/sensor.mac), restarts the server with EINK_LAYOUT
# set and waits until /health answers.
set -euo pipefail

HOST="eink-raspi"
REMOTE_DIR="~/e-ink/server"
URL="http://192.168.178.40:8080"
HEALTH_TIMEOUT=60  # first render fetches weather + calendar before the port opens

cd "$(dirname "$0")"

layout="${1:-bands}"
if [[ ! -f "layout_${layout}.py" ]]; then
  echo "Unbekanntes Layout '${layout}'. Verfügbar: $(ls layout_*.py | sed 's/layout_\(.*\)\.py/\1/' | tr '\n' ' ')" >&2
  exit 1
fi

echo "==> Pi erreichbar?"
ssh -o BatchMode=yes -o ConnectTimeout=5 "$HOST" true \
  || { echo "Pi nicht erreichbar (ssh $HOST)." >&2; exit 1; }

echo "==> Dateien kopieren"
ssh "$HOST" "mkdir -p $REMOTE_DIR/assets"
scp -q ./*.py requirements.txt "$HOST:$REMOTE_DIR/"
scp -q assets/weather-icons.ttf "$HOST:$REMOTE_DIR/assets/"

echo "==> Server neu starten (Layout: $layout)"
# fuser instead of pkill -f: a pkill pattern could also match this ssh command.
# Exit code 1 just means nothing was running.
# cd as its own step so '&' only backgrounds the fully redirected python
# process; otherwise a background subshell keeps the ssh session open.
ssh "$HOST" "fuser -k 8080/tcp >/dev/null 2>&1 || true; sleep 1; cd $REMOTE_DIR || exit 1; \
  EINK_LAYOUT=$layout setsid python3 server.py < /dev/null > server.log 2>&1 &"

echo -n "==> Warte auf $URL/health "
for _ in $(seq "$HEALTH_TIMEOUT"); do
  if curl -fsS --max-time 2 "$URL/health" >/dev/null 2>&1; then
    echo " ok"
    ssh "$HOST" "tail -n 3 $REMOTE_DIR/server.log"
    echo "Fertig. Das Display holt das neue Bild beim nächsten Zyklus (spätestens 10 Min)."
    exit 0
  fi
  echo -n "."
  sleep 1
done

echo " Timeout" >&2
echo "Server antwortet nicht nach ${HEALTH_TIMEOUT}s, letzte Log-Zeilen:" >&2
ssh "$HOST" "tail -n 20 $REMOTE_DIR/server.log" >&2
exit 1
