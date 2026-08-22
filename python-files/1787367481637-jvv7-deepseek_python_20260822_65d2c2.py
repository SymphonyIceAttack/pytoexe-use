#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DICOM Privacy Anonymizer
Removes privacy information from DICOM files
"""

import os
import sys

# ============================================================
# IMPORTANT FIX: Handle missing GDCM module gracefully
# ============================================================
try:
    import pydicom
    from pydicom import dcmread
    # Try to import gdcm, but don't fail if it's not available
    try:
        import gdcm
    except ImportError:
        # GDCM not available, use fallback
        pass
except ImportError as e:
    print(f"❌ Error: {e}")
    print("Please install pydicom: pip install pydicom")
    sys.exit(1)

# Define privacy tags to remove
PRIVACY_TAGS = [
    (0x0008, 0x0050),  # Accession Number
    (0x0010, 0x0010),  # Patient's Name
    (0x0010, 0x0020),  # Patient ID
    (0x0010, 0x0030),  # Patient's Birth Date
    (0x0010, 0x0032),  # Patient's Birth Time
    (0x0010, 0x0040),  # Patient's Sex
    (0x0010, 0x1010),  # Patient's Age
    (0x0010, 0x21C0),  # Pregnancy Status
    (0x0008, 0x0080),  # Institution Name
]

def anonymize_dicom(input_file, output_file=None, verbose=True):
    """
    Remove privacy information from DICOM file
    
    Args:
        input_file: Path to input DICOM file
        output_file: Path to output file (if None, overwrite original)
        verbose: Print progress messages
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if verbose:
            print(f"📖 Reading: {os.path.basename(input_file)}")
        
        # Read DICOM file with explicit options to avoid GDCM
        ds = dcmread(input_file, force=True, stop_before_pixels=False)
        
        # Check if pixel data exists without triggering pixel loading
        has_pixel_data = (0x7FE0, 0x0010) in ds
        if verbose and has_pixel_data:
            print("  ✅ Pixel data detected")
        
        # Remove privacy tags
        removed_count = 0
        removed_tags = []
        
        for tag in PRIVACY_TAGS:
            if tag in ds:
                tag_name = ds[tag].name
                vr = ds[tag].VR
                
                # Set appropriate empty value based on VR type
                if vr in ['US', 'SS', 'UL', 'SL', 'FL', 'FD']:
                    ds[tag].value = 0
                elif vr in ['DA', 'TM', 'DT']:
                    ds[tag].value = ''
                elif vr == 'PN':
                    ds[tag].value = ''
                else:
                    ds[tag].value = 'NONE'
                
                removed_count += 1
                removed_tags.append(tag_name)
                if verbose:
                    print(f"  ✅ Removed: {tag_name}")
        
        if removed_count == 0:
            if verbose:
                print("  ℹ️  No privacy tags found")
            return True
        
        # Determine output path
        if output_file is None:
            output_file = input_file
            if verbose:
                print(f"💾 Overwriting: {os.path.basename(output_file)}")
        else:
            if verbose:
                print(f"💾 Saving to: {os.path.basename(output_file)}")
        
        # Save file with explicit options
        ds.save_as(output_file, write_like_original=True)
        
        # Verify
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            if verbose:
                print(f"  📏 Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                
                # Quick verification without loading pixels
                try:
                    verify_ds = dcmread(output_file, force=True, stop_before_pixels=True)
                    still_has_pixel = (0x7FE0, 0x0010) in verify_ds
                    if still_has_pixel:
                        print("  ✅ Pixel data preserved")
                except:
                    pass
        
        if verbose:
            print(f"✅ Done! Removed {removed_count} tags")
        return True
        
    except FileNotFoundError:
        if verbose:
            print(f"❌ File not found: {input_file}")
        return False
    except Exception as e:
        if verbose:
            print(f"❌ Error: {str(e)}")
        return False

def process_file(file_path, create_new=True):
    """
    Process a single DICOM file
    
    Args:
        file_path: Path to DICOM file
        create_new: If True, create new file with suffix, else overwrite
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print("\n" + "=" * 60)
    print("🔒 Processing: " + os.path.basename(file_path))
    print("=" * 60)
    
    if create_new:
        dir_name = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(dir_name, f"{base_name}_anonymized.dcm")
        print(f"📁 Output: {os.path.basename(output_path)}")
    else:
        output_path = None
        print("⚠️  Will overwrite original file!")
    
    print("-" * 60)
    success = anonymize_dicom(file_path, output_path, verbose=True)
    print("-" * 60)
    
    if success:
        print("✅ Processing completed successfully!")
    else:
        print("❌ Processing failed!")
    
    return success

def process_folder(folder_path, create_new=True):
    """
    Process all DICOM files in a folder
    
    Args:
        folder_path: Path to folder containing DICOM files
        create_new: If True, create new folder with suffix, else overwrite
    """
    if not os.path.isdir(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return
    
    # Get all files
    files = [f for f in os.listdir(folder_path) 
             if os.path.isfile(os.path.join(folder_path, f))]
    
    if not files:
        print("❌ No files found in folder")
        return
    
    print("\n" + "=" * 60)
    print(f"📁 Batch Processing: {folder_path}")
    print(f"📄 Found {len(files)} files")
    print("=" * 60)
    
    # Create output folder if needed
    output_folder = None
    if create_new:
        output_folder = folder_path + "_anonymized"
        os.makedirs(output_folder, exist_ok=True)
        print(f"📁 Output folder: {output_folder}")
    else:
        print("⚠️  Will overwrite original files!")
    
    print("-" * 60)
    
    success_count = 0
    for i, filename in enumerate(files, 1):
        input_path = os.path.join(folder_path, filename)
        
        if create_new and output_folder:
            output_path = os.path.join(output_folder, filename)
        else:
            output_path = None
        
        print(f"\n[{i}/{len(files)}] Processing: {filename}")
        if anonymize_dicom(input_path, output_path, verbose=True):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Batch complete! Success: {success_count}/{len(files)}")
    print("=" * 60)

def show_help():
    """Display help information"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           DICOM Privacy Anonymizer v2.2                     ║
║                                                             ║
║  Removes privacy information from DICOM files              ║
║  Replaces with appropriate empty values:                   ║
║    - String tags → 'NONE'                                  ║
║    - Numeric tags → 0                                      ║
║    - Date/Time tags → ''                                   ║
║    - Patient Name → ''                                     ║
║                                                             ║
║  Supported tags:                                           ║
║    (0008,0050) AccessionNumber                             ║
║    (0010,0010) PatientName                                 ║
║    (0010,0020) PatientID                                   ║
║    (0010,0030) PatientBirthDate                            ║
║    (0010,0032) PatientBirthTime                            ║
║    (0010,0040) PatientSex                                  ║
║    (0010,1010) PatientAge                                  ║
║    (0010,21C0) PregnancyStatus                             ║
║    (0008,0080) InstitutionName                             ║
╚══════════════════════════════════════════════════════════════╝
    """)

def main():
    """Main entry point"""
    
    # Check if file was dragged onto the exe
    if len(sys.argv) > 1:
        # User dragged a file/folder onto the exe
        path = sys.argv[1]
        if os.path.isfile(path):
            print(f"\n📁 File dropped: {path}")
            print("\n💡 Save method:")
            print("  1. Create new file (_anonymized.dcm)")
            print("  2. Overwrite original")
            choice = input("Select (1/2): ").strip()
            
            create_new = choice != "2"
            process_file(path, create_new)
        elif os.path.isdir(path):
            print(f"\n📁 Folder dropped: {path}")
            print("\n💡 Save method:")
            print("  1. Create new folder (_anonymized)")
            print("  2. Overwrite original files")
            choice = input("Select (1/2): ").strip()
            
            create_new = choice != "2"
            process_folder(path, create_new)
        else:
            print(f"❌ Invalid path: {path}")
        
        input("\nPress Enter to exit...")
        return
    
    # Interactive mode
    show_help()
    
    while True:
        print("\n" + "=" * 60)
        print("Main Menu:")
        print("  1. Process single file")
        print("  2. Process folder (batch mode)")
        print("  3. Help")
        print("  4. Exit")
        print("=" * 60)
        
        choice = input("Select (1-4): ").strip()
        
        if choice == "1":
            # Single file
            file_path = input("\n📁 Enter file path (drag and drop): ").strip().strip('"')
            if not file_path:
                print("❌ No path entered")
                continue
            
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue
            
            print("\n💡 Save method:")
            print("  1. Create new file (_anonymized.dcm)")
            print("  2. Overwrite original")
            save_choice = input("Select (1/2): ").strip()
            
            create_new = save_choice != "2"
            process_file(file_path, create_new)
            
        elif choice == "2":
            # Batch mode
            folder_path = input("\n📁 Enter folder path (drag and drop): ").strip().strip('"')
            if not folder_path:
                print("❌ No path entered")
                continue
            
            if not os.path.isdir(folder_path):
                print(f"❌ Folder not found: {folder_path}")
                continue
            
            print("\n💡 Save method:")
            print("  1. Create new folder (_anonymized)")
            print("  2. Overwrite original files")
            save_choice = input("Select (1/2): ").strip()
            
            create_new = save_choice != "2"
            process_folder(folder_path, create_new)
            
        elif choice == "3":
            show_help()
            
        elif choice == "4":
            print("\nGoodbye!")
            break
            
        else:
            print("❌ Invalid choice. Please select 1-4.")
        
        print("\n" + "-" * 60)
        input("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")