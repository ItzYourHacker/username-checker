import asyncio
import sys
import os
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from utils.config import Config, INPUT_DIR
from utils.generator import UsernameGenerator
from utils.checker import UsernameChecker
from utils.webhook import WebhookSender
from utils.stats import Stats
from utils.logger import logger
from ui import (
    show_banner, show_menu, show_config_menu, inp,
    show_stats_block, show_summary, show_pattern_builder,
    show_separator, TitleUpdater,
)


async def handle_result(result: dict, webhook: WebhookSender, checker: UsernameChecker):
    username = result["username"]
    status = result["status"]

    if status == "available":
        logger.success(f"AVAILABLE  {username}")
        await checker.save_available(username)
        await webhook.send(username)
    elif status == "taken":
        logger.info(f"TAKEN      {username}")
    elif status == "invalid":
        pass
    elif status == "error":
        detail = str(result.get("code", result.get("detail", "")))
        logger.error(f"ERROR      {username} ({detail})")


async def run_checker(config: Config):
    checker = UsernameChecker(config)
    webhook = WebhookSender(config.webhook)

    await checker.start()
    await webhook.start()

    if config.resume:
        resumed_stats, remaining = Stats.load_checkpoint()
        if resumed_stats and remaining:
            logger.info(f"Resuming from checkpoint with {len(remaining)} usernames remaining")
            checker.stats = resumed_stats
            checker.stats.start_time = time.time()
            usernames = remaining
        else:
            usernames = _generate_usernames(config)
    else:
        usernames = _generate_usernames(config)

    if not usernames:
        logger.warning("No usernames generated")
        await checker.stop()
        await webhook.stop()
        return

    total = len(usernames)
    show_separator()
    logger.info(f"Generated {total} usernames")
    logger.info(f"Concurrency: {config.threads} | Delay: {config.delay}s | Proxies: {'On' if config.use_proxies else 'Off'}")
    logger.info(f"Tokens loaded: {len(config.tokens)} | Proxies loaded: {len(config.proxies)}")
    show_separator()
    print()

    title_updater = TitleUpdater(checker.stats)
    title_updater.start()

    async def on_result(result):
        await handle_result(result, webhook, checker)

    checker.on_result(on_result)

    auto_save_task = None
    if config.auto_save_interval > 0:
        auto_save_task = asyncio.create_task(
            _auto_save_loop(checker, usernames, config.auto_save_interval)
        )

    dashboard_task = asyncio.create_task(
        _dashboard_loop(checker, total, config)
    )

    try:
        await checker.check_batch(usernames)
    except KeyboardInterrupt:
        checker.request_stop()
        logger.warning("Interrupted! Saving checkpoint...")
        remaining = [u for u in usernames if u not in {r["username"] for r in checker._results}]
        checker.stats.save_checkpoint(remaining)
    finally:
        if auto_save_task:
            auto_save_task.cancel()
        dashboard_task.cancel()
        title_updater.stop()

        try:
            await dashboard_task
        except asyncio.CancelledError:
            pass

    stats_dict = checker.stats.to_dict()
    show_summary(stats_dict, total)

    await webhook.send_summary(stats_dict)
    await webhook.stop()
    await checker.stop()


async def _dashboard_loop(checker: UsernameChecker, total: int, config: Config):
    try:
        while True:
            await asyncio.sleep(2)
            stats_dict = checker.stats.to_dict()
            show_stats_block(stats_dict, total)
    except asyncio.CancelledError:
        pass


async def _auto_save_loop(checker: UsernameChecker, usernames: list, interval: int):
    try:
        while True:
            await asyncio.sleep(interval)
            checker.stats.save_checkpoint(usernames)
    except asyncio.CancelledError:
        pass


def _generate_usernames(config: Config) -> list:
    gen = UsernameGenerator(
        length=config.username_length,
        charset=config.charset,
        mode=config.mode,
        pattern=config.pattern,
        wordlist_file=config.wordlist_file,
    )
    return gen.generate(config.username_count)


async def validate_tokens(config: Config):
    checker = UsernameChecker(config)
    await checker.start()

    logger.info(f"Validating {len(config._tokens)} tokens...")
    valid = await checker.validate_tokens()
    logger.info(f"Valid tokens: {len(valid)} / {len(config._tokens)}")

    for t in valid:
        masked = t[:20] + "..." + t[-10:]
        logger.success(f"Valid: {masked}")

    if valid:
        tokens_path = os.path.join(INPUT_DIR, "tokens.txt")
        with open(tokens_path, "w") as f:
            f.write("\n".join(valid))
        logger.info("Updated input/tokens.txt with valid tokens only")

    await checker.stop()


async def test_proxies(config: Config):
    checker = UsernameChecker(config)
    await checker.start()

    logger.info(f"Testing {len(config._proxies)} proxies...")
    working = await checker.test_proxies()
    logger.info(f"Working proxies: {len(working)} / {len(config._proxies)}")

    for p in working:
        logger.success(f"Working: {p}")

    if working:
        proxies_path = os.path.join(INPUT_DIR, "proxies.txt")
        with open(proxies_path, "w") as f:
            f.write("\n".join(working))
        logger.info("Updated input/proxies.txt with working proxies only")

    await checker.stop()


async def main():
    config = Config.load()

    while True:
        show_banner()
        show_menu()
        choice = inp("Choice")

        if choice == "1":
            print()
            await run_checker(config)
            inp("Press Enter to continue")
        elif choice == "2":
            show_config_menu(config)
            config = Config.load()
        elif choice == "3":
            print()
            await validate_tokens(config)
            inp("Press Enter to continue")
        elif choice == "4":
            print()
            await test_proxies(config)
            inp("Press Enter to continue")
        elif choice == "5":
            show_pattern_builder()
            inp("Press Enter to continue")
        elif choice == "6":
            logger.info("Goodbye!")
            break
        else:
            logger.warning("Invalid option")
            await asyncio.sleep(1)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
