"""Background scheduler for auto-importing interest rate data from Excel."""

from pathlib import Path
import shutil
import tempfile
import time

from apscheduler.schedulers.background import BackgroundScheduler

from import_rates_excel import (
    DEFAULT_RATE_EXCEL_PATH,
    import_rate_rows,
    read_rates_excel,
)


RATE_EXCEL_PATH = DEFAULT_RATE_EXCEL_PATH
CHECK_INTERVAL_MINUTES = 1
FILE_STABLE_SECONDS = 10

_scheduler = None
_last_modified_time = None


def rate_excel_lock_path():
    return RATE_EXCEL_PATH.with_name(f"~${RATE_EXCEL_PATH.name}")


def rate_excel_is_ready(modified_time):
    if rate_excel_lock_path().exists():
        return False

    return time.time() - modified_time >= FILE_STABLE_SECONDS


def read_rate_rows_from_temporary_copy():
    with tempfile.TemporaryDirectory(prefix="ebl_rate_excel_") as temp_dir:
        copy_path = Path(temp_dir) / RATE_EXCEL_PATH.name
        shutil.copy2(RATE_EXCEL_PATH, copy_path)
        return read_rates_excel(copy_path)


def sync_rates_from_excel_if_changed():
    """Import rates when the Excel file has been saved after last sync."""
    global _last_modified_time

    if not RATE_EXCEL_PATH.exists():
        print(f"Rate Excel scheduler skipped. File not found: {RATE_EXCEL_PATH}")
        return

    modified_time = RATE_EXCEL_PATH.stat().st_mtime

    if _last_modified_time == modified_time:
        return

    if not rate_excel_is_ready(modified_time):
        return

    try:
        deposit_rows, lending_rows = read_rate_rows_from_temporary_copy()
        inserted = import_rate_rows(deposit_rows, lending_rows)
        _last_modified_time = modified_time
        print(
            "Rate Excel scheduler imported "
            f"{inserted['deposit']} deposit rows and "
            f"{inserted['lending']} lending rows from {RATE_EXCEL_PATH.name}."
        )

    except Exception as error:
        print(f"Rate Excel scheduler import failed: {error}")


def start_rate_excel_scheduler():
    """Start the background job once when FastAPI starts."""
    global _scheduler

    if _scheduler is not None:
        return

    sync_rates_from_excel_if_changed()

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        sync_rates_from_excel_if_changed,
        "interval",
        minutes=CHECK_INTERVAL_MINUTES,
        id="rate_excel_sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    print(
        "Rate Excel scheduler started. "
        f"It will check every {CHECK_INTERVAL_MINUTES} minute(s)."
    )
