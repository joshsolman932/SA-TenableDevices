"""
Splunk app build script for SA-TenableDevices.

Packages the existing app structure into a distributable .tgz file.
Output goes to dist/:
  dist/SA-TenableDevices_0.0.3/      <- assembled app (inspect this)
  dist/SA-TenableDevices_0.0.3.tgz   <- packaged app (deploy this)

Version: major.minor from app_build.yml, patch from git commit count.
"""
import os
import re
import json
import shutil
import tarfile
import subprocess
import yaml

APP_BUILD_YML = "app_build.yml"
DIST_DIR = "dist"

# Directories and files to include in the app package
APP_DIRS = ["bin", "default", "lib", "lookups", "metadata", "static", "appserver", "LICENSES"]
APP_FILES = ["README.txt", "README.md", "app.manifest"]


def get_patch_version():
    """Get patch number from git commit count, or 0 if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 0


def get_version(app):
    """Build full version: major.minor from app_build.yml, patch from git."""
    base = str(app.get("version", "0.0"))
    parts = base.split(".")
    major = parts[0] if len(parts) > 0 else "0"
    minor = parts[1] if len(parts) > 1 else "0"
    patch = get_patch_version()
    return f"{major}.{minor}.{patch}"


def update_app_conf_version(app_conf_path, version):
    """Update the version in an existing app.conf file."""
    with open(app_conf_path, "r") as f:
        content = f.read()

    # Update version in [launcher] and [id] sections
    content = re.sub(r"(version\s*=\s*)[\d.]+", rf"\g<1>{version}", content)

    with open(app_conf_path, "w") as f:
        f.write(content)


def update_app_manifest_version(manifest_path, version):
    """Update the version in app.manifest file."""
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    manifest["info"]["id"]["version"] = version

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=4)


def main():
    with open(APP_BUILD_YML) as f:
        config = yaml.safe_load(f)

    app = config["app"]
    appid = app["appid"]
    version = get_version(app)
    name = f"{appid}_{version}"

    app_dir = os.path.join(DIST_DIR, name)

    # Clean previous build
    if os.path.exists(app_dir):
        shutil.rmtree(app_dir, ignore_errors=True)
    os.makedirs(app_dir, exist_ok=True)

    # Copy app directories
    for dir_name in APP_DIRS:
        if os.path.exists(dir_name):
            shutil.copytree(dir_name, os.path.join(app_dir, dir_name), dirs_exist_ok=True)

    # Copy app files
    for file_name in APP_FILES:
        if os.path.exists(file_name):
            shutil.copy2(file_name, app_dir)

    # Update version in app.conf
    app_conf_path = os.path.join(app_dir, "default", "app.conf")
    if os.path.exists(app_conf_path):
        update_app_conf_version(app_conf_path, version)

    # Update version in app.manifest
    manifest_path = os.path.join(app_dir, "app.manifest")
    if os.path.exists(manifest_path):
        update_app_manifest_version(manifest_path, version)

    # Package as .tgz
    tgz_path = os.path.join(DIST_DIR, f"{name}.tgz")
    with tarfile.open(tgz_path, "w:gz") as tar:
        tar.add(app_dir, arcname=appid)

    print(f"Version: {version}")
    print(f"Built: {tgz_path}")
    print(f"Extracted app: {app_dir}")


if __name__ == "__main__":
    main()
