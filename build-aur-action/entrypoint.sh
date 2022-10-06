#!/bin/bash

pkgname=$1
preinstall_pkgs=$2

useradd builder -m
echo "builder ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
chmod -R a+rw .

cat << EOM >> /etc/pacman.conf
[archlinuxcn]
Server = https://repo.archlinuxcn.org/x86_64
EOM

pacman-key --init
pacman -Sy --noconfirm && pacman -S --noconfirm archlinuxcn-keyring
pacman -Syu --noconfirm yay "$preinstall_pkgs"

sudo --set-home -u builder yay -S --noconfirm --builddir=./ "$pkgname"
