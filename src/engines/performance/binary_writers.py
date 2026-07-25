"""Dedicated atomic persistence of already-produced binary report artifacts."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

__all__ = ["AtomicBinaryReportWriter"]


class AtomicBinaryReportWriter:
    """Write exact binary artifacts atomically without knowing their format."""

    def write(self, content: bytes, destination: Path) -> None:
        """Persist exact bytes through a temporary sibling and atomic replacement.

        The writer creates missing parent directories, writes no replacement over
        the destination until the temporary file is complete, and removes the
        temporary file after success or a pre-replacement failure where practical.

        Args:
            content: Already-produced immutable binary artifact bytes.
            destination: Target file path for the supplied binary artifact.

        Raises:
            TypeError: If content is not bytes or destination is not a ``Path``.
            ValueError: If destination has no filename or identifies a directory.
            OSError: If the destination cannot be prepared, written, or replaced.
        """
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes.")
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
                mode="wb",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(content)
            os.replace(temporary_path, destination)
        except OSError as error:
            raise OSError(f"unable to write binary report to {destination}.") from error
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
