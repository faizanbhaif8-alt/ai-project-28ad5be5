"""
File Manager Utility Module for BotManager V2.5

This module provides comprehensive file and directory management capabilities
for the Enhanced AI Project Generator with Multi-Bot Support.
It handles file operations, directory management, and file system utilities.
"""

import os
import shutil
import json
import yaml
import pickle
import hashlib
import tempfile
import zipfile
import tarfile
import pathlib
import fnmatch
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, BinaryIO, Callable
from pathlib import Path
import logging

# Configure logging
logger = logging.getLogger(__name__)


class FileManager:
    """
    Main File Manager class for handling all file and directory operations.
    
    This class provides methods for:
    - File and directory creation/deletion
    - File reading/writing in various formats
    - File searching and pattern matching
    - Backup and restore operations
    - File validation and integrity checks
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize FileManager with optional base directory.
        
        Args:
            base_path: Base directory for all file operations. If None, uses current directory.
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.ensure_directory_exists(self.base_path)
        logger.info(f"FileManager initialized with base path: {self.base_path}")
    
    # ==================== Directory Operations ====================
    
    def ensure_directory_exists(self, directory_path: Union[str, Path]) -> Path:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            Path object of the created/existing directory
        """
        path = Path(directory_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {path}")
        return path
    
    def create_directory(self, directory_path: Union[str, Path], 
                        parents: bool = True, exist_ok: bool = True) -> Path:
        """
        Create a directory with optional parent creation.
        
        Args:
            directory_path: Path to create
            parents: Create parent directories if they don't exist
            exist_ok: Don't raise error if directory already exists
            
        Returns:
            Path object of the created directory
        """
        path = Path(directory_path)
        path.mkdir(parents=parents, exist_ok=exist_ok)
        logger.debug(f"Directory created/ensured: {path}")
        return path
    
    def list_directory(self, directory_path: Union[str, Path], 
                      pattern: str = "*", recursive: bool = False) -> List[Path]:
        """
        List files and directories matching a pattern.
        
        Args:
            directory_path: Directory to list
            pattern: Glob pattern to match (e.g., "*.py", "**/*.txt")
            recursive: Whether to search recursively
            
        Returns:
            List of Path objects matching the pattern
        """
        path = Path(directory_path)
        if not path.exists():
            logger.warning(f"Directory does not exist: {path}")
            return []
        
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))
        
        logger.debug(f"Found {len(files)} items in {path} matching pattern '{pattern}'")
        return files
    
    def delete_directory(self, directory_path: Union[str, Path], 
                        force: bool = False) -> bool:
        """
        Delete a directory and optionally all its contents.
        
        Args:
            directory_path: Directory to delete
            force: If True, delete directory even if not empty
            
        Returns:
            True if deletion was successful, False otherwise
        """
        path = Path(directory_path)
        
        if not path.exists():
            logger.warning(f"Directory does not exist: {path}")
            return False
        
        try:
            if force:
                shutil.rmtree(path)
                logger.info(f"Force deleted directory: {path}")
            else:
                path.rmdir()
                logger.info(f"Deleted empty directory: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete directory {path}: {e}")
            return False
    
    def copy_directory(self, source: Union[str, Path], 
                      destination: Union[str, Path], 
                      overwrite: bool = False) -> bool:
        """
        Copy a directory and its contents.
        
        Args:
            source: Source directory path
            destination: Destination directory path
            overwrite: Overwrite destination if it exists
            
        Returns:
            True if copy was successful, False otherwise
        """
        src_path = Path(source)
        dst_path = Path(destination)
        
        if not src_path.exists():
            logger.error(f"Source directory does not exist: {src_path}")
            return False
        
        if dst_path.exists() and not overwrite:
            logger.error(f"Destination already exists: {dst_path}")
            return False
        
        try:
            if dst_path.exists() and overwrite:
                shutil.rmtree(dst_path)
            
            shutil.copytree(src_path, dst_path)
            logger.info(f"Copied directory from {src_path} to {dst_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy directory: {e}")
            return False
    
    # ==================== File Operations ====================
    
    def read_file(self, file_path: Union[str, Path], 
                 mode: str = "r", encoding: str = "utf-8") -> Union[str, bytes]:
        """
        Read content from a file.
        
        Args:
            file_path: Path to the file
            mode: Read mode ('r' for text, 'rb' for binary)
            encoding: Text encoding (only for text mode)
            
        Returns:
            File content as string or bytes
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            if 'b' in mode:
                with open(path, mode) as f:
                    content = f.read()
            else:
                with open(path, mode, encoding=encoding) as f:
                    content = f.read()
            
            logger.debug(f"Read file: {path} ({len(content)} bytes/chars)")
            return content
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            raise IOError(f"Failed to read file {path}: {e}")
    
    def write_file(self, file_path: Union[str, Path], 
                  content: Union[str, bytes], 
                  mode: str = "w", encoding: str = "utf-8") -> bool:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file
            content: Content to write
            mode: Write mode ('w' for text, 'wb' for binary)
            encoding: Text encoding (only for text mode)
            
        Returns:
            True if write was successful, False otherwise
        """
        path = Path(file_path)
        
        # Ensure parent directory exists
        self.ensure_directory_exists(path.parent)
        
        try:
            if isinstance(content, bytes) and 'b' not in mode:
                mode = 'wb'
            elif isinstance(content, str) and 'b' in mode:
                mode = 'w'
            
            if 'b' in mode:
                with open(path, mode) as f:
                    f.write(content)
            else:
                with open(path, mode, encoding=encoding) as f:
                    f.write(content)
            
            logger.debug(f"Wrote file: {path} ({len(content)} bytes/chars)")
            return True
        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            return False
    
    def append_to_file(self, file_path: Union[str, Path], 
                      content: Union[str, bytes], 
                      encoding: str = "utf-8") -> bool:
        """
        Append content to a file.
        
        Args:
            file_path: Path to the file
            content: Content to append
            encoding: Text encoding
            
        Returns:
            True if append was successful, False otherwise
        """
        path = Path(file_path)
        
        # Ensure parent directory exists
        self.ensure_directory_exists(path.parent)
        
        try:
            if isinstance(content, bytes):
                with open(path, 'ab') as f:
                    f.write(content)
            else:
                with open(path, 'a', encoding=encoding) as f:
                    f.write(content)
            
            logger.debug(f"Appended to file: {path} ({len(content)} bytes/chars)")
            return True
        except Exception as e:
            logger.error(f"Failed to append to file {path}: {e}")
            return False
    
    def delete_file(self, file_path: Union[str, Path]) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if deletion was successful, False otherwise
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"File does not exist: {path}")
            return False
        
        try:
            path.unlink()
            logger.info(f"Deleted file: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            return False
    
    def copy_file(self, source: Union[str, Path], 
                 destination: Union[str, Path], 
                 overwrite: bool = False) -> bool:
        """
        Copy a file.
        
        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Overwrite destination if it exists
            
        Returns:
            True if copy was successful, False otherwise
        """
        src_path = Path(source)
        dst_path = Path(destination)
        
        if not src_path.exists():
            logger.error(f"Source file does not exist: {src_path}")
            return False
        
        if dst_path.exists() and not overwrite:
            logger.error(f"Destination already exists: {dst_path}")
            return False
        
        try:
            # Ensure destination directory exists
            self.ensure_directory_exists(dst_path.parent)
            
            shutil.copy2(src_path, dst_path)
            logger.info(f"Copied file from {src_path} to {dst_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy file: {e}")
            return False
    
    def move_file(self, source: Union[str, Path], 
                 destination: Union[str, Path], 
                 overwrite: bool = False) -> bool:
        """
        Move/rename a file.
        
        Args:
            source: Source file path
            destination: Destination file path
            overwrite: Overwrite destination if it exists
            
        Returns:
            True if move was successful, False otherwise
        """
        src_path = Path(source)
        dst_path = Path(destination)
        
        if not src_path.exists():
            logger.error(f"Source file does not exist: {src_path}")
            return False
        
        if dst_path.exists() and not overwrite:
            logger.error(f"Destination already exists: {dst_path}")
            return False
        
        try:
            # Ensure destination directory exists
            self.ensure_directory_exists(dst_path.parent)
            
            if dst_path.exists() and overwrite:
                dst_path.unlink()
            
            shutil.move(str(src_path), str(dst_path))
            logger.info(f"Moved file from {src_path} to {dst_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            return False
    
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get detailed information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        path = Path(file_path)
        
        if not path.exists():
            return {"error": "File does not exist"}
        
        try:
            stat = path.stat()
            return {
                "path": str(path.absolute()),
                "name": path.name,
                "stem": path.stem,
                "suffix": path.suffix,
                "parent": str(path.parent),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "is_file": path.is_file(),
                "is_dir": path.is_dir(),
                "is_symlink": path.is_symlink(),
                "exists": path.exists()
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {path}: {e}")
            return {"error": str(e)}
    
    # ==================== File Format Operations ====================
    
    def read_json(self, file_path: Union[str, Path]) -> Union[Dict, List]:
        """
        Read JSON data from a file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed JSON data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        content = self.read_file(file_path, mode='r')
        return json.loads(content)
    
    def write_json(self, file_path: Union[str, Path], 
                  data: Union[Dict, List], 
                  indent: int = 2, sort_keys: bool = False) -> bool:
        """
        Write data to a JSON file.
        
        Args:
            file_path: Path to JSON file
            data: Data to write (must be JSON serializable)
            indent: Indentation level
            sort_keys: Whether to sort dictionary keys
            
        Returns:
            True if write was successful, False otherwise
        """
        try:
            json_str = json.dumps(data, indent=indent, sort_keys=sort_keys)
            return self.write_file(file_path, json_str)
        except Exception as e:
            logger.error(f"Failed to write JSON to {file_path}: {e}")
            return False
    
    def read_yaml(self, file_path: Union[str, Path]) -> Union[Dict, List]:
        """
        Read YAML data from a file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Parsed YAML data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        content = self.read_file(file_path, mode='r')
        return yaml.safe_load(content)
    
    def write_yaml(self, file_path: Union[str, Path], 
                  data: Union[Dict, List], 
                  default_flow_style: bool = False) -> bool:
        """
        Write data to a YAML file.
        
        Args:
            file_path: Path to YAML file
            data: Data to write
            default_flow_style: YAML flow style
            
        Returns:
            True if write was successful, False otherwise
        """
        try:
            yaml_str = yaml.dump(data, default_flow_style=default_flow_style)
            return self.write_file(file_path, yaml_str)
        except Exception as e:
            logger.error(f"Failed to write YAML to {file_path}: {e}")
            return False
    
    def read_pickle(self, file_path: Union[str, Path]) -> Any:
        """
        Read pickled data from a file.
        
        Args:
            file_path: Path to pickle file
            
        Returns:
            Unpickled data
            
        Warning: Only unpickle data from trusted sources!
        """
        content = self.read_file(file_path, mode='rb')
        return pickle.loads(content)
    
    def write_pickle(self, file_path: Union[str, Path], data: Any) -> bool:
        """
        Write data to a pickle file.
        
        Args:
            file_path: Path to pickle file
            data: Data to pickle
            
        Returns:
            True if write was successful, False otherwise
        """
        try:
            pickle_data = pickle.dumps(data)
            return self.write_file(file_path, pickle_data, mode='wb')
        except Exception as e:
            logger.error(f"Failed to write pickle to {file_path}: {e}")
            return False
    
    # ==================== Search and Pattern Operations ====================
    
    def find_files(self, directory: Union[str, Path], 
                  pattern: str = "*", 
                  recursive: bool = True) -> List[Path]:
        """
        Find files matching a pattern.
        
        Args:
            directory: Directory to search in
            pattern: Glob pattern or regex-like pattern
            recursive: Whether to search recursively
            
        Returns:
            List of matching file paths
        """
        return self.list_directory(directory, pattern, recursive)
    
    def find_files_by_extension(self, directory: Union[str, Path], 
                               extensions: List[str], 
                               recursive: bool = True) -> List[Path]:
        """
        Find files with specific extensions.
        
        Args:
            directory: Directory to search in
            extensions: List of extensions (e.g., ['.py', '.txt'])
            recursive: Whether to search recursively
            
        Returns:
            List of matching file paths
        """
        path = Path(directory)
        if not path.exists():
            return []
        
        files = []
        for ext in extensions:
            pattern = f"**/*{ext}" if recursive else f"*{ext}"
            files.extend(self.find_files(directory, pattern, recursive))
        
        return list(set(files))  # Remove duplicates
    
    def search_in_files(self, directory: Union[str, Path], 
                       search_text: str, 
                       file_pattern: str = "*", 
                       case_sensitive: bool = False, 
                       recursive: bool = True) -> Dict[Path, List[int]]:
        """
        Search for text in files.
        
        Args:
            directory: Directory to search in
            search_text: Text to search for
            file_pattern: Pattern for files to search in
            case_sensitive: Whether search is case sensitive
            recursive: Whether to search recursively
            
        Returns:
            Dictionary mapping file paths to line numbers where text was found
        """
        files = self.find_files(directory, file_pattern, recursive)
        results = {}
        
        if not case_sensitive:
            search_text = search_text.lower()
        
        for file_path in files:
            if not file_path.is_file():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                matching_lines = []
                for i, line in enumerate(lines, 1):
                    line_to_check = line if case_sensitive else line.lower()
                    if search_text in line_to_check:
                        matching_lines.append(i)
                
                if matching_lines:
                    results[file_path] = matching_lines
                    
            except Exception as e:
                logger.warning(f"Could not read file {file_path}: {e}")
                continue
        
        return results
    
    # ==================== Backup and Archive Operations ====================
    
    def create_backup(self, source: Union[str, Path], 
                     backup_dir: Optional[Union[str, Path]] = None, 
                     timestamp_format: str = "%Y%m%d_%H%M%S") -> Optional[Path]:
        """
        Create a backup of a file or directory.
        
        Args:
            source: File or directory to backup
            backup_dir: Directory to store backup (default: source_parent/backups)
            timestamp_format: Format for timestamp in backup name
            
        Returns:
            Path to backup file, or None if failed
        """
        source_path = Path(source)
        
        if not source_path.exists():
            logger.error(f"Source does not exist: {source_path}")
            return None
        
        if backup_dir is None:
            backup_dir = source_path.parent / "backups"
        
        backup_path = Path(backup_dir)
        self.ensure_directory_exists(backup_path)
        
        timestamp = datetime.now().strftime(timestamp_format)
        backup_name = f"{source_path.name}_{timestamp}"
        
        if source_path.is_file():
            backup_file = backup_path / backup_name
            if self.copy_file(source_path, backup_file, overwrite=True):
                logger.info(f"Created file backup: {backup_file}")
                return backup_file
        else:
            backup_file = backup_path / f"{backup_name}.zip"
            if self.create_zip_archive(source_path, backup_file):
                logger.info(f"Created directory backup: {backup_file}")
                return backup_file
        
        return None
    
    def create_zip_archive(self, source: Union[str, Path], 
                          destination: Union[str, Path], 
                          compression: int = zipfile.ZIP_DEFLATED) -> bool:
        """
        Create a ZIP archive of a file or directory.
        
        Args:
            source: File or directory to archive
            destination: Path for the ZIP file
            compression: Compression level
            
        Returns:
            True if archive creation was successful, False otherwise
        """
        source_path = Path(source)
        dest_path = Path(destination)
        
        if not source_path.exists():
            logger.error(f"Source does not exist: {source_path}")
            return False
        
        try:
            self.ensure_directory_exists(dest_path.parent)
            
            with zipfile.ZipFile(dest_path, 'w', compression) as zipf:
                if source_path.is_file():
                    zipf.write(source_path, source_path.name)
                else:
                    for file_path in source_path.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(source_path)
                            zipf.write(file_path, arcname)
            
            logger.info(f"Created ZIP archive: {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create ZIP archive: {e}")
            return False
    
    def extract_zip_archive(self, zip_file: Union[str, Path], 
                           destination: Union[str, Path], 
                           overwrite: bool = False) -> bool:
        """
        Extract a ZIP archive.
        
        Args:
            zip_file: Path to ZIP file
            destination: Directory to extract to
            overwrite: Overwrite existing files
            
        Returns:
            True if extraction was successful, False otherwise
        """
        zip_path = Path(zip_file)
        dest_path = Path(destination)
        
        if not zip_path.exists():
            logger.error(f"ZIP file does not exist: {zip_path}")
            return False
        
        if dest_path.exists() and not overwrite:
            logger.error(f"Destination already exists: {dest_path}")
            return False
        
        try:
            self.ensure_directory_exists(dest_path)
            
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(dest_path)
            
            logger.info(f"Extracted ZIP archive to: {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to extract ZIP archive: {e}")
            return False
    
    # ==================== File Validation and Integrity ====================
    
    def calculate_hash(self, file_path: Union[str, Path], 
                      algorithm: str = "sha256") -> Optional[str]:
        """
        Calculate hash of a file.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm (md5, sha1, sha256, sha512)
            
        Returns:
            Hexadecimal hash string, or None if failed
        """
        path = Path(file_path)
        
        if not path.exists() or not path.is_file():
            logger.error(f"File does not exist or is not a file: {path}")
            return None
        
        try:
            hash_func = hashlib.new(algorithm)
            
            with open(path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_func.update(chunk)
            
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {path}: {e}")
            return None
    
    def verify_file_integrity(self, file_path: Union[str, Path], 
                             expected_hash: str, 
                             algorithm: str = "sha256") -> bool:
        """
        Verify file integrity by comparing with expected hash.
        
        Args:
            file_path: Path to the file
            expected_hash: Expected hash value
            algorithm: Hash algorithm used
            
        Returns:
            True if hash matches, False otherwise
        """
        actual_hash = self.calculate_hash(file_path, algorithm)
        if actual_hash is None:
            return False
        
        return actual_hash.lower() == expected_hash.lower()
    
    def compare_files(self, file1: Union[str, Path], 
                     file2: Union[str, Path], 
                     binary: bool = False) -> bool:
        """
        Compare two files for equality.
        
        Args:
            file1: First file path
            file2: Second file path
            binary: Whether to compare as binary files
            
        Returns:
            True if files are identical, False otherwise
        """
        path1 = Path(file1)
        path2 = Path(file2)
        
        if not path1.exists() or not path2.exists():
            return False
        
        # Quick size check
        if path1.stat().st_size != path2.stat().st_size:
            return False
        
        try:
            if binary:
                with open(path1, 'rb') as f1, open(path2, 'rb') as f2:
                    while True:
                        chunk1 = f1.read(4096)
                        chunk2 = f2.read(4096)
                        
                        if chunk1 != chunk2:
                            return False
                        
                        if not chunk1:  # Both files ended
                            break
            else:
                content1 = self.read_file(path1, mode='r')
                content2 = self.read_file(path2, mode='r')
                return content1 == content2
            
            return True
        except Exception as e:
            logger.error(f"Failed to compare files: {e}")
            return False
    
    # ==================== Utility Methods ====================
    
    def get_file_size(self, file_path: Union[str, Path], 
                     human_readable: bool = False) -> Union[int, str]:
        """
        Get file size in bytes or human-readable format.
        
        Args:
            file_path: Path to the file
            human_readable: Return human-readable string (e.g., "1.5 MB")
            
        Returns:
            File size as integer or formatted string
        """
        path = Path(file_path)
        
        if not path.exists() or not path.is_file():
            return 0 if not human_readable else "0 B"
        
        size = path.stat().st_size
        
        if not human_readable:
            return size
        
        # Convert to human-readable format
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        
        return f"{size:.2f} PB"
    
    def get_directory_size(self, directory_path: Union[str, Path], 
                          human_readable: bool = False) -> Union[int, str]:
        """
        Get total size of a directory and all its contents.
        
        Args:
            directory_path: Path to the directory
            human_readable: Return human-readable string
            
        Returns:
            Total size as integer or formatted string
        """
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            return 0 if not human_readable else "0 B"
        
        total_size = 0
        for file_path in path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        if not human_readable:
            return total_size
        
        # Convert to human-readable format
        size = total_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        
        return f"{size:.2f} PB"
    
    def count_files(self, directory_path: Union[str, Path], 
                   recursive: bool = True) -> int:
        """
        Count files in a directory.
        
        Args:
            directory_path: Path to the directory
            recursive: Count files in subdirectories
            
        Returns:
            Number of files
        """
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            return 0
        
        if recursive:
            return sum(1 for file_path in path.rglob('*') if file_path.is_file())
        else:
            return sum(1 for file_path in path.iterdir() if file_path.is_file())
    
    def get_temp_file(self, suffix: str = "", prefix: str = "tmp_") -> Path:
        """
        Create a temporary file.
        
        Args:
            suffix: File suffix/extension
            prefix: File prefix
            
        Returns:
            Path to temporary file
        """
        temp_file = tempfile.NamedTemporaryFile(
            suffix=suffix, 
            prefix=prefix, 
            delete=False
        )
        temp_file.close()
        return Path(temp_file.name)
    
    def get_temp_directory(self, prefix: str = "tmp_") -> Path:
        """
        Create a temporary directory.
        
        Args:
            prefix: Directory prefix
            
        Returns:
            Path to temporary directory
        """
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        return Path(temp_dir)
    
    def cleanup_temp_resources(self, path: Union[str, Path]) -> bool:
        """
        Clean up temporary files or directories.
        
        Args:
            path: Path to temporary resource
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        path_obj = Path(path)
        
        if not path_obj.exists():
            return True
        
        try:
            if path_obj.is_file():
                path_obj.unlink()
            else:
                shutil.rmtree(path_obj)
            
            logger.debug(f"Cleaned up temporary resource: {path_obj}")
            return True
        except Exception as e:
            logger.warning(f"Failed to clean up temporary resource {path_obj}: {e}")
            return False
    
    # ==================== Project-specific Methods ====================
    
    def create_project_structure(self, project_path: Union[str, Path], 
                               structure: Dict[str, Any]) -> bool:
        """
        Create a project directory structure from a template.
        
        Args:
            project_path: Root path for the project
            structure: Dictionary defining the structure
                Example: {
                    "src": {
                        "__init__.py": "",
                        "main.py": "# Main file content",
                        "utils": {
                            "__init__.py": "",
                            "helpers.py": "# Helper functions"
                        }
                    },
                    "tests": {},
                    "README.md": "# Project README",
                    "requirements.txt": ""
                }
            
        Returns:
            True if structure creation was successful, False otherwise
        """
        project_root = Path(project_path)
        
        def create_structure(current_path: Path, current_structure: Dict[str, Any]):
            for name, content in current_structure.items():
                item_path = current_path / name
                
                if isinstance(content, dict):
                    # It's a directory
                    self.ensure_directory_exists(item_path)
                    create_structure(item_path, content)
                else:
                    # It's a file
                    self.ensure_directory_exists(item_path.parent)
                    self.write_file(item_path, str(content))
        
        try:
            self.ensure_directory_exists(project_root)
            create_structure(project_root, structure)
            logger.info(f"Created project structure at: {project_root}")
            return True
        except Exception as e:
            logger.error(f"Failed to create project structure: {e}")
            return False
    
    def merge_directories(self, source: Union[str, Path], 
                         destination: Union[str, Path], 
                         overwrite: bool = False) -> bool:
        """
        Merge contents of one directory into another.
        
        Args:
            source: Source directory
            destination: Destination directory
            overwrite: Overwrite existing files
            
        Returns:
            True if merge was successful, False otherwise
        """
        src_path = Path(source)
        dst_path = Path(destination)
        
        if not src_path.exists() or not src_path.is_dir():
            logger.error(f"Source directory does not exist: {src_path}")
            return False
        
        self.ensure_directory_exists(dst_path)
        
        try:
            for item in src_path.rglob('*'):
                if item.is_file():
                    rel_path = item.relative_to(src_path)
                    dst_item = dst_path / rel_path
                    
                    if not dst_item.exists() or overwrite:
                        self.ensure_directory_exists(dst_item.parent)
                        self.copy_file(item, dst_item, overwrite=True)
            
            logger.info(f"Merged directory {src_path} into {dst_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to merge directories: {e}")
            return False


# ==================== Helper Functions ====================

def get_file_manager(base_path: Optional[str] = None) -> FileManager:
    """
    Factory function to get a FileManager instance.
    
    Args:
        base_path: Base directory for file operations
        
    Returns:
        FileManager instance
    """
    return FileManager(base_path)


def validate_file_path(file_path: Union[str, Path], 
                      must_exist: bool = False, 
                      must_be_file: bool = False) -> bool:
    """
    Validate a file path.
    
    Args:
        file_path: Path to validate
        must_exist: Path must exist
        must_be_file: Path must be a file (not directory)
        
    Returns:
        True if path is valid, False otherwise
    """
    path = Path(file_path)
    
    if must_exist and not path.exists():
        return False
    
    if must_be_file and not path.is_file():
        return False
    
    # Check if path is absolute and has valid characters
    try:
        path.resolve()
        return True
    except Exception:
        return False


def sanitize_filename(filename: str, 
                     replace_with: str = "_", 
                     max_length: int = 255) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Original filename
        replace_with: Character to replace invalid characters with
        max_length: Maximum length of filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters for most filesystems
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, replace_with)
    
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Trim to max length
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename.strip()


# ==================== Example Usage ====================

if __name__ == "__main__":
    # Example usage of FileManager
    fm = FileManager()
    
    # Create a test directory
    test_dir = fm.base_path / "test_files"
    fm.ensure_directory_exists(test_dir)
    
    # Write a test file
    test_file = test_dir / "test.txt"
    fm.write_file(test_file, "Hello, FileManager!")
    
    # Read the file
    content = fm.read_file(test_file)
    print(f"File content: {content}")
    
    # Get file info
    info = fm.get_file_info(test_file)
    print(f"File info: {info}")
    
    # Clean up
    fm.delete_file(test_file)
    fm.delete_directory(test_dir)
    
    print("FileManager example completed successfully!")