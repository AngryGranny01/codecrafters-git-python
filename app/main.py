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
        write_tree_handler(".")
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
    sha1_hash = hashlib.sha1(uncompressed_content).hexdigest()
    print(sha1_hash)
    store_object(sha1_hash, uncompressed_content)

def read_tree(content_path):
    git_object_path = os.path.join(directory_objects_path, content_path[:2], content_path[2:])
    with open(git_object_path, "rb") as f:
        compressed_data = f.read()
    decompressed_tree = zlib.decompress(compressed_data)
    null_byte_index = decompressed_tree.index(b'\0')
    tree_header = decompressed_tree[:null_byte_index]
    tree_body = decompressed_tree[null_byte_index + 1:]
    object_type, object_size = tree_header.decode().split()
    entries = []
    parse_tree_body(tree_body, entries)
    entries.sort(key=lambda entry: entry['name'])
    return entries

def parse_tree_body(tree_body, entries):
    while tree_body:
        mode_end = tree_body.index(b' ')
        file_mode = tree_body[:mode_end].decode()
        tree_body = tree_body[mode_end + 1:]
        name_end = tree_body.index(b'\0')
        file_name = tree_body[:name_end].decode()
        tree_body = tree_body[name_end + 1:]
        sha1_hash = tree_body[:20].hex()
        tree_body = tree_body[20:]
        entries.append({"mode": file_mode, "name": file_name, "sha1": sha1_hash})

def write_tree_handler(directory):
    tree_sha1 = create_tree(directory)
    return tree_sha1

def create_blob(file_path):
    with open(file_path, "rb") as f:
        content = f.read()
    header = f"blob {len(content)}\0".encode()
    return header + content

def store_object(sha1_hash, data):
    object_dir = os.path.join(directory_objects_path, sha1_hash[:2])
    os.makedirs(object_dir, exist_ok=True)
    object_path = os.path.join(object_dir, sha1_hash[2:])
    if not os.path.exists(object_path):
        with open(object_path, 'wb') as f:
            f.write(zlib.compress(data))

def create_tree(directory):
    entries = []
    print(directory)
    for entry in sorted(os.listdir(directory)):
        if entry == ".git":
            continue
        entry_path = os.path.join(directory, entry)
        if os.path.isfile(entry_path):
            blob_data = create_blob(entry_path)
            sha1 = hashlib.sha1(blob_data).hexdigest()
            store_object(sha1, blob_data)
            mode = f"{REGULAR_FILE:06o}"
        elif os.path.isdir(entry_path):
            sha1 = create_tree(entry_path)
            mode = f"{DIRECTORY:06o}"
        else:
            continue
        entries.append(f"{mode} {entry}\0".encode() + bytes.fromhex(sha1))
    tree_data = b"".join(entries)
    tree_header = f"tree {len(tree_data)}\0".encode()
    tree_object = tree_header + tree_data
    tree_sha1 = hashlib.sha1(tree_object).hexdigest()
    print(tree_sha1)
    store_object(tree_sha1, tree_object)
    return tree_sha1