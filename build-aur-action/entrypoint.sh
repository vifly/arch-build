#!/bin/bash

pkgname=$1

useradd builder -m
echo "builder ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
chmod -R a+rw .

cat << EOM >> /etc/pacman.conf
[archlinuxcn]
Server = https://repo.archlinuxcn.org/x86_64
EOM

pacman -Syu --noconfirm
pacman -S yay --noconfirm

sudo --set-home -u builder yay -S "$pkgname"
mv ./.cache/yay/* ./

