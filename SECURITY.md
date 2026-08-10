# Security Policy

## Supported versions

Security fixes are applied to the latest version on the default branch.

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability or include credentials, cookies, tokens, private URLs, local paths, or downloaded media in a report.

Instead, contact the repository maintainer privately through the contact method listed on the repository profile. Include:

- A concise description of the issue and its impact.
- Steps to reproduce using non-sensitive example data.
- Suggested mitigations, if known.

Allow reasonable time for acknowledgment and remediation before public disclosure.

## Scope notes

Downloader from ABC is a local development application. Its API is not designed as an authenticated multi-user or internet-facing service. Do not expose it to untrusted networks without adding appropriate authentication, authorization, transport security, and deployment hardening.

## Firefox cookie handling

Downloader from ABC currently uses `yt-dlp` with `cookiesfrombrowser=("firefox",)` for media analysis and downloads. This causes `yt-dlp` to read cookies from the local Firefox profile of the user running Downloader from ABC.

- Cookie values are not bundled with Downloader from ABC, committed to this repository, uploaded to a Downloader from ABC server, shared with other users, or intentionally printed, logged, exported, or stored by the application.
- Each user uses their own local Firefox profile and should only use a profile they own or are authorized to access.
- Browser cookies can be sensitive account credentials. Do not submit them in issues, pull requests, logs, screenshots, or bug reports.
- Keep Downloader from ABC bound to a trusted local environment. Exposing the application to an untrusted network can create privacy and security risks beyond the local development use case.
