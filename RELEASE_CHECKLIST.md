# Release Checklist

Use this checklist before publishing a new release.

1) Bump version
   - Run: powershell -NoProfile -ExecutionPolicy Bypass -File scripts\bump-version.ps1 -Version X.Y.Z
   - Confirm `pyproject.toml` shows the new version.

2) Verify core behavior
   - Run basic init/sync on a test site.
   - Ensure `wpdrive --help` works after install.

3) Build Windows EXE
   - Run: powershell -NoProfile -ExecutionPolicy Bypass -File installer\build-exe.ps1
   - Confirm `installer\dist\WPDrive-Install.exe` exists.

4) Commit + tag
   - git add .
   - git commit -m "Release vX.Y.Z"
   - git tag vX.Y.Z

5) Push
   - git push origin main
   - git push origin vX.Y.Z

6) Create GitHub release
   - Create a release for vX.Y.Z
   - Upload `WPDrive-Install.exe` as a release asset.

7) Validate
   - Install from the EXE and from the release ZIP.
   - Confirm PATH is set and `wpdrive` runs.
