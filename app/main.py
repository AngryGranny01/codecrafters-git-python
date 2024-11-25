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

    for path, dirnames, filenames in os.walk('root'):
        print('{} {} {}'.format(repr(path), repr(dirnames), repr(filenames)))
    output = sys.stdout


if __name__ == "__main__":
    main()
