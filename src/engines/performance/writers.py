"""Dedicated UTF-8 text persistence for already-rendered report content."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

__all__ = ["TextReportWriter"]


class TextReportWriter:
    """Write exact rendered text atomically without knowing report semantics."""

    def write(self, content: str, destination: Path) -> None:
        """Persist ``content`` as UTF-8 text, creating parent directories.

        A temporary file in the destination directory is atomically replaced on
        success where the local filesystem supports ``os.replace``. Content is
        written with newline translation disabled, so supplied text is retained
        exactly, including an existing trailing newline.

        Args:
            content: Already-rendered text content to persist without changes.
            destination: Target file path for the supplied content.

        Raises:
            TypeError: If content is not text or destination is not a ``Path``.
            ValueError: If destination has no filename or identifies a directory.
            OSError: If the destination cannot be prepared, written, or replaced.
        """
        if not isinstance(content, str):
            raise TypeError("content must be a str.")
        if not isinstance(destination, Path):
            raise TypeError("destination must be a Path.")
        if not destination.name:
            raise ValueError("destination must include a filename.")

        temporary_path: Path | None = None
        try:
            if destination.exists() and destination.is_dir():
                raise ValueError("destination must identify a file.")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(content)
            os.replace(temporary_path, destination)
        except OSError as error:
            raise OSError(f"unable to write report to {destination}.") from error
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
