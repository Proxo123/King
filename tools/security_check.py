"""Check tracked/staged public files without printing sensitive values."""
import re
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PARTS = {".cache", ".vercel", ".venv", "node_modules", "var", "private", "__pycache__"}
PRIVATE_NAMES = {"auth.json", "private.json", "secret.key", "admin-login.json", "admin-password.hash"}
PRIVATE_SUFFIXES = {".pem", ".p12", ".pfx", ".sqlite", ".sqlite3", ".db"}
DEPLOYMENT = re.compile(rb"https?://[^\s\"'<>]*\.(?:vercel\.app|neon\.tech|upstash\.io)(?::[0-9]+)?", re.I)
PRIVATE_KEY = re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----")


def violations(name, content):
    path = PurePosixPath(name)
    found = []
    if path.suffix.lower() in {".lua", ".luau"} and name not in {"loader.luau", "Booga Booga Reborn/init.luau", "Booga Booga Reborn/King.protected.luau"}:
        found.append((name, 0, "only the two obfuscated loaders and the sealed game artifact may be tracked"))
    if (set(path.parts) & PRIVATE_PARTS or path.name in PRIVATE_NAMES or path.suffix.lower() in PRIVATE_SUFFIXES
            or path.name.endswith((".key", ".region-key", ".policy.json"))
            or ".private." in path.name or ".delivery." in path.name or ".original." in path.name
            or path.name.startswith(".env") and path.name != ".env.example"):
        found.append((name, 0, "private file must not be tracked"))
    for index, line in enumerate(content.splitlines(), 1):
        if DEPLOYMENT.search(line):
            found.append((name, index, "deployment address must stay in private configuration"))
        if PRIVATE_KEY.search(line):
            found.append((name, index, "private key material"))
    if re.search(rb"ProtectionKey\s*=\s*[\"\'][0-9a-fA-F]{64}[\"\']", content):
        found.append((name, 0, "private delivery response or embedded runtime key"))
    return found


def main():
    # Read from Git's index, not the working tree: ignored local credentials and
    # untracked dependencies never enter this audit or the publication bundle.
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    problems = []
    indexed = {}
    for name in filter(None, names):
        content = subprocess.check_output(["git", "show", ":" + name], cwd=ROOT)
        indexed[name] = content
        problems.extend(violations(name, content))
    try:
        manifest = json.loads(indexed["manifest.json"])
        expected = {"loader.luau", "Booga Booga Reborn/init.luau", "Booga Booga Reborn/King.protected.luau"}
        assert manifest["format"] == 1 and manifest["version"] == "0.6.0"
        assert set(manifest["artifacts"]) == expected
        for filename, metadata in manifest["artifacts"].items():
            assert hashlib.sha256(indexed[filename]).hexdigest() == metadata["sha256"]
        assert manifest["artifacts"]["Booga Booga Reborn/King.protected.luau"]["runtime_keyed"] is True
    except (AssertionError, KeyError, TypeError, ValueError):
        problems.append(("manifest.json", 0, "release artifact manifest does not match the staged runtime files"))
    for name, line, message in problems:
        print(f"{name}:{line}: {message}")
    if problems:
        raise SystemExit(1)
    print("PASS: tracked public files contain no private configuration paths or deployment addresses")


if __name__ == "__main__":
    main()
