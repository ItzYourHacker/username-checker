# Security Policy

## Project status

This is an experimental educational project. There is no formal security audit, supported release matrix, or guaranteed response time. Review [DISCLAIMER.md](DISCLAIMER.md) before using any network functionality.

## Sensitive data

Keep the following out of commits, issues, pull requests, screenshots, and shared archives:

- Discord authentication material in `input/tokens.txt` or elsewhere.
- Webhook URLs in `input/config.json`.
- Proxy credentials in `input/proxies.txt`.
- Private candidate lists, `available.txt`, `checkpoint.json`, and identifying logs.

These files are not encrypted by the application. Token validation displays credential fragments, and successful proxy tests display proxy entries. Review terminal output before sharing it.

The `.gitignore` protects against ordinary accidental staging of named local files. It does not sanitize history, untrack existing files, or apply to a manually uploaded archive. Only publish credential-free examples.

## Reporting a vulnerability

If the GitHub repository has private vulnerability reporting enabled, use its Security tab to submit a private report. Otherwise, use a private contact method explicitly published by the repository owner. No dedicated private reporting address is currently configured in this project.

If no private channel exists, open an issue asking the owner to enable one without including sensitive details. Never post real credentials or a working exploit publicly. A useful private report includes affected files, impact, an offline reproduction using fictional data, and a suggested mitigation.

## If a secret is exposed

1. Revoke or rotate the affected credential through the relevant provider immediately. Replace an exposed webhook and rotate exposed proxy credentials as applicable.
2. Remove the secret from the working files and ensure it is excluded from future commits.
3. Check repository history, pull requests, issues, logs, and artifacts for copies. Removing a current file does not erase older copies.
4. Coordinate any necessary history cleanup with collaborators. Treat public copies as potentially retained even after removal.
5. Review the affected account or service for unexpected activity.

## Safe verification

Use mocked responses and local fixtures when investigating defects. Do not test credential theft, access-control bypasses, or rate-limit evasion against live services.
