# Contributing

Thank you for helping improve the project's educational value, correctness, and documentation. Read [README.md](README.md), [DISCLAIMER.md](DISCLAIMER.md), and [SECURITY.md](SECURITY.md) first.

## Issues

Describe the expected behavior, actual behavior, Python version, operating system, and smallest reproduction. Use fictional usernames and sanitized configuration. Do not include tokens, webhook URLs, authenticated proxy addresses, private results, or unredacted terminal screenshots.

For security-sensitive reports, follow [SECURITY.md](SECURITY.md) rather than posting an exploit or credential publicly.

## Changes

1. Keep each change focused on a specific problem.
2. Explain the behavior before and after the change.
3. Update documentation when configuration, file paths, or behavior changes.
4. Verify relevant behavior locally using generated data and mock HTTP responses.
5. Describe the verification performed and any remaining limitations in the pull request.

Install dependencies using the virtual-environment instructions in the README. There is currently no automated test suite or CI configuration. Do not use live Discord requests as a routine test strategy.

Contributions should improve safe study, reliability, or authorized integrations. Do not add credential collection, enforcement evasion, or instructions for obtaining user-account tokens.

## Useful improvements

- Add an offline mode and deterministic HTTP fixtures.
- Implement global request pacing and explicit cancellation handling.
- Bound generation attempts and validate configuration values.
- Track completed candidates and make checkpoint saves atomic.
- Remove credential fragments and authenticated proxy URLs from terminal output.
- Verify proxy behavior and drain webhook queues on shutdown.
- Add meaningful tests for parsing, generation, and checkpoint recovery.

## Publication hygiene

Inspect staged files before opening a pull request. Keep local settings, tokens, proxies, wordlists, results, checkpoints, and logs out of commits. Git ignore rules do not remove previously committed content.

No project license has been selected. Proposed contributions do not by themselves establish licensing terms; the repository owner and contributors should resolve reuse and contribution permissions before accepting code for redistribution.
