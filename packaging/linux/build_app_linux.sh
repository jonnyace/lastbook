#!/bin/bash
# Builds the Lastbook .deb for one Ubuntu LTS release, x86_64. Run inside that release (a container is fine) from a checkout:
#   apt-get install -y python3 python3-venv python3-pil dpkg-dev binutils   (the script installs them itself when run as root)
#   bash packaging/linux/build_app_linux.sh
# Each release has its own python3, and the wheels in lib/ are built for one Python only, so each release gets its own .deb:
#   Ubuntu 24.04  python3 3.12  Lastbook_<version>_amd64.deb               Version: <version>
#   Ubuntu 26.04  python3 3.14  Lastbook_<version>_ubuntu26.04_amd64.deb   Version: <version>+ubuntu26.04
# The two hold different files, so they have different versions; +ubuntu26.04 sorts after <version>, so apt takes it as the newer one.
#
# What the .deb holds (nothing is written outside these at install, and nothing at all at removal but these):
#   /opt/lastbook/            lastbook.py (the launcher), app/ (main, bridge, shell_linux), server.py and the engine, web/ and content/ as they
#                             ship (ship_app_files.py), setup/manifest-v1.json, engine/setup/roots.pem, lib/ (wheels for the system's
#                             python3, 3.12 or 3.14: requirements_linux.txt), llm/ (lastbook-llm and its llama.cpp libraries, when derived/llm/bin-linux
#                             has them: packaging/llm/build_llm_linux.sh), gst/ (lastbooksrc, the video source: gst/lastbooksrc.c), VERSION
#   /usr/bin/lastbook          runs /usr/bin/python3 -I -B /opt/lastbook/lastbook.py
#   /usr/share/applications/lastbook.desktop, /usr/share/icons/hicolor/<size>/apps/lastbook.png
# The window is the system's GTK 3 and WebKitGTK 4.1 through python3-gi (Depends below). The person's library, settings and WebKit's
# storage live in their home folder (~/.local/share/Lastbook, ~/.config/Lastbook, ~/.cache/Lastbook) and the package never touches them.
# Each build gets derived/app-build/linux/<date-time>/; derived/app-build/linux/latest.deb points at the newest good one.
set -euo pipefail
HERE="$(dirname "$(realpath "$0")")"
ROOT="$(dirname "$(dirname "$HERE")")"
APP_VERSION="${LASTBOOK_VERSION:-1.1.13}"
BUILD="$ROOT/derived/app-build/linux"
OUT="$BUILD/$(date +%Y%m%d-%H%M%S)"
STAGE="$OUT/root"
LLM="$ROOT/derived/llm/bin-linux"
export PYTHONDONTWRITEBYTECODE=1

[ "$(uname -m)" = x86_64 ] || { echo "build on x86_64" >&2; exit 1; }
OS="$(. /etc/os-release; echo "$ID $VERSION_ID")"
case "$OS" in                         # the release, its own python3, and the .deb's version and file name
  "ubuntu 24.04") WANT_PY=3.12; DEB_VERSION="$APP_VERSION"; DEB="$OUT/Lastbook_${APP_VERSION}_amd64.deb" ;;
  "ubuntu 26.04") WANT_PY=3.14; DEB_VERSION="$APP_VERSION+ubuntu26.04"; DEB="$OUT/Lastbook_${APP_VERSION}_ubuntu26.04_amd64.deb" ;;
  *) echo "build on Ubuntu 24.04 or 26.04 (this is $OS): the wheels must match its python3" >&2; exit 1 ;;
esac
if [ "$(id -u)" = 0 ] && ! { python3 -c 'import venv, PIL' 2>/dev/null && pkg-config --exists gstreamer-base-1.0; }; then
  apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-venv python3-pil dpkg-dev binutils file gcc pkg-config libgstreamer1.0-dev >/dev/null
fi
PYV="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
[ "$PYV" = "$WANT_PY" ] || { echo "python3 is $PYV, not $WANT_PY" >&2; exit 1; }
PY_NEXT="${PYV%.*}.$(( ${PYV#*.} + 1 ))"   # the .deb needs this python3 exactly: lib/ holds compiled modules for it alone
mkdir -p "$OPT"

# web/ and content/ as they ship, and what setup can install (the same steps as the Mac and Windows builds)
python3 -I -B "$ROOT/packaging/ship_app_files.py" "$OUT/ship"
python3 -I -B "$ROOT/packaging/release_manifest.py" --packs "$ROOT/derived/release/manifest-v1.json" --out "$OUT/ship/setup/manifest-v1.json"
if [ "${SKIP_TLS_GATE:-}" != 1 ]; then   # release gate: every download host verifies through engine/setup/roots.pem only
  python3 -I -B "$ROOT/packaging/check_tls_roots.py" || { echo "TLS roots gate failed: refresh engine/setup/roots.pem (packaging/setup_roots.py)" >&2; exit 1; }
fi

# The wheels, for this python3, into lib/
python3 -m venv "$OUT/tools"
"$OUT/tools/bin/pip" install -q --disable-pip-version-check --only-binary=:all: --no-compile --target "$OUT/vendor" -r "$HERE/requirements_linux.txt"
# Compile the existing custom-scheme media source, then use the shared layout.
gcc -shared -fPIC -O2 -Wall -Werror -s -ffile-prefix-map="$HERE"=lastbook "$HERE/gst/lastbooksrc.c" -o "$OUT/libgstlastbooksrc.so" $(pkg-config --cflags --libs gstreamer-1.0 gstreamer-base-1.0)
LLM_ARGS=()
LLM_NOTE="without the local AI's runner (no $LLM/lastbook-llm yet)"
if [ -x "$LLM/lastbook-llm" ]; then
  LLM_ARGS=(--llm "$LLM")
  LLM_NOTE="with the local AI's runner from $LLM"
fi
python3 -I -B "$HERE/stage_linux.py" --source "$ROOT" --ship "$OUT/ship" --vendor "$OUT/vendor" \
  --plugin "$OUT/libgstlastbooksrc.so" --stage "$STAGE" --version "$APP_VERSION" "${LLM_ARGS[@]}"

# The package. Depends: the system's window (GTK 3, WebKitGTK 4.1 and its GObject bindings) and the codecs the library's videos need:
# H.264/AAC in MP4 through gstreamer1.0-libav, WebM and the rest through gstreamer1.0-plugins-good, and AV1 (many of the library's
# first-aid videos) through gstreamer1.0-plugins-bad's dav1d decoder: without it they play with sound but a black picture. With them
# present, WebKit never asks the system to go and look for a codec. The local AI's runner needs libgomp1, and libvulkan1 for graphics cards (else it runs on the CPU).
mkdir -p "$STAGE/DEBIAN"
SIZE_KB="$(du -sk --exclude=DEBIAN "$STAGE" | cut -f1)"
cat > "$STAGE/DEBIAN/control" <<CTRL
Package: lastbook
Version: $DEB_VERSION
Architecture: amd64
Maintainer: Lastbook <noreply@lastbook.org>
Installed-Size: $SIZE_KB
Depends: python3 (>= $PYV), python3 (<< $PY_NEXT), python3-gi, gir1.2-gtk-3.0, gir1.2-webkit2-4.1, gir1.2-soup-3.0, libwebkit2gtk-4.1-0 (>= 2.40), libgstreamer1.0-0, gstreamer1.0-plugins-base, gstreamer1.0-plugins-good, gstreamer1.0-plugins-bad, gstreamer1.0-libav, libgomp1
Recommends: libvulkan1
Section: education
Priority: optional
Homepage: https://lastbook.org
Description: Offline survival library
 Lastbook searches and reads a survival library kept on this computer: guides,
 manuals, videos, maps and an encyclopedia, with no internet. It opens no network
 port. Setup downloads the library the first time; nothing else goes online unless
 you ask it to check for a newer version. The person's library and settings stay
 in their home folder and are never removed with the package.
CTRL
dpkg-deb --root-owner-group -Zxz --build "$STAGE" "$DEB" >/dev/null
python3 -I -B "$HERE/scan_package_linux.py" "$DEB" --terms-file "$ROOT/derived/app-build/scan-terms.txt" | tee "$OUT/scan.txt"
ln -sfn "$(basename "$OUT")/$(basename "$DEB")" "$BUILD/latest.deb"
echo "Built $LLM_NOTE: $DEB"
ls -l "$DEB"
sha256sum "$DEB" | tee "$DEB.sha256"
