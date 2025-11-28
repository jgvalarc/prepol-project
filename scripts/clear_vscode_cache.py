"""
VS Code Cache Cleaner for Windows
Safely clears VS Code cache directories to resolve performance/corruption issues.
Includes GitHub Copilot-specific cache cleanup and extension restart.

Usage:
    python clear_vscode_cache.py [--backup] [--dry-run] [--copilot-only] [--restart-extension]

Options:
    --backup            Create backup of cache before deletion
    --dry-run           Show what would be deleted without actually deleting
    --copilot-only      Only clear GitHub Copilot-related caches
    --restart-extension Restart GitHub Copilot extension after clearing (requires VS Code running)
"""

import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import sys
import subprocess
import glob


def get_vscode_cache_paths(copilot_only=False):
    """Get VS Code cache directories on Windows.
    
    Args:
        copilot_only: If True, only return GitHub Copilot-related caches
    """
    user_profile = Path(os.environ.get('USERPROFILE', ''))
    app_data = Path(os.environ.get('APPDATA', ''))
    local_app_data = Path(os.environ.get('LOCALAPPDATA', ''))
    
    # GitHub Copilot-specific cache paths
    copilot_paths = {}
    
    # Copilot global storage (includes auth tokens and settings)
    copilot_global_storage = app_data / 'Code' / 'User' / 'globalStorage' / 'github.copilot'
    if copilot_global_storage.exists():
        copilot_paths['Copilot Global Storage'] = copilot_global_storage
    
    # Copilot chat storage
    copilot_chat_storage = app_data / 'Code' / 'User' / 'globalStorage' / 'github.copilot-chat'
    if copilot_chat_storage.exists():
        copilot_paths['Copilot Chat Storage'] = copilot_chat_storage
    
    # Copilot workspace storage (per-workspace caches)
    workspace_storage = app_data / 'Code' / 'User' / 'workspaceStorage'
    if workspace_storage.exists():
        for workspace_dir in workspace_storage.iterdir():
            if workspace_dir.is_dir():
                copilot_ws = workspace_dir / 'github.copilot'
                if copilot_ws.exists():
                    copilot_paths[f'Copilot Workspace ({workspace_dir.name[:8]}...)'] = copilot_ws
                copilot_chat_ws = workspace_dir / 'github.copilot-chat'
                if copilot_chat_ws.exists():
                    copilot_paths[f'Copilot Chat Workspace ({workspace_dir.name[:8]}...)'] = copilot_chat_ws
    
    # Copilot extension logs
    logs_dir = app_data / 'Code' / 'logs'
    if logs_dir.exists():
        for session_dir in logs_dir.iterdir():
            if session_dir.is_dir():
                exthost_output = session_dir / 'exthost' / 'output_logging_*'
                for output_dir in glob.glob(str(exthost_output)):
                    output_path = Path(output_dir)
                    for copilot_log in output_path.glob('*-GitHub Copilot*'):
                        if copilot_log.exists():
                            copilot_paths[f'Copilot Logs ({session_dir.name[:8]}...)'] = copilot_log
    
    # Microsoft Copilot cache (separate from GitHub Copilot)
    ms_copilot = local_app_data / 'Microsoft' / 'Copilot'
    if ms_copilot.exists():
        copilot_paths['Microsoft Copilot Cache'] = ms_copilot
    
    if copilot_only:
        return copilot_paths
    
    # General VS Code cache paths
    general_paths = {
        'User Cache': local_app_data / 'Microsoft' / 'vscode-cpptools',
        'Extension Cache': user_profile / '.vscode' / 'extensions' / '.obsolete',
        'GPUCache': app_data / 'Code' / 'GPUCache',
        'CachedData': app_data / 'Code' / 'CachedData',
        'CachedExtensions': app_data / 'Code' / 'CachedExtensions',
        'CachedExtensionVSIXs': app_data / 'Code' / 'CachedExtensionVSIXs',
        'logs': app_data / 'Code' / 'logs',
        'Service Worker': app_data / 'Code' / 'Service Worker',
        'Code Cache': app_data / 'Code' / 'Code Cache',
        'Crashpad': app_data / 'Code' / 'Crashpad',
        'Local Storage': app_data / 'Code' / 'Local Storage',
        'Session Storage': app_data / 'Code' / 'Session Storage',
    }
    
    # Combine and filter to only existing paths
    all_paths = {**copilot_paths, **general_paths}
    existing_paths = {name: path for name, path in all_paths.items() if path.exists()}
    
    return existing_paths


def get_dir_size(path):
    """Calculate total size of directory in MB."""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    pass
    except (OSError, PermissionError):
        pass
    return total_size / (1024 * 1024)  # Convert to MB


def backup_cache(cache_paths, backup_dir):
    """Create backup of cache directories."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_root = Path(backup_dir) / f'vscode_cache_backup_{timestamp}'
    backup_root.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📦 Creating backup at: {backup_root}")
    
    backed_up = []
    for name, path in cache_paths.items():
        try:
            backup_path = backup_root / name.replace(' ', '_')
            print(f"  • Backing up {name}...", end=' ')
            shutil.copytree(path, backup_path)
            print("✓")
            backed_up.append(name)
        except Exception as e:
            print(f"⚠ Failed: {e}")
    
    print(f"\n✓ Backed up {len(backed_up)}/{len(cache_paths)} cache directories")
    return backup_root


def clear_cache(cache_paths, dry_run=False):
    """Clear VS Code cache directories."""
    total_size = 0
    cleared = []
    
    print("\n🗑️  Clearing cache directories...")
    
    for name, path in cache_paths.items():
        size_mb = get_dir_size(path)
        total_size += size_mb
        
        if dry_run:
            print(f"  [DRY RUN] Would delete {name}: {size_mb:.2f} MB")
            cleared.append(name)
        else:
            try:
                print(f"  • Deleting {name} ({size_mb:.2f} MB)...", end=' ')
                shutil.rmtree(path)
                print("✓")
                cleared.append(name)
            except PermissionError:
                print("⚠ Permission denied (VS Code may be running)")
            except Exception as e:
                print(f"⚠ Failed: {e}")
    
    return cleared, total_size


def check_vscode_running():
    """Check if VS Code is currently running."""
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq Code.exe'],
            capture_output=True,
            text=True
        )
        return 'Code.exe' in result.stdout
    except Exception:
        return False


def find_vscode_cli():
    """Find VS Code CLI (code.cmd) on Windows."""
    # Common installation paths
    search_paths = [
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Microsoft VS Code' / 'bin' / 'code.cmd',
        Path(os.environ.get('PROGRAMFILES', '')) / 'Microsoft VS Code' / 'bin' / 'code.cmd',
        Path(os.environ.get('PROGRAMFILES(X86)', '')) / 'Microsoft VS Code' / 'bin' / 'code.cmd',
    ]
    
    # Check common paths
    for path in search_paths:
        if path.exists():
            return path
    
    # Check PATH
    try:
        result = subprocess.run(
            ['where', 'code.cmd'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return Path(result.stdout.strip().split('\n')[0])
    except Exception:
        pass
    
    return None


def is_copilot_installed():
    """Check if GitHub Copilot extension is installed."""
    try:
        code_cli = find_vscode_cli()
        if not code_cli:
            return False
        
        result = subprocess.run(
            [str(code_cli), '--list-extensions'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return 'github.copilot' in result.stdout.lower()
    except Exception:
        return False


def restart_copilot_extension():
    """Restart GitHub Copilot extension using VS Code CLI.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    code_cli = find_vscode_cli()
    
    if not code_cli:
        return False, "VS Code CLI (code.cmd) not found in PATH or standard locations"
    
    if not is_copilot_installed():
        return False, "GitHub Copilot extension is not installed"
    
    try:
        # Note: VS Code CLI extension commands don't work while editor is running
        # We'll provide instructions instead
        if check_vscode_running():
            return False, "VS Code is running - extension restart via CLI not supported while editor is active"
        
        # If VS Code is not running, we can disable/enable
        print("\n🔄 Restarting GitHub Copilot extension...")
        
        # Disable extension
        result = subprocess.run(
            [str(code_cli), '--disable-extension', 'github.copilot'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return False, f"Failed to disable extension: {result.stderr}"
        
        # Enable extension
        result = subprocess.run(
            [str(code_cli), '--enable-extension', 'github.copilot'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return False, f"Failed to enable extension: {result.stderr}"
        
        return True, "Extension restarted successfully"
        
    except subprocess.TimeoutExpired:
        return False, "CLI command timed out"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    parser = argparse.ArgumentParser(
        description='Safely clear VS Code cache directories (includes GitHub Copilot)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clear_vscode_cache.py                          # Clear all caches
  python clear_vscode_cache.py --dry-run                # Preview what would be deleted
  python clear_vscode_cache.py --copilot-only           # Only clear Copilot caches
  python clear_vscode_cache.py --backup                 # Backup before clearing
  python clear_vscode_cache.py --restart-extension      # Restart Copilot after clearing
  python clear_vscode_cache.py --copilot-only --restart-extension  # Full Copilot reset
        """
    )
    
    parser.add_argument('--backup', action='store_true',
                        help='Create backup before clearing cache')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be deleted without deleting')
    parser.add_argument('--copilot-only', action='store_true',
                        help='Only clear GitHub Copilot-related caches')
    parser.add_argument('--restart-extension', action='store_true',
                        help='Restart GitHub Copilot extension after clearing (manual if VS Code running)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    if args.copilot_only:
        print("GITHUB COPILOT CACHE CLEANER")
    else:
        print("VS CODE CACHE CLEANER")
    print("=" * 70)
    
    # Check if VS Code is running
    vscode_running = check_vscode_running()
    if vscode_running:
        if args.restart_extension:
            print("\n⚠️  WARNING: VS Code is currently running!")
            print("   Extension restart via CLI requires VS Code to be closed.")
            print("   After cache cleanup, you'll need to manually reload VS Code window.")
        else:
            print("\n⚠️  WARNING: VS Code is currently running!")
            print("   For best results, close VS Code before running this script.")
        response = input("\n   Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("\n❌ Aborted by user")
            return 1
    
    # Get cache paths
    cache_paths = get_vscode_cache_paths(copilot_only=args.copilot_only)
    
    if args.copilot_only and cache_paths:
        print("\n⚠️  COPILOT-ONLY MODE ENABLED")
        print("   This will clear GitHub Copilot caches including:")
        print("   • Authentication tokens (you may need to re-authenticate)")
        print("   • Conversation history")
        print("   • Cached suggestions")
    
    if not cache_paths:
        print("\n✓ No VS Code cache directories found")
        return 0
    
    # Display cache information
    print(f"\n📊 Found {len(cache_paths)} cache directories:")
    total_size = 0
    for name, path in cache_paths.items():
        size_mb = get_dir_size(path)
        total_size += size_mb
        print(f"  • {name}: {size_mb:.2f} MB")
        print(f"    {path}")
    
    print(f"\n📦 Total cache size: {total_size:.2f} MB")
    
    if args.dry_run:
        print("\n[DRY RUN MODE - No files will be deleted]")
    
    # Backup if requested
    backup_location = None
    if args.backup:
        backup_dir = Path.cwd() / 'vscode_cache_backups'
        backup_location = backup_cache(cache_paths, backup_dir)
        if not args.dry_run:
            print(f"\n✓ Backup created at: {backup_location}")
    
    # Confirm deletion
    if not args.dry_run:
        print("\n⚠️  This will permanently delete the cache directories listed above.")
        response = input("   Proceed with deletion? (y/N): ")
        if response.lower() != 'y':
            print("\n❌ Aborted by user")
            return 1
    
    # Clear cache
    cleared, freed_mb = clear_cache(cache_paths, dry_run=args.dry_run)
    
    # Handle extension restart
    restart_attempted = False
    restart_success = False
    restart_msg = ""
    
    if args.restart_extension and not args.dry_run and len(cleared) > 0:
        restart_attempted = True
        restart_success, restart_msg = restart_copilot_extension()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if args.dry_run:
        print(f"[DRY RUN] Would clear: {len(cleared)}/{len(cache_paths)} directories")
        print(f"[DRY RUN] Would free: {freed_mb:.2f} MB")
        if args.copilot_only:
            print(f"[DRY RUN] Mode: GitHub Copilot only")
    else:
        print(f"✓ Cleared: {len(cleared)}/{len(cache_paths)} directories")
        print(f"✓ Freed: {freed_mb:.2f} MB")
        
        if backup_location:
            print(f"✓ Backup: {backup_location}")
        
        # Extension restart status
        if restart_attempted:
            if restart_success:
                print(f"✓ Extension restart: {restart_msg}")
            else:
                print(f"⚠ Extension restart: {restart_msg}")
        
        print("\n📝 Next steps:")
        if args.copilot_only:
            if vscode_running:
                print("  1. Reload VS Code window: Ctrl+Shift+P → 'Developer: Reload Window'")
                print("  2. Or restart VS Code completely")
                print("  3. GitHub Copilot may prompt for re-authentication")
                print("  4. Test Copilot by typing a comment and waiting for suggestions")
            else:
                print("  1. Start VS Code")
                print("  2. GitHub Copilot will reinitialize with fresh cache")
                print("  3. You may need to re-authenticate (Ctrl+Shift+P → 'GitHub Copilot: Sign In')")
                print("  4. Test Copilot by typing a comment and waiting for suggestions")
        else:
            print("  1. Restart VS Code (or reload window with Ctrl+R if already running)")
            print("  2. VS Code will rebuild cache on next launch")
            print("  3. Extensions may need to reactivate")
            if any('Copilot' in name for name in cleared):
                print("  4. GitHub Copilot may prompt for re-authentication")
    
    print("=" * 70)
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
