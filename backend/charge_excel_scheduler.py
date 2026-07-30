"""Background scheduler for auto-importing charge data from Excel."""

from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

from import_charges_excel import import_charge_rows, read_charge_excel


CHARGE_EXCEL_PATH = (
    Path(__file__).resolve().parent
    / "charge_data"
    / "EBL_charges_update_template.xlsx"
)
CHECK_INTERVAL_MINUTES = 1

_scheduler = None
_last_modified_time = None


def sync_charges_from_excel_if_changed():
    """Import charges when the Excel file has been saved after last sync."""
    global _last_modified_time

    if not CHARGE_EXCEL_PATH.exists():
        print(f"Charge Excel scheduler skipped. File not found: {CHARGE_EXCEL_PATH}")
        return

    modified_time = CHARGE_EXCEL_PATH.stat().st_mtime

    if _last_modified_time == modified_time:
        return

    try:
        rows = read_charge_excel(CHARGE_EXCEL_PATH)
        inserted = import_charge_rows(rows)
        _last_modified_time = modified_time
        print(
            "Charge Excel scheduler imported "
            f"{inserted} rows from {CHARGE_EXCEL_PATH.name}."
        )

    except Exception as error:
        print(f"Charge Excel scheduler import failed: {error}")


def start_charge_excel_scheduler():
    """Start the background job once when FastAPI starts."""
    global _scheduler

    if _scheduler is not None:
        return

    sync_charges_from_excel_if_changed()

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        sync_charges_from_excel_if_changed,
        "interval",
        minutes=CHECK_INTERVAL_MINUTES,
        id="charge_excel_sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    print(
        "Charge Excel scheduler started. "
        f"It will check every {CHECK_INTERVAL_MINUTES} minute(s)."
    )
