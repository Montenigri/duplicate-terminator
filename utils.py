
####
###
### Support file for utility functions, i want a really clean main python file.
###
####

import hashlib
import os

# Read sizes used by the scan pipeline (bytes)
CHUNK_SIZE = 256 * 1024
QUICK_HASH_SIZE = 64 * 1024


class ScanCancelled(Exception):
    """Raised by scan_for_duplicates when should_stop() returns True."""


def _hash_file(file_path, limit=None):
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            if limit is None:
                while chunk := f.read(CHUNK_SIZE):
                    sha256.update(chunk)
            else:
                sha256.update(f.read(limit))
    except OSError:
        return None
    return sha256.hexdigest()


def get_hash(file_path):
    """ Generate SHA256 hash of a file's contents, read in chunks. Returns None if the file cannot be read. """
    return _hash_file(file_path)


def get_quick_hash(file_path):
    """ SHA256 of the first QUICK_HASH_SIZE bytes of a file, used to cheaply discard files that cannot be duplicates. Returns None if the file cannot be read. """
    return _hash_file(file_path, QUICK_HASH_SIZE)


def get_all_files(directory, recursive=True):
    """ Get a list of all file paths in the given directory, and in its subdirectories when recursive is True. Symlinks are not followed. """
    file_paths = []

    def visit(entry):
        try:
            is_file = entry.is_file(follow_symlinks=False)
            is_dir = entry.is_dir(follow_symlinks=False)
        except OSError:
            return
        if is_file:
            file_paths.append(entry.path)
            return
        if recursive and is_dir:
            try:
                with os.scandir(entry.path) as sub_entries:
                    for sub_entry in sub_entries:
                        visit(sub_entry)
            except OSError:
                pass

    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                visit(entry)
    except OSError:
        raise ValueError(f"Error accessing directory {directory}, make sure it exists and is accessible.")

    return file_paths


def get_dict_of_hashes(file_paths):
    """ Given a list of file paths, return a dictionary with file hashes as keys and lists of file paths as values. Unreadable files are skipped. """
    dict_of_hashes = {}
    for file_path in file_paths:
        file_hash = get_hash(file_path)
        if file_hash is None:
            continue
        dict_of_hashes.setdefault(file_hash, []).append(file_path)
    return dict_of_hashes


def find_duplicates(dict_of_hashes):
    """Given a dictionary of file hashes, return only the duplicates. Expects a dict with hash as key and list of file paths as values."""
    duplicates = {hash_value: paths for hash_value, paths in dict_of_hashes.items() if len(paths) > 1}
    return duplicates


def scan_for_duplicates(directory, recursive=True, progress_callback=None, should_stop=None):
    """
    Optimized duplicate scan pipeline:
      1. list files (recursively when recursive is True)
      2. group files by size: files with a unique size cannot be duplicates
      3. hash the first QUICK_HASH_SIZE bytes of the remaining candidates only
      4. fully hash only files whose (size, quick hash) pair collides
    Returns {full_hash: [paths]} with groups sorted by file size, biggest first.
    progress_callback(stage, done, total, path) reports progress, with stage in
    ("list", "size", "quick", "full"). should_stop is a callable polled between
    files; when it returns True the scan raises ScanCancelled.
    """

    def report(stage, done, total, path=""):
        if progress_callback is not None:
            progress_callback(stage, done, total, path)

    def check_stop():
        if should_stop is not None and should_stop():
            raise ScanCancelled()

    # Stage 1: file listing
    file_paths = get_all_files(directory, recursive)
    total_files = len(file_paths)
    report("list", 0, total_files)

    # Stage 2: group by size, unique sizes can never be duplicates
    by_size = {}
    sizes = {}
    for index, path in enumerate(file_paths):
        check_stop()
        report("size", index + 1, total_files, path)
        try:
            size = os.path.getsize(path)
        except OSError:
            continue
        sizes[path] = size
        by_size.setdefault(size, []).append(path)

    candidate_groups = [paths for paths in by_size.values() if len(paths) > 1]
    candidate_groups.sort(key=lambda paths: -sizes[paths[0]])
    candidates_total = sum(len(group) for group in candidate_groups)

    def hash_stage(groups, hash_func, stage, total, group_key):
        grouped = {}
        done = 0
        for group in groups:
            for path in group:
                check_stop()
                file_hash = hash_func(path)
                done += 1
                report(stage, done, total, path)
                if file_hash is None:
                    continue
                grouped.setdefault(group_key(path, file_hash), []).append(path)
        return grouped

    # Stage 3: quick pre-hash of the candidates only
    by_quick = hash_stage(
        candidate_groups,
        get_quick_hash,
        "quick",
        candidates_total,
        lambda path, _hash: (sizes[path], _hash),
    )

    # Stage 4: full hash only where the (size, quick hash) pair collides
    colliding_groups = [group for group in by_quick.values() if len(group) > 1]
    hashed = hash_stage(
        colliding_groups,
        get_hash,
        "full",
        sum(len(group) for group in colliding_groups),
        lambda _path, file_hash: file_hash,
    )

    duplicates = {hash_value: sorted(paths) for hash_value, paths in hashed.items() if len(paths) > 1}
    duplicates = dict(sorted(duplicates.items(), key=lambda item: -sizes[item[1][0]]))
    return duplicates


def save_duplicates_to_file(duplicates_dict, output_path='duplicates.txt'):
    """ Save the duplicates dictionary to a text file in a readable format. """
    with open(output_path, 'w') as f:
        f.write("Hash is a unique identifier for the files, below it are the paths of duplicate files:\n")
        f.write("Duplicate Files Found:\n")
        for hash_value, paths in duplicates_dict.items():
            f.write(f"Hash: {hash_value}\n")
            for path in paths:
                f.write(f"    {path}\n")
            f.write("\n")


IMAGE_EXTENSIONS = {
    '.png',
    '.jpg',
    '.jpeg',
    '.gif',
    '.bmp',
    '.ico',
    '.webp',
}

TEXT_EXTENSIONS = {
    '.txt',
    '.md',
    '.csv',
    '.json',
    '.xml',
    '.log',
    '.py',
    '.ini',
    '.conf',
}

GOOD_EXTENSIONS = IMAGE_EXTENSIONS | TEXT_EXTENSIONS


def has_extension(file_path, extensions):
    """ Check if the file's lowercase extension is in the given set. """
    _, ext = os.path.splitext(file_path)
    return ext.lower() in extensions


def is_extension_good_to_open(file_path):
    """ Check if the file extension is in the predefined set of good extensions. """
    return has_extension(file_path, GOOD_EXTENSIONS)


def is_image(file_path):
    """ Check if the file has an extension that can be displayed as an image preview. """
    return has_extension(file_path, IMAGE_EXTENSIONS)


def is_text(file_path):
    """ Check if the file has an extension that can be previewed as text. """
    return has_extension(file_path, TEXT_EXTENSIONS)


def filter_files_by_extension(duplicates_path='duplicates.txt'):
    """ Filter the duplicates list to include only files with good extensions. """
    with open(duplicates_path, 'r') as f:
        lines = f.readlines()

    duplicates_dict = {}
    current_hash = None

    for line in lines:
        line = line.strip()
        if line.startswith('Hash: '):
            current_hash = line.replace('Hash: ', '')
            duplicates_dict[current_hash] = []
        elif line and current_hash and not line.startswith('Duplicate') and not line.startswith('Hash'):
            duplicates_dict[current_hash].append(line)

    filtered_duplicates = {
        hash_value: [path for path in paths if is_extension_good_to_open(path)]
        for hash_value, paths in duplicates_dict.items()
    }

    return {k: v for k, v in filtered_duplicates.items() if v}
