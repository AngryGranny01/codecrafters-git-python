import sys
import os
import zlib

directory_objects_path = ".git/objects"
output = sys.stdout

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
        object_read()
    elif command == "hash-object":
        object_write(sys.argv[3])
    else:
        raise RuntimeError(f"Unknown command #{command}")


def object_read():
    for root, dirs, files in os.walk(directory_objects_path):
        for file in files:
            file_path = os.path.join(root, file)
        
            with open(file_path, "rb") as f:
                compressed_content = f.read()

                content = zlib.decompress(compressed_content)
                result = content.decode("utf-8").split("\x00")
                output.write(result[1])

def object_write(content_path):
    with open(content_path, "rt") as f:
        newcontent = f.read()
        print(newcontent)

    


if __name__ == "__main__":
    main()
