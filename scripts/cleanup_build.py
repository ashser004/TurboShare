import os
import shutil
import sys
from pathlib import Path

def cleanup():
    """Remove unused, heavy libraries from compiled distribution directory."""
    print("Starting post-build cleanup...")
    
    # Target PyInstaller's internal distribution folder
    internal_dir = Path("dist/TurboShare/_internal")
    if not internal_dir.exists():
        print(f"Error: Build folder not found at '{internal_dir.resolve()}'. Make sure to run PyInstaller first.", file=sys.stderr)
        sys.exit(1)

    # Specific heavy, unused DLLs and .pyd files (paths relative to _internal)
    files_to_remove = [
        "PySide6/opengl32sw.dll",
        "PySide6/Qt6Qml.dll",
        "PySide6/Qt6Quick.dll",
        "PySide6/Qt6Pdf.dll",
        "PySide6/Qt6OpenGL.dll",
        "PySide6/Qt6Network.dll",
        "PySide6/Qt6Svg.dll",
        "PySide6/Qt6VirtualKeyboard.dll",
        "PySide6/Qt6QmlModels.dll",
        "PySide6/Qt6QmlMeta.dll",
        "PySide6/Qt6QmlWorkerScript.dll",
        "PySide6/QtNetwork.pyd",
    ]

    # Specific heavy, unused folders (paths relative to _internal)
    folders_to_remove = [
        "PySide6/translations",
    ]

    # Process files
    removed_files_count = 0
    saved_bytes = 0
    for rel_path in files_to_remove:
        file_path = internal_dir / rel_path
        if file_path.exists():
            try:
                size = file_path.stat().st_size
                os.remove(file_path)
                removed_files_count += 1
                saved_bytes += size
                print(f"Removed unused binary: {rel_path} ({size / (1024*1024):.2f} MB)")
            except Exception as e:
                print(f"Warning: Could not remove {rel_path}: {e}")

    # Process folders
    removed_folders_count = 0
    for rel_path in folders_to_remove:
        folder_path = internal_dir / rel_path
        if folder_path.exists():
            try:
                # Calculate folder size
                folder_size = sum(f.stat().st_size for f in folder_path.glob('**/*') if f.is_file())
                shutil.rmtree(folder_path)
                removed_folders_count += 1
                saved_bytes += folder_size
                print(f"Removed unused folder: {rel_path} ({folder_size / (1024*1024):.2f} MB)")
            except Exception as e:
                print(f"Warning: Could not remove folder {rel_path}: {e}")

    saved_mb = saved_bytes / (1024 * 1024)
    print(f"\nCleanup complete! Removed {removed_files_count} files and {removed_folders_count} folders. Saved ~{saved_mb:.2f} MB.")

if __name__ == "__main__":
    cleanup()
