#!/usr/bin/env python3
"""Daemon upload delete stats report deleted files."""

import subprocess

from rsyncfns import (
    FROMDIR, TODIR,
    build_rsyncd_conf, forced_protocol, makepath, rmtree, rsync_argv,
    start_test_daemon, test_fail, test_skipped,
)


# The delete-stats wire message (NDX_DEL_STATS) only exists at protocol >= 31,
# so a daemon can't report its delete counts to an older client.
pv = forced_protocol()
if pv is not None and pv < 31:
    test_skipped(f"daemon delete stats need protocol 31+ (pinned to {pv})")

DAEMON_PORT = 12899

src = FROMDIR
dst = TODIR

rmtree(src)
rmtree(dst)
makepath(src, dst)

(src / 'keep.txt').write_text("keep\n")
(dst / 'keep.txt').write_text("keep\n")
(dst / 'delete.txt').write_text("delete\n")

url = start_test_daemon(build_rsyncd_conf(), DAEMON_PORT)

proc = subprocess.run(
    rsync_argv('-a', '--delete', '-i', '--stats', f'{src}/', f'{url}test-to/'),
    capture_output=True,
    text=True,
)
out = proc.stdout + proc.stderr
print(out)

if proc.returncode != 0:
    test_fail(f"daemon upload delete run exited {proc.returncode}")

if '*deleting   delete.txt' not in out:
    test_fail(f"daemon upload did not itemize the deleted file:\n{out}")

if 'Number of deleted files: 1 (reg: 1)' not in out:
    test_fail(f"daemon upload did not report the deleted file in stats:\n{out}")
