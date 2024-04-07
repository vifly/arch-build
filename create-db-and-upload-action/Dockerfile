FROM archlinux:base-devel

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && date
RUN pacman-key --init
RUN pacman -Syu git python rclone pyalpm --noconfirm && sed -i '/E_ROOT/d' /usr/bin/makepkg

COPY gitconfig /etc/gitconfig
COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
