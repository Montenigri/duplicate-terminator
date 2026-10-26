# AGENTS.md

## Commands

- Run app: `python main.py` (customtkinter GUI; needs a display **and `tkinter`** — on Debian/Ubuntu `sudo apt install python3-tk`; system Python here lacks it)
- Install deps: `pip install -r requirements.txt` in a venv (system Python is externally managed / PEP 668)
- Generate fixtures + benchmark: `python test.py --num-files 20` (creates `test_files/` and `duplicates.txt`, both gitignored)
- No pytest tests, no lint/typecheck/CI config exist.

## Gotchas

- `test.py` is NOT a test suite: it's a fixture generator + benchmark. Verify changes by running the pipeline directly (`scan_for_duplicates`) and `test.py`.
- `duplicates.txt` is a data-exchange format: `save_duplicates_to_file()` writes it, `filter_files_by_extension()` re-parses it by text matching (`Hash: ` prefix, indented paths). No extra lines under a hash — any other line is parsed as a path. Changing the format breaks the comparison feature.
- Scans run on a daemon thread; the GUI is updated via a `queue.Queue` polled with `after()`. Never touch CTk widgets from worker threads.
- Cancellation: `scan_for_duplicates(should_stop=...)` raises `ScanCancelled`; the GUI catches it. Window close sets the same event.
- Unreadable files are skipped silently (`get_hash`/`get_quick_hash` return `None`), they never crash a scan.
- Preview whitelists live in `utils.py` (`IMAGE_EXTENSIONS` / `TEXT_EXTENSIONS`); the GUI preview depends on them. Non-whitelisted files show "Preview not available".

## Structure

Flat 3-file layout: `main.py` = GUI + thread/queue glue only (keep logic out), `utils.py` = all scan/hash logic, `test.py` = generator/benchmark script.

- `scan_for_duplicates()` is the 4-stage pipeline: list → group by size (unique size ⇒ no duplicate) → quick hash of first 64 KB → full SHA256 only on (size, quick) collisions. Groups sorted biggest-first; paths sorted within groups.
- Naive helpers `get_dict_of_hashes()` + `find_duplicates()` are kept only for compatibility/testing — don't use them in the main flow.
- `main.py` has an `if __name__ == "__main__"` guard, so importing it is safe.
