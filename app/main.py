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

    for path, directories, files in os.walk(directory_objects_path):
        if file in files:
             print('found %s' % os.path.join(path, file))
    output = sys.stdout


if __name__ == "__main__":
    main()
