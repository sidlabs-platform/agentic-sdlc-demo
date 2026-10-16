#!/usr/bin/env python3
"""Run checksum-pinned actionlint on supported template-maintenance platforms."""

import hashlib
import io
import platform
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path

from sdlc.contracts import require

VERSION = "1.7.7"
BINARIES = {
    ("Linux", "x86_64"): ("linux_amd64", "023070a287cd8cccd71515fedc843f1985bf96c436b7effaecce67290e7e0757"),
    ("Darwin", "arm64"): ("darwin_arm64", "2693315b9093aeacb4ebd91a993fea54fc215057bf0da2659056b4bc033873db"),
}


def main():
    target = BINARIES.get((platform.system(), platform.machine()))
    require(target, "Run template workflow validation on Linux x64 or macOS arm64; application runners are independent")
    name, checksum = target
    url = f"https://github.com/rhysd/actionlint/releases/download/v{VERSION}/actionlint_{VERSION}_{name}.tar.gz"
    with urllib.request.urlopen(url, timeout=60) as response:
        archive = response.read()
    require(hashlib.sha256(archive).hexdigest() == checksum, "actionlint download checksum mismatch")
    with tempfile.TemporaryDirectory(prefix="sdlc-actionlint-") as directory:
        executable = Path(directory) / "actionlint"
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            member = bundle.getmember("actionlint")
            require(member.isfile() and member.size < 50_000_000, "Invalid actionlint archive")
            executable.write_bytes(bundle.extractfile(member).read())
        executable.chmod(0o700)
        # Static expressions are checked; shellcheck is deliberately not downloaded implicitly.
        subprocess.run([str(executable), "-color", "-shellcheck=",
                        *map(str, sorted(Path(".github/workflows").glob("*.yml")))],
                       check=True, timeout=120)


if __name__ == "__main__":
    main()
