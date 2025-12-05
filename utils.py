
####
###
### Support file for utility functions, i want a really clean main python file.
###
####

'''
Mi serve:

funzione per hash

funzione per avere tutti i file data una cartella

funzione per formattare e salvare i percorsi dei file duplicati




'''



import hashlib #im using hashlib instead of plain hash() just because i can
import os

def get_hash(file_path):
    """ Generate SHA256 hash of a file's contents. """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk) #With update we can process chunks of data instead of loading big file all at once
    return sha256.hexdigest()


def get_all_files(directory):
    """ Get a list of all file paths in the given directory and its subdirectories. """
    try:
        file_paths = os.listdir(directory)
        absolute_file_paths = [os.path.join(directory, f) for f in file_paths if os.path.isfile(os.path.join(directory, f))]
    except:
        raise ValueError(f"Error accessing directory {directory}, make sure it exists and is accessible.")
    
    return absolute_file_paths

def get_dict_of_hashes(file_paths):
    """ Given a list of file paths, return a dictionary with file hashes as keys and lists of file paths as values. """
    dict_of_hashes = {}
    for file_path in file_paths:
        file_hash = get_hash(file_path)
        if file_hash in dict_of_hashes:
            dict_of_hashes[file_hash].append(file_path)
        else:
            dict_of_hashes[file_hash] = [file_path]
    return dict_of_hashes

def find_duplicates(dict_of_hashes):
    """Given a dictionary of file hashes, return only the duplicates. Expects a dict with hash as key and list of file paths as values."""
    duplicates = {hash_value: paths for hash_value, paths in dict_of_hashes.items() if len(paths) > 1}
    return duplicates


def save_duplicates_to_file(duplicates_dict):
    """ Save the duplicates dictionary to a text file in a readable format. """
    with open('duplicates.txt', 'w') as f:
        f.write("Hash is a unique identifier for the files, below it are the paths of duplicate files:\n")
        f.write("Duplicate Files Found:\n")
        for hash_value, paths in duplicates_dict.items():
            f.write(f"Hash: {hash_value}\n")
            for path in paths:
                f.write(f"    {path}\n")
            f.write("\n")


# Extensions that can be helded by tkinter
GOOD_EXTENSIONS = {
    # text
    '.txt',
    '.md',
    '.csv',
    '.json',
    '.xml',
    '.log',
    '.py',
    '.ini', 
    '.conf',

    # Img 
    '.png',
    '.jpg',
    '.jpeg',
    '.gif',
    '.bmp',
    '.ico',
    '.webp',
}

def is_extension_good_to_open(file_path):
    """ Check if the file extension is in the predefined set of good extensions. """
    _, ext = os.path.splitext(file_path)
    return ext.lower() in GOOD_EXTENSIONS

    
def filter_files_by_extension():
    """ Filter the duplicates list to include only files with good extensions. """
    with open('duplicates.txt', 'r') as f:
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