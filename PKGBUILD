# Maintainer: SanteriK123 <kaisanteri@pm.me>
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
sha256sums=('726517c33eac0c15f9c353bca6bf696305f0a4ccb81f008fc35e58ec36fff833'
            '66198a2fafa8ce066fddebfdc3ad19541a5bba64e418bd192d52ac3bb2e0f412'
            'be57c4a11f115de30729e536f4b4763b595bb8b3ed0cab2e5aaddc530b76ca0e'
)

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
Description=Video compression utility
Comment=Compresses videos to a desired size
Exec=python3 /usr/bin/kompressori
Icon=kompressori
Type=Application
Categories=Utility;Video;
EOF
}

