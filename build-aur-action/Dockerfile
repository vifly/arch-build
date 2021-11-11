FROM archlinux:latest

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
RUN date
RUN pacman -Syu --noconfirm
RUN pacman -S base-devel git --noconfirm
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"] 
