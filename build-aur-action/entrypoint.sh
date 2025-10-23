#!/bin/bash

pkgname=$1

useradd builder -m
echo "builder ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
chmod -R a+rw .

pacman-key --init
pacman -Syu --noconfirm archlinux-keyring
install-yay(){
  pacman -S --needed --noconfirm base-devel
  sudo --set-home -u builder git clone https://aur.archlinux.org/yay-bin.git buildyay
  cd buildyay
  sudo --set-home -u builder makepkg -si --noconfirm
  cd ..
  rm -rf buildyay
}
install-yay
if [ ! -z "$INPUT_PREINSTALLPKGS" ]; then
    pacman -Su --noconfirm "$INPUT_PREINSTALLPKGS"
fi

sudo --set-home -u builder yay -S --noconfirm --builddir=./ "$pkgname"

# Find the actual build directory (pkgbase) created by yay.
# Some AUR packages use a different pkgbase directory name,
# e.g. otf-space-grotesk has a pkgbase 38c3-styles, 
# when using yay -S otf-space-grotesk, it's built under folder 38c3-styles.
function get_pkgbase(){
  local pkg="$1"
  url="https://aur.archlinux.org/rpc/?v=5&type=info&arg=${pkg}"
  resp="$(curl -sS "$url")"
  pkgbase="$(printf '%s' "$resp" | jq -r '.results[0].PackageBase // .results[0].Name')"
  echo "$pkgbase"
}

if [[ -d "$pkgname" ]];
  then
    pkgdir="$pkgname"
  else
    pacman -S --needed --noconfirm jq
    pkgdir="$(get_pkgbase $pkgname)"
fi

echo "The pkgdir is $pkgdir"
echo "The pkgname is $pkgname"
cd $pkgdir || exit 1
python3 ../build-aur-action/encode_name.py
