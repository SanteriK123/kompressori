# Maintainer: Your Name <you@example.com>
pkgname=kompressori
pkgver=1.0.0
pkgrel=1
pkgdesc="Simple video compressor using FFmpeg and PySide6"
arch=('x86_64')
url="https://example.com"
license=('GPL')
depends=('python' 'pyside6' 'ffmpeg')
makedepends=('python-setuptools' 'python-pip')
source=("kompressori.py" "kompressori.png" "README.md")
sha256sums=('SKIP' 'SKIP' 'SKIP')

package() {
    mkdir -p "$pkgdir/usr/bin"
    mkdir -p "$pkgdir/usr/share/applications"
    mkdir -p "$pkgdir/usr/share/icons/hicolor/128x128/apps"

    # Install main script
    install -Dm755 kompressori.py "$pkgdir/usr/bin/kompressori"

    # Install icon
    install -Dm644 kompressori.png "$pkgdir/usr/share/icons/hicolor/128x128/apps/kompressori.png"

    # Install .desktop file
    cat > "$pkgdir/usr/share/applications/kompressori.desktop" << EOF
[Desktop Entry]
Name=Kompressori
Exec=python3 /usr/bin/kompressori
Icon=kompressori
Type=Application
Categories=Utility;Video;
EOF
}

