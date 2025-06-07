FROM gentoo/stage3

RUN set -e \
 && echo "MAKEOPTS=\"-j$(nproc)\"" >>/etc/portage/make.conf \
 && echo "sys-apps/util-linux python" >>/etc/portage/package.use/util-linux \
 && echo "sys-fs/squashfs-tools lz4 lzma lzo zstd" >>/etc/portage/package.use/squashfs-tools \
 && emerge --sync \
 && emerge --jobs=$(nproc) -vuDN \
        sys-apps/util-linux sys-fs/squashfs-tools \
        dev-vcs/git dev-python/urllib3 dev-python/python-gnupg \
        app-editors/vim
