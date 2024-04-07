FROM archlinux:base-devel

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && date
RUN pacman-key --init && pacman-key --lsign-key "farseerfc@archlinux.org"
RUN pacman -Syu git python --noconfirm

COPY gitconfig /etc/gitconfig
COPY entrypoint.sh /entrypoint.sh

USER root

ENTRYPOINT ["/entrypoint.sh"]
