# portage-sqfssync

**portage-sqfssync** is a portage compatible sync plugin to download
and mount the latest SquashFS portage snapshot found
[here](http://distfiles.gentoo.org/snapshots/squashfs/).

This plugin can be configured within *repos.conf* and used with
`emaint sync -r gentoo` or `emerge --sync`, just like a normal rsync.

## Installation

Either use my ebuild shipped with my own
[portage overlay](https://github.com/g0dscookie/cookie-monster)
or clone this repository and use *setup.py* to install locally:

```sh
git clone https://github.com/g0dsCookie/portage-sqfssync.git
cd portage-sqfssync
sudo ./setup.py install
```

This will install the *sqfssync* module into *portage.sync.modules.sqfssync*.

## Requirements

* \>=dev-lang/python-3.6
* sys-apps/util-linux[python]
* dev-python/urllib3

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

| Option         | Description                                                  | Default |
| -------------- | ------------------------------------------------------------ | ------- |
| file           | SquashFS file to download from *sync-uri*                    | gentoo-current.xz.sqfs |
| verify         | Should the downloaded file be verified?                      | yes |
| signature-file | The file containing the signature for *sync-sqfs-file*       | sha512sum.txt |
| uid            | The *uid=* option passed to mount.                           | portage |
| gid            | The *gid=* option passed to mount.                           | portage |
| mode           | The *mode=* option passed to mount.                          | 0555 |
| options        | Additional mount options.                                    | |
| tmpdir         | Path to the temporary directory to download new SquashFS to. | $PORTAGE_TMPDIR or /tmp if unset. |
