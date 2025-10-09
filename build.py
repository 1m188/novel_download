import subprocess


def pack_pyinstaller():
    subprocess.run([
        "pyinstaller",
        "--distpath",
        "build/pyinstaller/dist",
        "--workpath",
        "build/pyinstaller/work",
        "pack.spec",
    ])


if __name__ == "__main__":
    pack_pyinstaller()
