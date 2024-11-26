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
        tree = read_tree(sys.argv[3])
        if sys.argv[2] == "--name-only":
            for entry in tree:
                print(f"{entry['name']}")
        else:
            for entry in tree:
                print(f"Mode: {entry['mode']}, Name: {entry['name']}, SHA1: {entry['sha1']}")
    elif command == "write-tree":
        tree_hash = recursive_tree_hash_generation("./")
        print(tree_hash)
    else:
        raise RuntimeError(f"Unknown command #{command}")

def initialize_git_directory():
    os.makedirs(".git/objects", exist_ok=True)
    os.makedirs(".git/refs", exist_ok=True)
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized git directory")

def cat_file_handler():
    for root, dirs, files in os.walk(directory_objects_path):
        for file in files:
            file_path = os.path.join(root, file)
        
            with open(file_path, "rb") as f:
                compressed_content = f.read()

                content = zlib.decompress(compressed_content)
                result = content.decode("utf-8").split("\x00")
                output.write(result[1])

def hash_object_handler(content_path):
    uncompressed_content = create_blob(content_path)
    hash_object(uncompressed_content, "blob")

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

def create_blob(blob_path):
    with open(blob_path, "rb") as f:
        blob_content = f.read()
    header = f"blob {len(blob_content)}\0".encode("utf-8")
    blob = header + blob_content
    return blob  # Return the complete blob data
        

def recursive_tree_hash_generation(start_path):
    tree_entries = []
    
    for entry in sorted(os.listdir(start_path)):
        entry_path = os.path.join(start_path, entry)
        if entry_path == "./.git":
            continue

        if os.path.isfile(entry_path):
            # Create a blob for the file
            uncompressed_blob = create_blob(entry_path)
            sha1 = hash_object(uncompressed_blob, "blob")
            mode = f"{REGULAR_FILE:o}"
        elif os.path.isdir(entry_path):
            # Recurse into the directory
            sha1 = recursive_tree_hash_generation(entry_path)
            mode = f"{DIRECTORY:o}"
        else:
            continue  # Skip unsupported entries

        # Add the entry to the tree
        tree_entry = f"{mode} {entry}\0".encode() + bytes.fromhex(sha1)
        tree_entries.append(tree_entry)
    
    # Combine all entries to create the tree object
    tree_data = b"".join(tree_entries)
    return hash_object(tree_data, "tree")
    
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
