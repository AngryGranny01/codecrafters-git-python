import hashlib
import sys
import os
import zlib

directory_objects_path = ".git/objects"
output = sys.stdout

REGULAR_FILE = 100644
EXEC_FILE = 100755
SYMBOLIC_LINK = 120000
DIRECTORIES = 40000

def main():
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    elif command == "cat-file":
        blub_read()
    elif command == "hash-object":
        blub_write(sys.argv[3])
    elif command == "ls-tree":
        read_tree(sys.argv[3])
    else:
        raise RuntimeError(f"Unknown command #{command}")


def blub_read():
    for root, dirs, files in os.walk(directory_objects_path):
        for file in files:
            file_path = os.path.join(root, file)
        
            with open(file_path, "rb") as f:
                compressed_content = f.read()

                content = zlib.decompress(compressed_content)
                result = content.decode("utf-8").split("\x00")
                output.write(result[1])

def blub_write(content_path):
    with open(content_path, "rt") as f:
        newcontent = f.read()
        uncompressed_content = b'blob ' + str(len(newcontent)).encode() + b'\x00' + bytes(newcontent, "utf-8")
        # Compute hash
        compressed_content = hashlib.sha1(uncompressed_content).hexdigest()
        print(compressed_content)
        if compressed_content:
            object_dir = os.path.join(directory_objects_path,compressed_content[0:2])
            # Ensure the parent directory exists
            os.makedirs(object_dir, exist_ok=True)

            blub_path=str(compressed_content[0:2])+'/'+str(compressed_content[2:])
            new_directory_path = os.path.join(directory_objects_path, blub_path) 
            if not os.path.exists(new_directory_path):
                with open(new_directory_path, 'wb') as f:
                    f.write(zlib.compress(uncompressed_content))

def read_tree(content_path):
    git_object_path = os.path.join(directory_objects_path,content_path[0:2],content_path[2:])
    
    with open(git_object_path, "rb") as f:
        compressed_data = f.read()

    decompressed_tree = zlib.decompress(compressed_data)
    null_byte_index = decompressed_tree.index(b'\0')
    print(null_byte_index)
    tree_header = decompressed_tree[:null_byte_index]
    tree_body = decompressed_tree[null_byte_index+1:]
    print(tree_body)
    

if __name__ == "__main__":
    main()
