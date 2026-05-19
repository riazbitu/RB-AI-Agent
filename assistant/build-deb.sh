#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="1.0.0"
PACKAGE_NAME="rb-assistant"
ARCH="amd64"
OUTPUT_FILE="../${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

rm -rf package
mkdir -p package/DEBIAN package/opt/rb-assistant package/usr/lib/systemd/system package/usr/local/bin

# core files
install -m 755 server.py package/opt/rb-assistant/server.py
install -m 755 indexer.py package/opt/rb-assistant/indexer.py
install -m 755 cli.py package/opt/rb-assistant/cli.py
install -m 755 embeddings.py package/opt/rb-assistant/embeddings.py
install -m 644 __init__.py package/opt/rb-assistant/__init__.py
install -m 644 README.md package/opt/rb-assistant/README.md
install -m 644 requirements.txt package/opt/rb-assistant/requirements.txt
install -m 755 setup_env.sh package/opt/rb-assistant/setup_env.sh

# copy UI
mkdir -p package/opt/rb-assistant/ui
install -m 644 ui/index.html package/opt/rb-assistant/ui/index.html

# copy docs
mkdir -p package/opt/rb-assistant/docs
cp -r ../docs/* package/opt/rb-assistant/docs/ || true

# include modules and tests
mkdir -p package/opt/rb-assistant/modules
cp -r modules package/opt/rb-assistant/ || true
mkdir -p package/opt/rb-assistant/tests
cp -r tests package/opt/rb-assistant/ || true

install -m 644 assistant.service package/usr/lib/systemd/system/assistant.service

# postinst: create system user, set permissions, create venv and install optional deps, reload systemd and enable service
cat > package/DEBIAN/postinst <<'EOF'
#!/usr/bin/env bash
set -e
if ! id -u rbassistant >/dev/null 2>&1; then
	useradd --system --no-create-home --shell /usr/sbin/nologin rbassistant || true
fi
mkdir -p /opt/rb-assistant
chown -R rbassistant:rbassistant /opt/rb-assistant || true
# create venv and install optional dependencies (may require network)
if command -v python3 >/dev/null 2>&1; then
  python3 -m venv /opt/rb-assistant/venv || true
  /opt/rb-assistant/venv/bin/pip install --upgrade pip || true
  if [ -f /opt/rb-assistant/requirements.txt ]; then
    /opt/rb-assistant/venv/bin/pip install -r /opt/rb-assistant/requirements.txt || true
  fi
fi
systemctl daemon-reload || true
systemctl enable assistant.service || true
exit 0
EOF
chmod 755 package/DEBIAN/postinst

cat > package/usr/local/bin/rb-assistant <<'EOF'
#!/usr/bin/env bash
exec /usr/bin/python3 /opt/rb-assistant/cli.py "$@"
EOF
chmod 755 package/usr/local/bin/rb-assistant

cat > package/DEBIAN/control <<EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: python3
Maintainer: RB Assistant <none@example.com>
Description: RB Assistant - offline semantic search over DeepSeek docs
 A simple assistant that builds a TF-IDF index and exposes a semantic search API.
EOF

chmod 755 package/DEBIAN
chmod 644 package/DEBIAN/control

dpkg-deb --build package "$OUTPUT_FILE"

echo "Created package: $OUTPUT_FILE"
