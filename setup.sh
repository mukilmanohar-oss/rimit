#!/usr/bin/env bash
set -euo pipefail

# setup.sh
# Idempotent script to install Docker + Docker Compose and start services
# Usage: sudo ./setup.sh [--path /path/to/repo] [--no-build] [--pull]

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
NO_BUILD=0
PULL=0
NO_MIGRATE=0


while [ "$#" -gt 0 ]; do
  case "$1" in
    --path) REPO_DIR="$2"; shift 2 ;;
    --no-build) NO_BUILD=1; shift ;;
    --pull) PULL=1; shift ;;
    -h|--help) echo "Usage: sudo ./setup.sh [--path /path/to/repo] [--no-build] [--pull]"; exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

command_exists() { command -v "$1" >/dev/null 2>&1; }

install_docker_debian() {
  echo "Installing Docker (Debian/Ubuntu)..."
  curl -fsSL https://get.docker.com | sh
}

install_docker_amazon() {
  echo "Installing Docker on Amazon Linux..."
  # Clean up accidentally added centos repo from previous runs if any
  if [ -f /etc/yum.repos.d/docker-ce.repo ]; then
    rm -f /etc/yum.repos.d/docker-ce.repo
  fi
  if command_exists amazon-linux-extras; then
    amazon-linux-extras install docker -y || true
  fi
  if command_exists dnf; then
    dnf install -y docker || true
  elif command_exists yum; then
    yum install -y docker || true
  fi
}

install_docker_rhel() {
  echo "Installing Docker (RHEL/CentOS)..."
  if command_exists yum-config-manager; then
    yum install -y yum-utils
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
  fi
  if command_exists dnf; then
    dnf install -y docker-ce docker-ce-cli containerd.io
  else
    yum install -y docker-ce docker-ce-cli containerd.io
  fi
}

install_docker_compose_binary() {
  echo "Installing docker-compose binary..." >&2
  COMPOSE_URL="https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)"
  mkdir -p /usr/local/bin
  curl -L "$COMPOSE_URL" -o /usr/local/bin/docker-compose
  chmod +x /usr/local/bin/docker-compose
  
  echo "Installing docker-buildx plugin..." >&2
  mkdir -p /usr/libexec/docker/cli-plugins
  BUILDX_ARCH=$(uname -m)
  if [ "$BUILDX_ARCH" = "x86_64" ]; then BUILDX_ARCH="amd64"; fi
  if [ "$BUILDX_ARCH" = "aarch64" ]; then BUILDX_ARCH="arm64"; fi
  curl -L "https://github.com/docker/buildx/releases/download/v0.17.1/buildx-v0.17.1.linux-${BUILDX_ARCH}" -o /usr/libexec/docker/cli-plugins/docker-buildx
  chmod +x /usr/libexec/docker/cli-plugins/docker-buildx
}

ensure_buildx() {
  if ! docker buildx version 2>/dev/null | grep -qE "0\.1[7-9]\.|0\.[2-9][0-9]\."; then
    echo "Installing docker-buildx plugin to satisfy docker-compose requirements..." >&2
    mkdir -p /usr/libexec/docker/cli-plugins
    BUILDX_ARCH=$(uname -m)
    if [ "$BUILDX_ARCH" = "x86_64" ]; then BUILDX_ARCH="amd64"; fi
    if [ "$BUILDX_ARCH" = "aarch64" ]; then BUILDX_ARCH="arm64"; fi
    curl -L "https://github.com/docker/buildx/releases/download/v0.17.1/buildx-v0.17.1.linux-${BUILDX_ARCH}" -o /usr/libexec/docker/cli-plugins/docker-buildx
    chmod +x /usr/libexec/docker/cli-plugins/docker-buildx
  fi
}

is_amazon_linux() {
  if [ -r /etc/system-release ]; then
    if grep -Eiq 'amazon linux' /etc/system-release; then
      return 0
    fi
  fi
  if [ -r /etc/os-release ]; then
    if grep -Eiq '^ID=(amzn|amazon)$' /etc/os-release || grep -Eiq '^ID_LIKE=.*(amzn|amazon|al202[0-9]).*$' /etc/os-release || grep -Eiq '^NAME=.*Amazon Linux.*$' /etc/os-release; then
      return 0
    fi
  fi
  return 1
}

ensure_docker() {
  if command_exists docker; then
    echo "Docker already installed"
    return
  fi

  if command_exists apt-get; then
    install_docker_debian
  elif is_amazon_linux; then
    install_docker_amazon
  elif command_exists yum || command_exists dnf; then
    install_docker_rhel
  else
    echo "Unsupported package manager. Please install Docker manually." >&2
    exit 1
  fi

  if command_exists systemctl; then
    systemctl enable --now docker || true
  fi
}

choose_compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose"
  elif command_exists docker-compose; then
    echo "docker-compose"
  else
    # try installing docker-compose binary
    install_docker_compose_binary
    echo "docker-compose"
  fi
}

find_compose_file() {
  candidates=("docker-compose.yml" "docker-compose.yaml" "rimit/docker-compose.yml" "rimit/docker-compose.yaml")
  for c in "${candidates[@]}"; do
    if [ -f "$REPO_DIR/$c" ]; then
      echo "$REPO_DIR/$c"
      return 0
    fi
  done
  return 1
}

main() {
  if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo: sudo ./setup.sh" >&2
    exit 1
  fi

  echo "Using repo path: $REPO_DIR"

  ensure_docker
  ensure_buildx

  COMPOSE_CMD=$(choose_compose_cmd)

  COMPOSE_FILE=$(find_compose_file || true)
  if [ -z "$COMPOSE_FILE" ]; then
    echo "No docker-compose file found in repository. Checked: docker-compose.yml, rimit/docker-compose.yml" >&2
    exit 1
  fi

  echo "Using compose file: $COMPOSE_FILE"

  COMPOSE_DIR=$(dirname "$COMPOSE_FILE")
  
  # copy .env if missing and example exists
  if [ ! -f "$COMPOSE_DIR/.env" ]; then
    if [ -f "$COMPOSE_DIR/.env.example" ]; then
      echo "Copying .env.example to .env in $COMPOSE_DIR"
      cp "$COMPOSE_DIR/.env.example" "$COMPOSE_DIR/.env"
    else
      echo "Creating empty .env in $COMPOSE_DIR to satisfy docker-compose"
      touch "$COMPOSE_DIR/.env"
    fi
  fi

  cd "$REPO_DIR"

  # optionally pull images
  if [ "$PULL" -eq 1 ]; then
    echo "Pulling images..."
    $COMPOSE_CMD -f "$COMPOSE_FILE" pull
  fi

  # bring up services
  if [ "$NO_BUILD" -eq 1 ]; then
    echo "Starting services without build"
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d
  else
    echo "Building and starting services"
    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --build
  fi

  echo "Services started. Waiting for Postgres to accept connections..."

  # wait for Postgres using pg_isready inside the db service
  # MAX_WAIT=60
  # waited=0
  # until $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T db pg_isready -U rimit >/dev/null 2>&1; do
  #   sleep 2
  #   waited=$((waited+2))
  #   if [ "$waited" -ge "$MAX_WAIT" ]; then
  #     echo "Postgres did not become ready after $MAX_WAIT seconds" >&2
  #     break
  #   fi
  #   echo "Waiting for Postgres... ($waited/$MAX_WAIT)"
  # done

  if [ "$NO_MIGRATE" -eq 0 ]; then
    echo "Running Django migrations and collectstatic inside a temporary app container"
    $COMPOSE_CMD -f "$COMPOSE_FILE" run -T --rm app python manage.py makemigrations admissions aggregator audit common finance integrations notifications partners rules || true
    $COMPOSE_CMD -f "$COMPOSE_FILE" run -T --rm app python manage.py migrate --noinput || true
    $COMPOSE_CMD -f "$COMPOSE_FILE" run -T --rm app python manage.py collectstatic --noinput || true
  else
    echo "Skipping migrations as requested"
  fi

  echo "Services started. To see logs: $COMPOSE_CMD -f $COMPOSE_FILE logs -f"
}

main "$@"
