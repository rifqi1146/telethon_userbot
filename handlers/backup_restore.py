import json
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from telethon import events


DATA_DIR = Path("data")
TZ = ZoneInfo("Asia/Jakarta")


def _get_topic_reply_id(event):
    try:
        reply = getattr(event.message, "reply_to", None)
        if reply:
            return getattr(reply, "reply_to_top_id", None)
    except Exception:
        pass
    return None


def _backup_filename() -> str:
    now = datetime.now(TZ)
    return f"userbot_backup_{now.day:02d}-{now.month}-{now.year}.zip"


def _zip_data_folder(zip_path: Path) -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    count = 0

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(DATA_DIR.rglob("*")):
            if path.is_dir():
                continue
            zf.write(path, arcname=path.as_posix())
            count += 1

        if count == 0:
            zf.writestr(
                "data/.backup_meta.json",
                json.dumps({"note": "empty data backup"}, indent=2)
            )

    return count


def _safe_extract_zip(zip_path: Path, dest_dir: Path):
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise RuntimeError(f"Unsafe archive entry: {member.filename}")
        zf.extractall(dest_dir)


def _find_extracted_data_root(base_dir: Path) -> Path:
    direct = base_dir / "data"
    if direct.exists() and direct.is_dir():
        return direct

    entries = list(base_dir.iterdir())
    if entries and all(x.is_file() for x in entries):
        return base_dir

    raise RuntimeError("Archive does not contain a valid data folder")


def _reload_runtime_state():
    reloaded = []

    try:
        from handlers import dm_protect as dm_protect_module

        fresh_approved = dm_protect_module._load_approved()
        dm_protect_module.approved_users.clear()
        dm_protect_module.approved_users.update(fresh_approved)
        dm_protect_module.dm_spam_counter.clear()
        reloaded.append("dm_protect")
    except Exception:
        pass

    try:
        from handlers import ai as ai_module

        fresh_modes = ai_module._load_json(ai_module.AI_MODE_FILE, {})
        ai_module.AI_MODE.clear()
        ai_module.AI_MODE.update(fresh_modes)
        reloaded.append("ai")
    except Exception:
        pass

    return reloaded


def register(kiyoshi):

    @kiyoshi.on(events.NewMessage(pattern=r"^[./]backup$", outgoing=True))
    async def backup_handler(event):
        topic_id = _get_topic_reply_id(event)
        status = await event.edit("Creating data backup...")

        try:
            with tempfile.TemporaryDirectory(prefix="userbot_backup_") as tmpdir:
                zip_name = _backup_filename()
                zip_path = Path(tmpdir) / zip_name
                file_count = _zip_data_folder(zip_path)

                await kiyoshi.send_file(
                    event.chat_id,
                    str(zip_path),
                    caption=(
                        "**Data backup created**\n"
                        f"File: `{zip_name}`\n"
                        f"Files: `{file_count}`"
                    ),
                    force_document=True,
                    reply_to=topic_id,
                )

            await status.delete()
        except Exception as e:
            await status.edit(f"Failed to create backup.\nError: {e}")

    @kiyoshi.on(events.NewMessage(pattern=r"^[./]restore$", outgoing=True))
    async def restore_handler(event):
        if not event.is_reply:
            return await event.edit("Reply to a backup zip file first.")

        reply = await event.get_reply_message()
        if not reply or not reply.file:
            return await event.edit("Reply to a valid backup zip file first.")

        topic_id = _get_topic_reply_id(event)
        name = (getattr(reply.file, "name", "") or "").lower()
        mime = (getattr(reply.file, "mime_type", "") or "").lower()

        if not name.endswith(".zip") and "zip" not in mime:
            return await event.edit("Backup file must be a .zip archive.")

        status = await event.edit("Restoring data backup...")
        rollback_dir = None

        try:
            with tempfile.TemporaryDirectory(prefix="userbot_restore_") as tmpdir:
                tmpdir_path = Path(tmpdir)
                zip_path = tmpdir_path / "backup.zip"
                extract_dir = tmpdir_path / "extract"
                extract_dir.mkdir(parents=True, exist_ok=True)

                downloaded = await kiyoshi.download_media(reply, file=str(zip_path))
                if not downloaded or not zip_path.exists():
                    return await status.edit("Failed to download backup archive.")

                if not zipfile.is_zipfile(zip_path):
                    return await status.edit("Invalid backup archive.")

                _safe_extract_zip(zip_path, extract_dir)
                extracted_data_root = _find_extracted_data_root(extract_dir)

                rollback_dir = Path(tempfile.mkdtemp(prefix="userbot_data_rollback_"))
                rollback_data = rollback_dir / "data"

                if DATA_DIR.exists():
                    shutil.copytree(DATA_DIR, rollback_data, dirs_exist_ok=True)
                    shutil.rmtree(DATA_DIR)

                shutil.copytree(extracted_data_root, DATA_DIR, dirs_exist_ok=True)

                reloaded = _reload_runtime_state()
                reloaded_text = ", ".join(reloaded) if reloaded else "none"

                await status.edit(
                    "**Data restored successfully**\n"
                    f"Reloaded runtime: `{reloaded_text}`"
                )

        except Exception as e:
            try:
                if rollback_dir and (rollback_dir / "data").exists():
                    if DATA_DIR.exists():
                        shutil.rmtree(DATA_DIR)
                    shutil.copytree(rollback_dir / "data", DATA_DIR, dirs_exist_ok=True)
                    _reload_runtime_state()
            except Exception:
                pass

            await status.edit(f"Failed to restore backup.\nError: {e}")

        finally:
            try:
                if rollback_dir and rollback_dir.exists():
                    shutil.rmtree(rollback_dir, ignore_errors=True)
            except Exception:
                pass