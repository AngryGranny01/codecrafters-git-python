import sys
import os
import zlib

directory_objects_path = ".git/objects"

def main():
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(directory_objects_path)
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    else:
        raise RuntimeError(f"Unknown command #{command}")
    object_read()
    output = sys.stdout

def object_read():
    for root, dirs, files in os.walk(directory_objects_path):
        for file in files:
            file_path = os.path.join(root, file)
            print(f"Found file: {file_path}")
    


if __name__ == "__main__":
    main()
