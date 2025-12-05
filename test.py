####
###
### File generator for testing purposes
###
####



import os
from utils import get_dict_of_hashes, find_duplicates, save_duplicates_to_file, get_all_files
import time

def gen_file(test_path,filename, content):
    cwd = os.getcwd()
    full_file_path = os.path.join(cwd, test_path, filename)
    with open(full_file_path, 'w') as f:
        f.write(content)
    print(f"File '{filename}' generated.")

def argparse_args():
    import argparse

    parser = argparse.ArgumentParser(description="Generate test files.")
    parser.add_argument(
        '--num-files',
        type=int,
        default=10,
        help='Number of test files to generate (default: 5)'
    )
    parser.add_argument(
        '--content',
        type=str,
        default='Sample content for testing.',
        help='Content to write into each test file (default: "Sample content for testing.")'
    )
    parser.add_argument( 
        '--repetions',
        type=int,
        default=2,
        help='Number of times to repeat the content in each file (default: 1) for testing purposes'
    )
    parser.add_argument(
        "--test_dir",
        type=str,
        default="test_files",
        help="Directory to store generated test files (default: 'test_files'), must be a subdirectory of the current working directory."
    )
    return parser.parse_args()

def main():
    args = argparse_args()
    ## Validation
    if args.repetions > args.num_files:
        raise ValueError("Number of repetitions cannot be greater than number of files.")
    if args.repetions < 1:
        raise ValueError("Number of repetitions must be at least 1.")
    if args.num_files < 1:
        raise ValueError("Number of files must be at least 1.")
    

    os.makedirs('test_files', exist_ok=True)
    test_path = args.test_dir
    print(f"Generating {args.num_files} test files in directory: {test_path}")
    benchmark_start = time.time()
    
    number_of_unique_files = args.num_files // args.repetions # example: 10 files, 2 repetitions -> 5 unique files, each repeated twice

    for i in range(number_of_unique_files):
        for j in range(args.repetions):
            filename = f"test_file_{i * args.repetions + j + 1}.txt"
            content = args.content + "\nindex: " + str(i)
            gen_file(test_path, filename, content)
    print("File generation completed.\n")
    print("Now testing the utils functions on the generated files...\n")


    benchmark_for_retriving_files_start = time.time()
    file_paths = get_all_files(test_path)
    benchmark_for_retriving_files_end = time.time()
    print(f"Total files founded: {len(file_paths)}\n")
    benchmark_for_getting_hashes_start = time.time()
    dict_of_hashes = get_dict_of_hashes(file_paths)
    benchmark_for_getting_hashes_end = time.time()
    print(f"Total unique files (by hash): {len(dict_of_hashes)}\n")
    benchmark_for_getting_duplicates_start = time.time()
    duplicates = find_duplicates(dict_of_hashes)
    benchmark_for_getting_duplicates_end = time.time()
    print(f"Total duplicates found: {len(duplicates)}\n")
    save_duplicates_to_file(duplicates)
    print("Duplicates saved to 'duplicates.txt'.")

    
    benchmark_end = time.time()
    print(f"Benchmark time for {args.num_files} files: {benchmark_end - benchmark_start:.2f} seconds.")
    print(f"Breakdown: \n - Retrieving files: {benchmark_for_retriving_files_end - benchmark_for_retriving_files_start:.2f} seconds.\n - Getting hashes: {benchmark_for_getting_hashes_end - benchmark_for_getting_hashes_start:.2f} seconds.\n - Finding duplicates: {benchmark_for_getting_duplicates_end - benchmark_for_getting_duplicates_start:.2f} seconds.\n")

if __name__ == "__main__":
    main()
# test.py
    