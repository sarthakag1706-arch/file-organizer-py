import os
import sys
import shutil
import logging
import argparse
from datetime import datetime

# ---------------------------------------------------------------------
# 1. Extension - Category mapping
# ---------------------------------------------------------------------
CATEGORY_MAP = {
    "Images":    [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".xls", ".ppt",
                  ".pptx", ".csv", ".odt"],
    "Videos":    [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
    "Audio":     [".mp3", ".wav", ".aac", ".flac", ".ogg", ".wma"],
    "Archives":  [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code":      [".py", ".java", ".c", ".cpp", ".js", ".html", ".css",
                  ".json", ".xml", ".sql"],
}
DEFAULT_CATEGORY = "Others"

# ---------------------------------------------------------------------
# 2. Logging configuration
# ---------------------------------------------------------------------
def setup_logger(log_path: str) -> logging.Logger:
    logger = logging.getLogger("FileOrganizer")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


# ---------------------------------------------------------------------
# 3. Core class
# ---------------------------------------------------------------------
class FileOrganizer:
    """Scans a directory and arranges files into category folders
    based on their extensions."""

    def __init__(self, source_dir: str, copy_mode: bool = False,
                 dry_run: bool = False, logger: logging.Logger = None):
        self.source_dir = os.path.abspath(source_dir)
        self.copy_mode = copy_mode
        self.dry_run = dry_run
        self.logger = logger or logging.getLogger("FileOrganizer")
        self.summary = {category: 0 for category in CATEGORY_MAP}
        self.summary[DEFAULT_CATEGORY] = 0

    def classify_extension(self, extension: str) -> str:
        """Return the category name for a given file extension."""
        extension = extension.lower()
        for category, ext_list in CATEGORY_MAP.items():
            if extension in ext_list:
                return category
        return DEFAULT_CATEGORY

    def ensure_folder(self, folder_path: str) -> None:
        if not os.path.exists(folder_path):
            if not self.dry_run:
                os.makedirs(folder_path)
            self.logger.info(f"Created folder: {folder_path}")

    def organize(self) -> dict:
        """Main routine: scan the source directory and sort files."""
        if not os.path.isdir(self.source_dir):
            raise NotADirectoryError(f"{self.source_dir} is not a valid directory")

        self.logger.info(f"Scanning directory: {self.source_dir}")
        entries = [e for e in os.listdir(self.source_dir)
                   if os.path.isfile(os.path.join(self.source_dir, e))]

        for filename in entries:
            source_path = os.path.join(self.source_dir, filename)
            _, extension = os.path.splitext(filename)

            if extension == "":
                category = DEFAULT_CATEGORY
            else:
                category = self.classify_extension(extension)

            target_folder = os.path.join(self.source_dir, category)
            self.ensure_folder(target_folder)

            target_path = os.path.join(target_folder, filename)
            target_path = self._resolve_conflict(target_path)

            if not self.dry_run:
                if self.copy_mode:
                    shutil.copy2(source_path, target_path)
                else:
                    shutil.move(source_path, target_path)

            self.summary[category] += 1
            action = "Copied" if self.copy_mode else "Moved"
            self.logger.info(f"{action}: {filename}  ->  {category}/")

        return self.summary

    @staticmethod
    def _resolve_conflict(target_path: str) -> str:
        """Avoid overwriting an existing file by appending a counter."""
        if not os.path.exists(target_path):
            return target_path
        base, ext = os.path.splitext(target_path)
        counter = 1
        new_path = f"{base}_{counter}{ext}"
        while os.path.exists(new_path):
            counter += 1
            new_path = f"{base}_{counter}{ext}"
        return new_path

    def print_summary(self) -> None:
        print("\n----- File Organization Summary -----")
        total = 0
        for category, count in self.summary.items():
            if count > 0:
                print(f"{category:<12}: {count} file(s)")
                total += count
        print(f"{'Total':<12}: {total} file(s)")
        print("--------------------------------------\n")


# ---------------------------------------------------------------------
# 4. Command-line interface
# ---------------------------------------------------------------------
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Identify and arrange files in a folder based on their extension.")
    parser.add_argument("directory", help="Path of the directory to organize")
    parser.add_argument("--copy", action="store_true",
                         help="Copy files instead of moving them")
    parser.add_argument("--dry-run", action="store_true",
                         help="Preview actions without moving/copying any file")
    parser.add_argument("--log", default="organizer_log.txt",
                         help="Path of the log file")
    return parser.parse_args()


def main():
    args = parse_arguments()
    logger = setup_logger(args.log)
    logger.info("===== File Organizer session started: "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")

    organizer = FileOrganizer(
        source_dir=args.directory,
        copy_mode=args.copy,
        dry_run=args.dry_run,
        logger=logger,
    )

    try:
        organizer.organize()
        organizer.print_summary()
    except NotADirectoryError as err:
        logger.error(str(err))
        sys.exit(1)

    logger.info("===== File Organizer session ended =====")


if __name__ == "__main__":
    main()
