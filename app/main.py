import hashlib
import sys
import os
import time
import zlib

directory_objects_path = ".git/objects"
output = sys.stdout

REGULAR_FILE = 100644
EXEC_FILE = 100755
SYMBOLIC_LINK = 120000
DIRECTORY = 40000

def main():
    command = sys.argv[1]
    if command == "init":
        initialize_git_directory()
    elif command == "cat-file":
        cat_file_handler()
    elif command == "hash-object":
        hash_object_handler(sys.argv[3])
    elif command == "ls-tree":
        ls_tree_handler()
    elif command == "write-tree":
        tree_hash = write_tree(".")
        print(tree_hash)
    elif command == "commit-tree":
        handle_commit_tree()
    else:
        raise RuntimeError(f"Unknown command #{command}")

def initialize_git_directory():
    os.makedirs(".git/objects", exist_ok=True)
    os.makedirs(".git/refs", exist_ok=True)
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized git directory")

# Handles the 'cat-file' command to display content of a Git object.
def cat_file_handler():
    for root, dirs, files in os.walk(directory_objects_path):
        for file in files:
            file_path = os.path.join(root, file)
        
            with open(file_path, "rb") as f:
                compressed_content = f.read()

                content = zlib.decompress(compressed_content)
                result = content.decode("utf-8").split("\x00")
                output.write(result[1])

# Handles the 'hash-object' command to hash and store a file as a blob.
def hash_object_handler(content_path):
    uncompressed_content = create_blob(content_path)
    # Compute hash
    compressed_content = hashlib.sha1(uncompressed_content).hexdigest()
    write_object(compressed_content, uncompressed_content)
    print(compressed_content)


# Handles the 'ls-tree' command to list the contents of a tree object.
def ls_tree_handler():
    tree_hash = sys.argv[len(sys.argv)-1] 
    name_only = "--name-only" in sys.argv

    tree_entries = read_tree(tree_hash)
    for entry in tree_entries:
        if name_only:
            print(entry["name"])
        else:
            print(f"Mode: {entry['mode']}, Name: {entry['name']}, SHA1: {entry['sha1']}")

# Reads and parses a tree object.
def read_tree(content_path):
    # Construct the Git object path
    git_object_path = os.path.join(directory_objects_path, content_path[:2], content_path[2:])
    
    # Read the compressed Git object
    with open(git_object_path, "rb") as f:
        compressed_data = f.read()

    # Decompress the data
    decompressed_tree = zlib.decompress(compressed_data)
    null_byte_index = decompressed_tree.index(b'\0')

    # Parse the tree header
    tree_header = decompressed_tree[:null_byte_index]
    tree_body = decompressed_tree[null_byte_index + 1:]
    object_type, object_size = tree_header.decode().split()

    # Print the header of the tree
    # print(f"Object Type: {object_type}, Size: {object_size}")

    # Parse the tree body
    entries = []  # List to store parsed tree entries
    recursive_read_tree_body(tree_body, entries)

    # Sort entries after name
    entries.sort(key=lambda entry: entry['name'])

    return entries

def recursive_read_tree_body(tree_body, entries):
    if len(tree_body) <= 1:  # Stop recursion when the tree body is exhausted
        return

    # Extract the file mode
    mode_index = tree_body.index(b' ')
    file_mode = tree_body[:mode_index].decode()

    # Move forward to extract the file name
    tree_body = tree_body[mode_index + 1:]
    name_index = tree_body.index(b'\0')
    file_name = tree_body[:name_index].decode()

    # Move forward to extract the SHA-1 hash
    tree_body = tree_body[name_index + 1:]
    sha1_hash = tree_body[:20].hex()

    # Add the parsed entry to the list
    entries.append({"mode": file_mode, "name": file_name, "sha1": sha1_hash})

    # Recursively process the rest of the tree body
    recursive_read_tree_body(tree_body[20:], entries)

# Creates a blob object for a file.
def create_blob(file_path):
    with open(file_path, "rb") as f:
        blob_content = f.read()
    header = f"blob {len(blob_content)}\0".encode("utf-8")
    return header + blob_content

# Writes a Git object to the .git/objects directory.
def write_object(sha1, data):
    object_dir = os.path.join(directory_objects_path, sha1[:2])
    object_path = os.path.join(object_dir, sha1[2:])
    os.makedirs(object_dir, exist_ok=True)
    with open(object_path, "wb") as f:
        f.write(zlib.compress(data))


# Recursively writes a tree object and returns its SHA1 hash.
def write_tree(path ,write =True):
    if os.path.isfile(path):
        # For files, create a blob and return its SHA1 hash
        blob_data = create_blob(path)
        blob_sha1 = hashlib.sha1(blob_data).hexdigest()
        
        write_object(blob_sha1, blob_data)
        return blob_sha1

    # Accumulate tree entries
    tree_entries = b""

    # Sort directory contents (files before directories)
    for entry in sorted(os.listdir(path)):
        if entry == ".git":  # Skip the .git directory
            continue
        full_path = os.path.join(path, entry)

        # Determine the mode (100644 for files, 40000 for directories)
        if os.path.isfile(full_path):
            mode = "100644"
        elif os.path.isdir(full_path):
            mode = "40000"
        else:
            continue  # Skip unsupported entries

        # Recursively process the entry and get its SHA1 hash
        sha1 = write_tree(full_path)

        # Add the entry to the tree (mode, name, and SHA1 in binary form)
        tree_entries += f"{mode} {entry}\0".encode() + bytes.fromhex(sha1)

    # Create the tree object
    tree_header = f"tree {len(tree_entries)}\0".encode()
    tree_data = tree_header + tree_entries
    tree_sha1 = hashlib.sha1(tree_data).hexdigest()

    # Write the tree to the .git/objects directory
    write_object(tree_sha1, tree_data)
    return tree_sha1


# Handles the 'commit-tree' command to create a commit object.
def handle_commit_tree():
    if len(sys.argv) < 4 or sys.argv[3] != "-m":
        print("Usage: ./your_program.sh commit-tree <tree-hash> [-p <parent-hash>] -m <message>")
        return

    tree_sha = sys.argv[2]
    parent_sha = sys.argv[4] if len(sys.argv) > 5 and sys.argv[3] == "-p" else None
    message_index = 6 if parent_sha else 4
    commit_message = " ".join(sys.argv[message_index:])
    commit_sha = create_commit_tree(tree_sha, commit_message, parent_sha)
    print(commit_sha)

# Creates a commit object and writes it to the .git/objects directory.
def create_commit_tree(tree_sha, message, parent_sha=None, author="Author <author@example.com>", committer=None):
    committer = committer or author
    timestamp = int(time.time())
    timezone = time.strftime("%z")

    commit = f"tree {tree_sha}\n"
    if parent_sha:
        commit += f"parent {parent_sha}\n"
        commit += f"author {author} {timestamp} {timezone}\n"
        commit += f"committer {committer} {timestamp} {timezone}\n\n"
        commit += message + "\n"

    commit_object = f"commit {len(commit)}\0".encode() + commit.encode()
    sha1 = hashlib.sha1(commit_object).hexdigest()
    write_object(sha1, commit_object)
    return sha1


if __name__ == "__main__":
    main()
