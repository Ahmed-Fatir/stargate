#!/usr/bin/env python3
"""
Startgate Test File Discovery Script
Script to discover files across multiple app databases and folders for testing the Startgate service
"""
import os
import random
from pathlib import Path

def discover_files(service="app", target_count=100):
    """Discover files across different databases and folders for a specific service"""
    
    service_paths = {
        "system": "/ceph/data/infra/odoo/system-fs/filestore",
        "app": "/ceph/data/infra/odoo/app-fs/filestore",
        "btblk": "/ceph/data/infra/odoo/btblk-fs/filestore", 
        "decimal": "/ceph/data/infra/odoo/decimal-fs/filestore",
        "srm": "/ceph/data/infra/odoo/srm-fs/filestore",
        "portal": "/ceph/data/infra/odoo/portal-fs/filestore"
    }
    
    if service not in service_paths:
        available = ", ".join(service_paths.keys())
        raise ValueError(f"Service '{service}' not supported. Available: {available}")
    
    base_path = service_paths[service]
    """Discover files across different databases and folders"""
    all_files = []
    
    # Get all experio_cabinet databases
    databases = [d for d in os.listdir(base_path) if d.startswith("experio_cabinet_")]
    print(f"Found {len(databases)} databases")
    
    # Sample a few files from each database to build a diverse collection
    for database in databases:
        db_path = Path(base_path) / database
        if not db_path.exists():
            continue
            
        print(f"Scanning {database}...")
        
        # Get first few folders only (faster)
        folders = [f for f in os.listdir(db_path) if len(f) == 2 and f.isalnum()]
        folders = folders[:5]  # Only check first 5 folders per database
        
        db_files = []
        for folder in folders:
            folder_path = db_path / folder
            if not folder_path.exists():
                continue
                
            try:
                # Get up to 3 files from this folder
                file_hashes = [f for f in os.listdir(folder_path) if len(f) == 40]
                
                if file_hashes:
                    # Take first few files (fast, no random sampling needed here)
                    sampled = file_hashes[:2]  # Max 2 files per folder
                    
                    for file_hash in sampled:
                        file_spec = f"{database}-{file_hash}"
                        file_path = folder_path / file_hash
                        size = file_path.stat().st_size
                        all_files.append({
                            "spec": file_spec,
                            "database": database,
                            "folder": folder, 
                            "hash": file_hash,
                            "size": size
                        })
                        
                        # Stop if we have enough files total
                        if len(all_files) >= target_count * 3:  # Collect 3x target for good randomization
                            break
                
                if len(all_files) >= target_count * 3:
                    break
                            
            except PermissionError:
                continue
            except Exception as e:
                continue
        
        # Stop scanning databases if we have enough files
        if len(all_files) >= target_count * 3:
            break
    
    print(f"Found {len(all_files)} total files")
    
    # Randomly sample exactly target_count files
    if len(all_files) > target_count:
        import random
        random.shuffle(all_files)
        selected_files = all_files[:target_count]
    else:
        selected_files = all_files
    
    return selected_files

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate test files for Startgate service testing')
    parser.add_argument('--service', default='app', choices=['system', 'app', 'btblk', 'decimal', 'srm', 'portal'],
                      help='Service to discover files from (default: app)')
    parser.add_argument('--count', type=int, default=100, help='Number of files to discover (default: 100)')
    
    args = parser.parse_args()
    
    print(f"Discovering files for {args.service} service...")
    files = discover_files(service=args.service, target_count=args.count)
    
    print(f"\nDiscovery Summary:")
    print(f"Total files found: {len(files)}")
    
    # Group by database and folder
    by_db = {}
    by_folder = {}
    total_size = 0
    
    for file_info in files:
        db = file_info['database']
        folder = file_info['folder']
        size = file_info['size']
        
        by_db[db] = by_db.get(db, 0) + 1
        by_folder[folder] = by_folder.get(folder, 0) + 1
        total_size += size
    
    print(f"\nFiles by database:")
    for db, count in sorted(by_db.items())[:10]:  # Show first 10
        print(f"  {db}: {count} files")
    if len(by_db) > 10:
        print(f"  ... and {len(by_db) - 10} more databases")
    
    print(f"\nTotal size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    
    # Save file specs for testing
    file_specs = [f['spec'] for f in files]
    
    import json
    test_data = {"files": file_specs}
    
    filename = f'test_files_{args.service}.json'
    with open(filename, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"\n✅ Files saved to {filename}")
    print(f"\n🚀 Test the {args.service} service:")
    print(f"curl -X POST http://localhost:8000/{args.service}/files \\")
    print(f"  -H \"Content-Type: application/json\" \\")
    print(f"  -H \"Authorization: Bearer your_token_here\" \\")
    print(f"  -d @{filename} \\")
    print(f"  --output {args.service}_files.zip")

