import sys
import os
import zlib

directory_objects_path = ".git/objects"

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
        output = sys.stdout
    else:
        raise RuntimeError(f"Unknown command #{command}")


def object_read():
    for root, dirs, files in os.walk(directory_objects_path):
        for file in files:
            print(zlib.decompress(file))
    


if __name__ == "__main__":
    main()
