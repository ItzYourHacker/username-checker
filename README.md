# CYBORG Discord Username Checker

A Python terminal project for studying asynchronous HTTP requests, username generation, response parsing, and basic progress tracking. The existing implementation attempts to check Discord username availability and can send results to a configured webhook.

**Educational and research use only.** This project uses a Discord user-account endpoint rather than a supported bot workflow. Automating normal user accounts in this way is prohibited by Discord's [Automated User Accounts policy](https://support.discord.com/hc/en-us/articles/115002192352-Automated-User-Accounts-Self-Bots) and can result in account termination. An educational purpose does not create an exception or authorize access. Prefer offline study and mocked responses; do not run live checks without explicit permission from Discord covering the activity.

This project is independent and is not affiliated with, endorsed by, or supported by Discord. Read [DISCLAIMER.md](DISCLAIMER.md) before using the network features.

## What the code includes

- Random, pattern-based, and wordlist-based username generation.
- Asynchronous requests with configurable concurrency, delay, timeout, and retries.
- Response classification for available, taken, invalid, and failed checks.
- Terminal statistics and a session summary.
- Local result output and checkpoint storage.
- Optional webhook notifications.
- Credential and proxy handling, including menu actions for checking them.

These describe the implementation, not a guarantee that Discord currently accepts its requests. The project does not claim or reserve usernames.

## Requirements

- Python 3.10 or newer is recommended.
- `pip` and a terminal with UTF-8 support.
- Windows for the optional `run.bat` launcher. The Python entry point also contains paths for other operating systems, but cross-platform behavior has not been verified.

Dependencies are listed in [requirements.txt](requirements.txt). Versions are currently unpinned, so installs may differ over time.

## Installation

Download the repository, open a terminal in its root directory, and create a virtual environment.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Linux or macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Offline example

After installing dependencies, generate a small sample without making network requests:

```powershell
.\.venv\Scripts\python.exe -c "from utils.generator import UsernameGenerator; print(UsernameGenerator(length=4, mode='pattern', pattern='a1a1').generate(5))"
```

On Linux or macOS, substitute `.venv/bin/python` for the Python executable above. This example generates candidates locally; it does not check availability. There is no built-in offline checker or dry-run mode.

For educational experiments with the request code, replace network interactions with local mocks. Do not use real credentials in fixtures or tests.

## Terminal interface

Start the interface with the virtual environment's Python executable:

```powershell
.\.venv\Scripts\python.exe main.py
```

Opening the menu creates `input/config.json`, `input/tokens.txt`, and `input/proxies.txt` if missing. The menu offers:

| Option | Action | Network access |
| --- | --- | --- |
| 1 | Start Username Checker | Sends requests to Discord; may send webhook notifications |
| 2 | Configure Settings | None |
| 3 | Validate Tokens | Sends requests to Discord |
| 4 | Test Proxies | Sends requests to Discord through listed proxies |
| 5 | Pattern Builder | None |
| 6 | Exit | None |

Options 1, 3, and 4 are live network actions. Do not select them for offline study. When validation or proxy testing finds successful entries, it overwrites the corresponding input file with those entries. Token validation prints portions of credentials, and proxy testing prints successful proxy entries; avoid sharing terminal output.

`run.bat` installs dependencies using the `pip` on your PATH and launches `python main.py`. The explicit virtual-environment commands above make the interpreter choice clearer.

## Configuration

[input/config.example.json](input/config.example.json) contains a credential-free example with reduced concurrency and a small candidate count. It is not loaded automatically. Before the first launch, copy it to `input/config.json`, or edit the locally generated config through option 2. Do not overwrite an existing config unless you intend to replace its settings.

The table lists the defaults in `utils/config.py`; your local config may override them.

| Setting | Code default | Meaning |
| --- | --- | --- |
| `threads` | `120` | Maximum concurrent workers, not operating-system threads |
| `delay` | `0.1` | Per-worker delay in seconds, randomized by approximately 20% |
| `webhook` | `""` | Optional destination for available usernames and session statistics |
| `use_proxies` | `false` | Whether checking uses the proxy list |
| `timeout` | `10` | Request timeout in seconds |
| `username_length` | `4` | Candidate length in random mode |
| `username_count` | `1000` | Requested number of candidates |
| `charset` | `"letters+digits"` | Character set for random generation |
| `mode` | `"random"` | `random`, `pattern`, or `wordlist` |
| `pattern` | `"a1a1"` | Pattern used in pattern mode |
| `wordlist_file` | `"wordlist.txt"` | Wordlist path, relative to the working directory unless absolute |
| `rps_limit` | `0` | Stored setting; currently not enforced by the checker |
| `auto_save_interval` | `30` | Checkpoint interval in seconds; `0` disables periodic saves |
| `resume` | `false` | Whether to attempt loading an existing checkpoint |

The code defaults are not a recommended request rate or evidence of permission. A delay applies separately to workers and does not impose a global request limit. The example config also does not make live use compliant or automatically safe.

### Generation modes

Random mode supports `letters`, `digits`, `letters+digits`, `letters+digits+underscore`, `letters+digits+dot`, and `all`. An unrecognized charset string is treated as a literal character pool.

Pattern mode replaces each `a` with a random lowercase letter and each `1` with a random digit. Other characters are literal. For example, `a1a1` could produce `m7q2`. The pattern determines length independently of `username_length`.

Wordlist mode reads non-empty lines from `wordlist_file` and samples when the list exceeds `username_count`. It does not apply the random generator's validation or deduplication. [input/wordlist.example.txt](input/wordlist.example.txt) contains fictional local-study examples.

## Files and data handling

```text
main.py                    Terminal entry point and session workflow
ui.py                      Menus, pattern preview, and statistics display
run.bat                    Windows dependency-installation and launch helper
requirements.txt           Python dependencies
input/config.example.json  Public configuration example without secrets
input/wordlist.example.txt  Public example candidate list
input/config.json          Private local configuration
input/tokens.txt           Private authentication material, if supplied
input/proxies.txt          Private proxy settings, if supplied
utils/config.py            Configuration loading and saving
utils/generator.py         Candidate generation
utils/checker.py           Request handling and result output
utils/stats.py             Counters and checkpoints
utils/webhook.py           Optional outbound notifications
utils/logger.py            Terminal logging
available.txt              Appended results from live checks
checkpoint.json            Saved statistics and candidate list
```

Authentication material, webhook URLs, and proxy credentials are stored as plaintext when configured. Requests send authentication material to Discord; configured proxies carry checker traffic. Webhook notifications send available usernames, timestamps, and session statistics to the configured destination. Treat those destinations and local files accordingly.

The included [.gitignore](.gitignore) excludes local configuration, credentials, private wordlists, results, checkpoints, logs, virtual environments, and Python caches. It does not remove files already tracked by Git or protect files uploaded manually. Inspect the staged files and repository history before publishing. See [SECURITY.md](SECURITY.md).

## Known limitations

- The account endpoint and response assumptions may change without notice. Availability results are not guarantees that a name can be claimed.
- `rps_limit` is not implemented. Concurrency and retries can produce substantial traffic.
- Random and pattern generation can loop indefinitely if the requested count exceeds the number of valid unique combinations, or if no valid candidate can be generated.
- Checkpoint resume is incomplete: periodic saves include the full candidate list, and completed checks are not consistently tracked for interruption saves. Resuming may repeat checks; interruption recovery is not guaranteed.
- SOCKS-style proxy strings are recognized, but the request code does not configure a SOCKS connector. Do not assume SOCKS support works.
- Invalid candidates contribute to the error counter. Wordlists are not normalized or validated before requests.
- Token validation uses response heuristics and should not be treated as a definitive credential validity check.
- Webhook delivery is best effort; pending notifications are not guaranteed to drain before shutdown.
- There is no automated test suite included, and live service compatibility is not verified by this documentation.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). Useful improvements include offline fixtures, enforced rate controls, bounded generation, checkpoint correctness, and credential-safe logging.

