"""
File storage layer for audio recordings.
Handles disk operations with proper directory structure.
"""

from pathlib import Path
import os
import shutil
from typing import Optional, Tuple


class StorageManager:
    """Manages local disk storage for audio files."""
    
    def __init__(self, root_dir: str = "storage"):
        """
        Initialize storage manager.
        
        Parameters
        ----------
        root_dir : str
            Root storage directory (will be created if needed)
        """
        self.root_dir = Path(root_dir)
        self.audio_dir = self.root_dir / "audio"
        
        # Create directories
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
    
    def get_user_dir(self, user_id: str) -> Path:
        """Get user's storage directory (creates if needed)."""
        user_dir = self.audio_dir / user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def save(
        self,
        user_id: str,
        file_id: str,
        file_content: bytes,
        extension: str,
    ) -> str:
        """
        Save file to storage.
        
        Parameters
        ----------
        user_id : str
            User ID
        file_id : str
            Unique file ID (UUID)
        file_content : bytes
            File content
        extension : str
            File extension without dot (e.g., 'wav', 'mp3')
        
        Returns
        -------
        str
            Relative path from storage root (e.g., 'audio/user123/abc-def.wav')
        """
        user_dir = self.get_user_dir(user_id)
        filename = f"{file_id}.{extension}"
        filepath = user_dir / filename
        
        # Write file
        with open(filepath, "wb") as f:
            f.write(file_content)
        
        # Return relative path
        relative_path = filepath.relative_to(self.root_dir).as_posix()
        return relative_path
    
    def open_path(self, relative_path: str) -> Path:
        """
        Get absolute path from relative storage path.
        
        Parameters
        ----------
        relative_path : str
            Relative path stored in database (e.g., 'audio/user123/abc-def.wav')
        
        Returns
        -------
        Path
            Absolute path to file
        
        Raises
        ------
        FileNotFoundError
            If file doesn't exist
        """
        full_path = self.root_dir / relative_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        
        # Security: ensure path is within root_dir
        try:
            full_path.relative_to(self.root_dir)
        except ValueError:
            raise ValueError(f"Invalid path: {relative_path}")
        
        return full_path
    
    def delete(self, relative_path: str) -> None:
        """
        Delete file from storage.
        
        Parameters
        ----------
        relative_path : str
            Relative path stored in database
        """
        try:
            full_path = self.open_path(relative_path)
            full_path.unlink()
        except (FileNotFoundError, ValueError):
            # Silently ignore if file doesn't exist
            pass
    
    def get_size(self, relative_path: str) -> int:
        """
        Get file size in bytes.
        
        Parameters
        ----------
        relative_path : str
            Relative path stored in database
        
        Returns
        -------
        int
            File size in bytes
        """
        full_path = self.open_path(relative_path)
        return full_path.stat().st_size
    
    def cleanup_user_dir(self, user_id: str) -> None:
        """
        Delete all files for a user (e.g., when account is deleted).
        
        Parameters
        ----------
        user_id : str
            User ID
        """
        user_dir = self.audio_dir / user_id
        if user_dir.exists():
            shutil.rmtree(user_dir)


# Global storage instance
_storage: Optional[StorageManager] = None


def get_storage() -> StorageManager:
    """Get or create global storage manager."""
    global _storage
    if _storage is None:
        _storage = StorageManager(root_dir="storage")
    return _storage


def set_storage(storage: StorageManager) -> None:
    """Set global storage manager (useful for testing)."""
    global _storage
    _storage = storage
