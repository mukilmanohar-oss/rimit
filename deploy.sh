#!/usr/bin/env bash
set -euo pipefail

# deploy.sh
# Usage: ./deploy.sh user@host -i /path/to/key.pem -r /remote/path -s /local/source
# Example: ./deploy.sh ec2-user@13.60.98.14 -i ~/.ssh/RIMITSERVER_KEY.pem -r /home/ec2-user/rimit

REMOTE=""
KEY=""
REMOTE_PATH="/home/${USER:-ubuntu}/app"
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

usage(){
  echo "Usage: $0 user@host -i /path/to/key.pem [-r /remote/path] [-s /local/source]"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--identity) KEY="$2"; shift 2 ;;
    -r|--remote-path) REMOTE_PATH="$2"; shift 2 ;;
    -s|--source) SOURCE_DIR="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) if [ -z "$REMOTE" ]; then REMOTE="$1"; shift; else usage; fi ;;
  esac
done

if [ -z "$REMOTE" ]; then
  echo "Missing target user@host" >&2; usage
fi

if [ -z "$KEY" ]; then
  echo "Missing identity key (-i)." >&2; usage
fi

TMPFILE="/tmp/deploy-$(date +%s).tar.gz"
echo "Creating archive of $SOURCE_DIR -> $TMPFILE (excluding .git and node_modules)"
tar --exclude='.git' --exclude='node_modules' -C "$SOURCE_DIR" -czf "$TMPFILE" .

echo "Copying archive to $REMOTE:$REMOTE_PATH"
scp -i "$KEY" -o StrictHostKeyChecking=no "$TMPFILE" "$REMOTE":/tmp/

echo "Extracting on remote and preparing"
ssh -i "$KEY" -o StrictHostKeyChecking=no "$REMOTE" "mkdir -p $REMOTE_PATH && tar -xzf /tmp/$(basename "$TMPFILE") -C $REMOTE_PATH && rm -f /tmp/$(basename "$TMPFILE") && chmod +x $REMOTE_PATH/setup.sh || true"

echo "Deployment complete. You can SSH and run the setup script:" \
     "ssh -i $KEY $REMOTE 'sudo $REMOTE_PATH/setup.sh'"

rm -f "$TMPFILE"
