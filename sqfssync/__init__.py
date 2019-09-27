doc = """SquashFS plug-in module for portage.
Downloads latest squashfs, unmounts old
and mounts the new one.
"""
__doc__ = doc
__version__ = "0.1.1"


from portage.localization import _
from portage.sync.config_checks import CheckSyncConfig


module_spec = {
    "name": "sqfssync",
    "description": doc,
    "provides": {
        "sqfssync-module": {
            "name": "sqfssync",
            "sourcefile": "sqfssync",
            "class": "SqfsSync",
            "functions": ["sync", "new", "exists"],
            "func_desc": {
                "sync": "Download latest squashfs and mount to destination",
                "new": "Creates the new repository at the specified location",
                "exists": "Returns a boolean of whether the specified dir " +
                    "exists and the squashfs is mounted",
            },
            "validate_config": CheckSyncConfig,
            "module_specific_options": (
                "sync-sqfs-file",
                "sync-sqfs-verify",
                "sync-sqfs-signature-file",
                "sync-sqfs-uid",
                "sync-sqfs-gid",
                "sync-sqfs-mode",
                "sync-sqfs-options",
                "sync-sqfs-tmpdir",
            )
        }
    }
}
