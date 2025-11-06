"""
Automatic cleanup service for old order files.
Deletes JSON files older than X days from processed and cancelled folders.
"""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread

from app.config import COMENZI_PROCESATE, COMENZI_ANULATE, CLEANUP_FILES_DAYS_OLD, CLEANUP_FILES_INTERVAL
from app.logging_config import get_logger

logger = get_logger("cleanup_service")


class CleanupService:
    """
    Service for automatic cleanup of old order files.
    Runs periodically to delete files older than N days.
    """
    
    def __init__(self):
        """Initialize CleanupService."""
        self.running = True
        self.interval = CLEANUP_FILES_INTERVAL
        self.days_old = CLEANUP_FILES_DAYS_OLD
        self.check_interval = 60  # Check every 60 seconds for shutdown signal
        
        logger.info(f"CleanupService initialized (interval: {self.interval/3600:.0f}h, keep: {self.days_old} days)")
    
    def cleanup_old_files(self):
        """
        Delete JSON files older than X days from processed/cancelled order folders.
        """
        try:
            logger.info("=" * 80)
            logger.info(f"START File cleanup (older than {self.days_old} days)")
            logger.info("=" * 80)
            
            cutoff_date = datetime.now() - timedelta(days=self.days_old)
            total_deleted = 0
            
            # Process folders
            folders = {
                "procesate": COMENZI_PROCESATE,
                "anulate": COMENZI_ANULATE
            }
            
            for folder_name, folder_path in folders.items():
                if not folder_path.exists():
                    logger.debug(f"Folder {folder_name} doesn't exist, skipping")
                    continue
                
                deleted_count = 0
                
                # Process files in folder
                for filename in os.listdir(folder_path):
                    if not filename.endswith('.json'):
                        continue
                    
                    filepath = folder_path / filename
                    
                    try:
                        # Check file modification date
                        file_modified_time = datetime.fromtimestamp(filepath.stat().st_mtime)
                        
                        if file_modified_time < cutoff_date:
                            # Delete file
                            os.remove(filepath)
                            deleted_count += 1
                            logger.debug(f"Deleted: {filename} (modified: {file_modified_time.strftime('%Y-%m-%d %H:%M')})")
                    
                    except Exception as e:
                        logger.error(f"Error deleting file {filename}: {e}")
                
                if deleted_count > 0:
                    logger.info(f"Folder '{folder_name}': {deleted_count} files deleted")
                else:
                    logger.info(f"Folder '{folder_name}': No old files to delete")
                
                total_deleted += deleted_count
            
            logger.info("=" * 80)
            if total_deleted > 0:
                logger.info(f"Cleanup completed: {total_deleted} files deleted total")
            else:
                logger.info("Cleanup completed: No old files found")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error during file cleanup: {e}", exc_info=True)
    
    def run_cleanup_loop(self):
        """
        Main loop that runs cleanup periodically.
        Uses short sleep intervals for graceful shutdown.
        """
        logger.info("=" * 80)
        logger.info("START Cleanup Service")
        logger.info(f"Cleanup interval: {self.interval/3600:.0f} hours")
        logger.info(f"History retention: {self.days_old} days")
        logger.info("=" * 80)
        
        # Run cleanup at startup
        self.cleanup_old_files()
        
        # Periodic loop with short sleep intervals for graceful shutdown
        elapsed_time = 0
        while self.running:
            try:
                # Sleep in short intervals (60 seconds) to allow graceful shutdown
                # This prevents the worker from being killed due to timeout
                if elapsed_time == 0:
                    logger.info(f"Next cleanup in {self.interval/3600:.0f} hours...")
                
                time.sleep(self.check_interval)
                elapsed_time += self.check_interval
                
                # Check if it's time to run cleanup
                if elapsed_time >= self.interval:
                    if self.running:
                        self.cleanup_old_files()
                    elapsed_time = 0  # Reset counter
                    
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                # Continue running even if an error occurs
                time.sleep(60)  # Wait 1 minute before retry
        
        logger.info("=" * 80)
        logger.info("STOP Cleanup Service")
        logger.info("=" * 80)
    
    def start(self):
        """Start cleanup service."""
        try:
            self.run_cleanup_loop()
        except KeyboardInterrupt:
            logger.info("\nKeyboardInterrupt received - stopping...")
        finally:
            self.running = False
    
    def stop(self):
        """Stop cleanup service."""
        logger.info("Stopping Cleanup Service...")
        self.running = False


def start_cleanup_service():
    """
    Helper function to start cleanup service in a separate thread.
    """
    cleanup = CleanupService()
    cleanup.start()
