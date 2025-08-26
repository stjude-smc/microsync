#!/usr/bin/env python3
"""
Build script for microsync release artifacts.
Run this to create local release files before pushing to GitHub.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def get_version():
    """Get version from __version__.py"""
    version_file = Path("python/microsync/__version__.py")
    if not version_file.exists():
        raise FileNotFoundError(f"Version file not found: {version_file}")
    
    # Execute the version file to get __version__
    with open(version_file, 'r') as f:
        exec(f.read())
    
    return locals()['__version__']

def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(f"Success: {result.stdout}")
    return True

def main():
    # Clean-up any previous release artifacts
    if Path("release_artifacts").exists():
        for item in Path("release_artifacts").iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    # Get version from single source of truth
    try:
        version = get_version()
        print(f"Building microsync v{version} release artifacts...")
    except Exception as e:
        print(f"Error getting version: {e}")
        return False
    
    # Create release directory
    release_dir = Path("release_artifacts")
    release_dir.mkdir(exist_ok=True)

    # Copy firmware
    print("\n1. Copying firmware...")
    firmware_src = Path("microsync/Release/microsync.bin")
    if firmware_src.exists():
        dest_file = os.path.join(release_dir, f"microsync-{version}.bin")
        shutil.copy2(firmware_src, dest_file)
        print(f"Copied: {dest_file}")
    else:
        print("❌ Firmware bin file not found. Please open `microsync.atsln` in Microchip Studio, "
              "select the Release build configuration, and build the project, then rerun this script.")
        return False

    # Build Python package
    print("\n2. Building Python package...")
    if not run_command("python -m build", cwd="python"):
        print("Failed to build Python package")
        return False
    
    # Copy Python artifacts
    python_dist = Path("python/dist")
    if python_dist.exists():
        for file in python_dist.glob("*"):
            shutil.copy2(file, release_dir)
            print(f"Copied: {file.name}")
    
    
    # Create release notes template
    print("\n3. Creating release notes document...")
    release_notes = release_dir / f"RELEASE_NOTES-{version}.md"
    with open(release_notes, 'w') as f:
        f.write(f"""# microsync v{version} Release Notes


## Python Driver Installation
```bash
pip install microsync-{version}-py3-none-any.whl
```

## Firmware Upload
Upload `microsync-{version}.bin` to your Arduino Due using BOSSA or Atmel-ICE with Microchip Studio.

### Uploading firmware with BOSSA

1. Download BOSSA from https://github.com/shumatech/BOSSA/releases (pick the right binary for your OS).
2. Connect Due to your computer, use the USB port next to the power jack.
3. Find newly created Arduino Due COM port (e.g. in the Device manager).
4. On your Due, press **Erase** and **Reset** buttons at the same time (to enter programming mode).


#### Upload via BOSSA GUI
1. Run BOSSA GUI.
2. Select the correct COM port.
3. Select `microsync-{version}.bin` file.
4. **Important**: Check the "Boot from Flash" option (this sets GPNVM0=1).
5. Click "Write".

#### Upload via command line
1. Put `bossac.exe` (or `bossac` on Mac/Linux) and `microsync-{version}.bin` in the same folder.
2. Open a terminal in that folder and run (replace `<COM-PORT>` with the actual COM port of your Due):

```sh
bossac.exe -e -w -v -b microsync-{version}.bin -p <COM-PORT>
```


### Uploading firmware with Microchip Studio using Atmel-ICE debugger
1. Connect Atmel-ICE SAM connector to JTAG header on your Due.
2. Connect Atmel-ICE to your computer.
3. Power up your Due with a USB cable.
4. Open Microchip Studio.
5. Open the Device Programming dialog (Ctrl+Shift+P).
6. Select Atmel-ICE tool, `ATSAM3X8E` device, JTAG interface, click "Apply".
7. Go to "Memory" tab, select `microsync-{version}.bin` file, click "Program".


## Documentation
Visit https://stjude-smc.github.io/microsync/ for the latest documentation.
""")
    
    print(f"\n✅ Release artifacts created in: {release_dir}")
    print("\nFiles created:")
    for file in release_dir.iterdir():
        if file.is_file():
            print(f"  - {file.name}")
        elif file.is_dir():
            print(f"  - {file.name}/ (directory)")
    
    print(f"\nTo create a GitHub release:")
    print(f"1. git tag v{version}")
    print(f"2. git push origin v{version}")
    print(f"3. Draft a new release on GitHub https://github.com/stjude-smc/microsync/releases/new\n")

if __name__ == "__main__":
    main() 