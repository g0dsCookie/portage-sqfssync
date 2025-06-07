# portage-sqfssync

**portage-sqfssync** is a portage compatible sync plugin to download
and mount the latest SquashFS portage snapshot found
[here](http://distfiles.gentoo.org/snapshots/squashfs/).

This plugin can be configured within *repos.conf* and used with
`emaint sync -r gentoo` or `emerge --sync`, just like a normal rsync.

## Installation

Clone this repository and use *pip* to install locally:

```sh
git clone https://github.com/g0dsCookie/portage-sqfssync.git
cd portage-sqfssync
sudo python -m pip install --break-system-packages .
```

Or create/use an ebuild for this.
Here's an older [example](https://github.com/g0dsCookie/cookie-monster/blob/master/app-portage/sqfssync/sqfssync-0.1.1.ebuild).

### Legacy

**Calling *setup.py* directly will soon be removed.**

Clone this repository and use *setup.py* to install locally:

```sh
git clone https://github.com/g0dsCookie/portage-sqfssync.git
cd portage-sqfssync
sudo ./setup.py install
```

This will install the *sqfssync* module into *portage.sync.modules.sqfssync*.

## Requirements

* \>=dev-lang/python-3.6
* dev-python/pip (to install this)
* sys-apps/util-linux[python]
* dev-python/urllib3
* sys-fs/squashfs-tools

## Configuration

You can configure *sqfssync* within *repos.conf* just like any other sync
module (e.g. laymansync, rsync, git, etc.):

```ini
[gentoo]
location = /var/db/portage
sync-type = sqfssync
sync-uri = http://distfiles.gentoo.org/snapshots/squashfs/
```

## Additional configuration options

The following additional configuration options are available.
These are all prefixed by *sync-sqfs-*, e.g. *sync-sqfs-file*.

| Option                | Description                                                  | Default |
| --------------------- | ------------------------------------------------------------ | ------- |
| file                  | SquashFS file to download from *sync-uri*                    | gentoo-current.xz.sqfs |
| verify                | Should the downloaded file be verified?                      | yes |
| sync-openpgp-key-path | Path to keyring to validate digest signature against         | /usr/share/openpgp-keys/gentoo-release.asc |
| signature-file        | The file containing the signature for *sync-sqfs-file*       | sha512sum.txt |
| options               | Additional mount options.                                    | |
| tmpdir                | Path to the temporary directory to download new SquashFS to. | $PORTAGE_TMPDIR or /tmp if unset. |
