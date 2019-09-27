import os
import logging
from hashlib import sha512
import urllib.parse
import shutil

import portage
from portage.util import writemsg_level
from portage.sync.syncbase import NewBase

import libmount as mnt
import urllib3


class SqfsSync(NewBase):
    """SquashFS sync class"""

    short_desc = "Downloads and mounts latest squashfs"

    CHUNK_SIZE = 2048

    @staticmethod
    def name():
        return "SqfsSync"

    def __init__(self):
        # we don't need any external binary
        # however we need the following packages/use flags
        # sys-apps/util-linux[python]
        # dev-python/urllib3
        super().__init__("mount", "sys-apps/util-linux")
        self._http = urllib3.PoolManager()

    @property
    def filename(self):
        return self.repo.module_specific_options.get(
            "sync-sqfs-file", "gentoo-current.xz.sqfs")

    @property
    def verify_sig(self):
        return self.repo.module_specific_options.get(
            "sync-sqfs-verify", "yes").lower() in ("true", "yes")

    @property
    def signature_file(self):
        return self.repo.module_specific_options.get(
            "sync-sqfs-signature-file", "sha512sum.txt")

    @property
    def uid(self):
        return self.repo.module_specific_options.get("sync-sqfs-uid",
                                                     "portage")

    @property
    def gid(self):
        return self.repo.module_specific_options.get("sync-sqfs-gid",
                                                     "portage")

    @property
    def mode(self):
        return self.repo.module_specific_options.get("sync-sqfs-mode",
                                                     "0555")

    @property
    def mount_options(self):
        opts = [
            "uid=%s" % self.uid,
            "gid=%s" % self.gid,
            "mode=%s" % self.mode
        ]
        extra = self.repo.module_specific_options.get("sync-sqfs-options")
        if extra:
            opts.append(extra)
        return ",".join(opts)

    @property
    def tempdir(self):
        tmpdir = self.repo.module_specific_options.get("sync-sqfs-tmpdir")
        if not tmpdir:
            tmpdir = os.getenv("PORTAGE_TMPDIR", "/tmp")
        return tmpdir

    def _is_mounted(self):
        return os.path.ismount(self.repo.location)

    def _unmount(self, dir):
        ctx = mnt.Context()
        ctx.target = dir
        try:
            ctx.umount()
        except Exception as err:
            writemsg_level("Failed to unmount %s: %r\n" % (dir, err),
                           level=logging.ERROR, noiselevel=-1)
            return
        return True

    def _mount(self, source, target):
        ctx = mnt.Context()
        ctx.source = source
        ctx.target = target
        ctx.options = self.mount_options
        ctx.fstype = "squashfs"

        try:
            ctx.mount()
        except Exception as err:
            writemsg_level("Failed to mount %s: %r\n" % (source, err),
                           level=logging.ERROR, noiselevel=-1)
            return
        return True

    def _fetch_signature(self):
        writemsg_level("Fetching file signature...\n")
        digest_uri = urllib.parse.urljoin(self.repo.sync_uri,
                                          self.signature_file)
        r = self._http.request("GET", digest_uri)

        if r.status != 200:
            writemsg_level("Could not fetch signature from %s: %s\n" % (
                digest_uri,
                "Server returned %d" % r.status
            ), level=logging.ERROR, noiselevel=-1)
            return

        lines = r.data.decode("utf8").split("\n")
        for line in lines:
            if not line:
                continue
            if line.endswith(self.filename):
                return line[:128]

    def _download(self):
        url = urllib.parse.urljoin(self.repo.sync_uri, self.filename)
        tmpfile = os.path.join(self.tempdir, self.filename + ".tmp")

        if self.verify_sig:
            signature = self._fetch_signature()
            if not signature:
                writemsg_level("Could not find SHA512 signature for %s\n" %
                               self.filename, level=logging.ERROR,
                               noiselevel=-1)
                return (1, False)
            hasher = sha512()

        writemsg_level("Downloading new SquashFS file...\n")
        r = self._http.request("GET", url, preload_content=False)
        with open(tmpfile, "wb") as out:
            while True:
                data = r.read(self.CHUNK_SIZE)
                if not data:
                    break
                out.write(data)
                if self.verify_sig:
                    hasher.update(data)
        r.release_conn()

        if self.verify_sig:
            if hasher.hexdigest() != signature:
                writemsg_level("Signature %s does not match!\n" %
                               hasher.hexdigest(),
                               level=logging.ERROR, noiselevel=-1)
                return

        return tmpfile

    def exists(self):
        """Tests whether the directory exists and is mounted"""
        return os.path.exists(self.repo.location)

    def update(self):
        """Download latest squashfs and remount."""
        destfile = os.path.join(self.repo.location.rstrip("/") + ".sqfs")
        destfile_new = destfile + ".new"
        tmpfile = self._download()
        if not tmpfile:
            return (1, False)

        writemsg_level("Replacing old SquashFS with new one...\n")
        try:
            shutil.move(tmpfile, destfile_new)
        except OSError as err:
            writemsg_level("Could not move temporary file %s\n" +
                           " to destination %s: %r\n" % (tmpfile, destfile_new,
                                                         err),
                           level=logging.ERROR, noiselevel=-1)
            return (2, False)

        if self._is_mounted():
            if not self._unmount(self.repo.location):
                return (3, False)

        if os.path.exists(destfile):
            try:
                os.remove(destfile)
            except OSError as err:
                writemsg_level("Could not remove %s: %r\n" % (destfile, err),
                               level=logging.ERROR, noiselevel=-1)
                return (4, False)

        try:
            os.rename(destfile_new, destfile)
        except OSError as err:
            writemsg_level("Could not rename %s to %s: %r\n" % (
                destfile_new, destfile, err
            ), level=logging.ERROR, noiselevel=-1)
            return (5, False)

        if not self._mount(destfile, self.repo.location):
            return (6, False)
        return (os.EX_OK, True)

    def new(self, **kwargs):
        """Do the initial download and install of the repository"""
        if kwargs:
            self._kwargs(kwargs)
        try:
            if not os.path.exists(self.repo.location):
                os.makedirs(self.repo.location)
                self.logger(self.xterm_titles,
                            "Created new directory %s" % self.repo.location)
        except IOError:
            return (1, False)
        return self.update()
