# Security

This public repository contains obfuscated loaders and a sealed game artifact.
Kinoue remains public and unobfuscated. Service credentials, runtime keys,
licenses, session files, device identifiers, and private game sources belong
outside this checkout.

The public loader has no secret. The server validates a device-bound session
before delivering execution material. Client requests reveal their destination;
a service URL is not a security boundary. An authorized recipient can capture
their delivered code and runtime key. This is not uncrackable copy protection.

New public files start from an independent Git root. Never import private Git
history. Before publishing, run the loader tests, index publication guard, and a
redacted Gitleaks scan. The guard checks the three runtime files against the
manifest and rejects embedded runtime-key assignments and private file paths.

If a credential is ever exposed, revoke it. Making a repository private cannot
erase existing third-party copies.
