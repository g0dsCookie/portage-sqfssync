import os
import logging
import typing
from hashlib import sha512
import urllib.parse
import shutil
import io
from datetime import datetime, timedelta

import portage
from portage.util import writemsg_level
from portage.sync.syncbase import NewBase

from gemato.openpgp import GNUPG, OpenPGPEnvironment, OpenPGPSignatureList
from gemato.exceptions import GematoException

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
    def yesterday(self) -> str:
        return (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')

    @property
    def filename(self) -> str:
        today = datetime.now().strftime('%Y%m%d')
        return self.repo.module_specific_options.get(
            'sync-sqfs-file',
            'gentoo-%(yesterday)s.xz.sqfs' % {'yesterday': self.yesterday})

    @property
    def verify_sig(self) -> bool:
        return self.repo.module_specific_options.get(
            "sync-sqfs-verify", "yes").lower() in ("true", "yes")

    @property
    def openpgp_key_path(self) -> str:
        return self.repo.module_specific_options.get(
            "sync-openpgp-key-path",
            "/usr/share/openpgp-keys/gentoo-release.asc")

    @property
    def signature_file(self) -> str:
        return self.repo.module_specific_options.get(
            'sync-sqfs-signature-file',
            'gentoo-%(yesterday)s.sha512sum.txt' % {'yesterday': self.yesterday})

    @property
    def mount_options(self) -> str:
        opts = []
        extra = self.repo.module_specific_options.get("sync-sqfs-options")
        if extra:
            opts.append(extra)
        return ",".join(opts)

    @property
    def tempdir(self) -> str:
        tmpdir = self.repo.module_specific_options.get("sync-sqfs-tmpdir")
        if not tmpdir:
            tmpdir = os.getenv("PORTAGE_TMPDIR", "/tmp")
        return tmpdir

    def _is_mounted(self) -> bool:
        return os.path.ismount(self.repo.location)

    def _unmount(self, dir) -> bool:
        ctx = mnt.Context()
        ctx.target = dir
        try:
            ctx.umount()
        except Exception as err:
            writemsg_level("Failed to unmount %s: %r\n" % (dir, err),
                           level=logging.ERROR, noiselevel=-1)
            return False
        return True

    def _mount(self, source: str, target: str) -> bool:
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
            return False
        return True

    def _pgp_verify(self,
                    openpgp_env: OpenPGPEnvironment,
                    f: typing.IO[str]) -> tuple[bytes, OpenPGPSignatureList]:
        exitst, out, err = openpgp_env._spawn_gpg(
                [GNUPG, '--batch', '--status-fd', '1', '--verify', '-o', '-'],
                f.read().encode('utf8'))

        out_arr: list[bytes] = out.split(b'\n')
        if len(out_arr) == 0:
            return # TODO

        gpg_plainstart = out_arr.pop(0)
        if not gpg_plainstart.startswith(b'[GNUPG:] PLAINTEXT'):
            return # TODO

        gpg_plain_arr: list[bytes] = []
        for line in out_arr:
            if line.startswith(b'[GNUPG:]'):
                break
            gpg_plain_arr.append(line)

        gpg_plain = b'\n'.join(gpg_plain_arr)
        out = b'\n'.join(out_arr[len(gpg_plain_arr):])

        return (gpg_plain,
                openpgp_env._process_gpg_verify_output(out, err, True))

    def _fetch_signature(self) -> str:
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

        openpgp_env = self._get_openpgp_env(self.openpgp_key_path)
        if openpgp_env is None:
            writemsg_level("Failed to initialize OpenPGP environment\n",
                           level=logging.ERROR, noiselevel=-1)
            return

        try:
            with open(self.openpgp_key_path, "rb") as f:
                openpgp_env.import_key(f)

            verify_buffer = io.StringIO(r.data.decode("utf8"))
            verified_data, signatures = self._pgp_verify(openpgp_env,
                                                         verify_buffer)
            openpgp_env.close()
        except GematoException as e:
            writemsg_level(
                f"Failed to validate digest signature:\n{e}\n",
                level=logging.ERROR,
                noiselevel=-1,
            )
            return

        lines = verified_data.decode("utf8").split("\n")
        for line in lines:
            if not line:
                continue
            if line.endswith(self.filename):
                return line[:128]

    def _download(self) -> tuple[str, bool]:
        url = urllib.parse.urljoin(self.repo.sync_uri, self.filename)
        tmpfile = os.path.join(self.tempdir, self.filename + ".tmp")

        if self.verify_sig:
            signature = self._fetch_signature()
            if not signature:
                writemsg_level("Could not find SHA512 signature for %s\n" %
                               self.filename, level=logging.ERROR,
                               noiselevel=-1)
                return ("", False)
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
                return ("", False)

        return (tmpfile, True)

    def exists(self) -> bool:
        """Tests whether the directory exists and is mounted"""
        return os.path.exists(self.repo.location)

    def update(self) -> tuple[int, bool]:
        """Download latest squashfs and remount."""
        destfile = os.path.join(self.repo.location.rstrip("/") + ".sqfs")
        destfile_new = destfile + ".new"
        tmpfile, success = self._download()
        if not success or not tmpfile:
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

    def new(self, **kwargs) -> tuple[int, bool]:
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
