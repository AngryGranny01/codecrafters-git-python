import hashlib
import sys
import os
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
        handle_ls_tree()
    elif command == "write-tree":
        tree_hash = write_tree(".")
        print(tree_hash)
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
    uncompressed_blob = create_blob(content_path)
    hash_object(uncompressed_blob, "blob")


# Handles the 'ls-tree' command to list the contents of a tree object.
def handle_ls_tree():
    """Handles the 'ls-tree' command to list the contents of a tree object."""
    tree_hash = sys.argv[2]
    tree = read_tree(tree_hash)
    if "--name-only" in sys.argv:
        for entry in tree:
            print(entry["name"])
    else:
        for entry in tree:
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
    header = f"blob {len(blob_content)}\0".encode()
    return header + blob_content
        
# Recursively writes a tree object and returns its SHA1 hash.
def write_tree(path):
    if os.path.isfile(path):
        return hash_object(create_blob(path), "blob")
    
    tree_entries = []

    # Process directory contents, sorting files before directories
    for entry in sorted(os.listdir(path)):
        if entry == ".git":  # Skip .git directory
            continue
        full_path = os.path.join(path, entry)
        
        if os.path.isfile(full_path):
            mode = f"{REGULAR_FILE:o}"  # File mode
            sha1 = write_tree(full_path)  # Create blob and get its SHA1
        elif os.path.isdir(full_path):
            mode = f"{DIRECTORY:o}"  # Directory mode
            sha1 = write_tree(full_path)  # Recursively process directory
        else:
            continue  # Skip unsupported entries
        
        # Create a tree entry: "<mode> <filename>\0<binary SHA1>"
        entry_data = f"{mode} {entry}\0".encode() + bytes.fromhex(sha1)
        tree_entries.append(entry_data)
    
    # Combine all entries into the tree object
    tree_data = b"".join(tree_entries)
    tree_object = f"tree {len(tree_data)}\0".encode() + tree_data
    
    # Hash and store the tree object
    return hash_object(tree_object, "tree")

# Hashes and stores a Git object.
def hash_object(data, obj_type):
    header = f"{obj_type} {len(data)}\0".encode()
    full_data = header + data
    sha1_hash = hashlib.sha1(full_data).hexdigest()
    object_dir = os.path.join(directory_objects_path, sha1_hash[:2])
    os.makedirs(object_dir, exist_ok=True)
    object_path = os.path.join(object_dir, sha1_hash[2:])
    if not os.path.exists(object_path):
        with open(object_path, "wb") as f:
            f.write(zlib.compress(full_data))
    return sha1_hash

if __name__ == "__main__":
    main()
