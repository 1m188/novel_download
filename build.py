import subprocess
import os
import zipfile
from pathlib import Path
import shutil
import argparse


def pack_pyinstaller():
    subprocess.run([
        "pyinstaller",
        "--distpath",
        "build/pyinstaller/dist",
        "--workpath",
        "build/pyinstaller/work",
        "pack.spec",
    ])


def pack_embed():
    os.makedirs("./build/embed/py/Lib/site-packages", exist_ok=True)

    with zipfile.ZipFile("./python-3.10.11-embed-amd64.zip", "r") as zipf:
        zipf.extractall("./build/embed/py")

    path = Path("./build/embed/py")
    for file in path.rglob("*"):
        if str(file).endswith('._pth'):
            with open(file, 'a') as f:
                f.write('import site\n')
                f.write('../src\n')
            break

    subprocess.run([
        'pip',
        'install',
        '-r',
        'requirements_embed.txt',
        '-t',
        './build/embed/py/Lib/site-packages',
    ])

    os.makedirs('./build/embed/src', exist_ok=True)
    shutil.copytree(
        './src',
        './build/embed/src',
        ignore=shutil.ignore_patterns('*.pyc', '__pycache__'),
        copy_function=shutil.copy2,
        dirs_exist_ok=True,
    )

    with open('./build/embed/start.bat', 'w') as f:
        f.write(r'@echo off' + '\n')
        f.write(r'%~dp0py\python.exe %~dp0src\gui.py' + '\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--build',
        type=str,
        choices=['pyinstaller', 'embed'],
        default='pyinstaller',
        help='build type',
    )
    args = parser.parse_args()

    if args.build == 'pyinstaller':
        pack_pyinstaller()
    elif args.build == 'embed':
        pack_embed()
    else:
        raise ValueError(f'Invalid build type: {args.build}')
