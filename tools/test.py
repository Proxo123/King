import argparse
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--luau", default="luau")
parser.add_argument("--compiler", default="luau-compile")
args = parser.parse_args()
subprocess.run([args.compiler, "--null", "loader.luau", "Booga Booga Reborn/init.luau", "Booga Booga Reborn/King.protected.luau"], cwd=root, check=True)
source = "local ROOT_SOURCE = [====[" + (root / "loader.luau").read_text() + "]====]\n"
source += "local GAME_SOURCE = [====[" + (root / "Booga Booga Reborn/init.luau").read_text() + "]====]\n"
source += (root / "tests/loader.test.txt").read_text()
cache = root / ".cache"
cache.mkdir(exist_ok=True)
harness = cache / "loader-test.luau"
harness.write_text(source, encoding="utf-8", newline="\n")
subprocess.run([args.luau, str(harness)], cwd=root, check=True)

# Publication checks are also tested against synthetic bad files; values are
# intentionally fake and never printed when rejected.
from security_check import violations
assert violations("private/payload.luau", b"return true")
assert violations("Booga Booga Reborn/payload.luau", b"return true")
assert violations("King/private.json", b"{}")
assert violations(".env.production.local", b"CONFIG=fixture")
assert violations("fixture.region-key", b"fixture")
assert violations("fixture.delivery.luau", b"return true")
assert violations("loader.luau", b'context.ProtectionKey="' + b"a"*64 + b'"')
assert not violations("loader.luau", (root / "loader.luau").read_bytes())
print("PASS: private-file, runtime-script allowlist and deployment-address publication guard")
