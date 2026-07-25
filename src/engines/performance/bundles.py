"""Deterministic in-memory ZIP bundles for already-produced report artifacts."""

from collections.abc import Mapping
from io import BytesIO
from pathlib import PurePosixPath, PureWindowsPath
from zipfile import ZIP_STORED, ZipFile, ZipInfo

__all__ = ["StandardReportBundleBuilder"]

_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_ZIP_FILE_ATTRIBUTES = 0o100644 << 16


class StandardReportBundleBuilder:
    """Build stable ZIP bytes from safe named text or binary report artifacts."""

    def build(self, artifacts: Mapping[str, str | bytes]) -> bytes:
        """Return one deterministic in-memory ZIP archive.

        Text artifacts are encoded as UTF-8 and binary artifacts are copied
        exactly. Entries use sorted normalized names, fixed metadata, and stored
        compression so valid input produces reproducible archive bytes.

        Args:
            artifacts: Safe relative artifact names mapped to text or bytes.

        Returns:
            Complete ZIP bytes containing each supplied artifact exactly once.

        Raises:
            TypeError: If artifacts is not a mapping or an artifact value is invalid.
            ValueError: If an artifact name is unsafe, empty, or duplicates another.
        """
        if not isinstance(artifacts, Mapping):
            raise TypeError("artifacts must be a Mapping.")

        entries = _normalize_entries(artifacts)
        output = BytesIO()
        with ZipFile(output, mode="w", compression=ZIP_STORED) as archive:
            for filename, content in entries:
                archive.writestr(_zip_info(filename), content)
        return output.getvalue()


def _normalize_entries(
    artifacts: Mapping[str, str | bytes],
) -> tuple[tuple[str, bytes], ...]:
    """Validate, encode, normalize, and deterministically order artifact entries."""
    normalized_entries: list[tuple[str, bytes]] = []
    normalized_names: set[str] = set()
    for name, content in artifacts.items():
        normalized_name = _normalize_filename(name)
        if normalized_name in normalized_names:
            raise ValueError("artifact names must be unique after normalization.")
        normalized_names.add(normalized_name)
        normalized_entries.append((normalized_name, _encode_content(content)))
    return tuple(sorted(normalized_entries, key=lambda entry: entry[0]))


def _normalize_filename(name: object) -> str:
    """Return one safe slash-separated archive name or raise a clear error."""
    if not isinstance(name, str):
        raise TypeError("artifact names must be str values.")
    if not name.strip():
        raise ValueError("artifact names must not be empty.")
    if "\x00" in name:
        raise ValueError("artifact names must not contain null bytes.")

    normalized_input = name.replace("\\", "/")
    windows_path = PureWindowsPath(name)
    posix_path = PurePosixPath(normalized_input)
    if (
        normalized_input.endswith("/")
        or windows_path.is_absolute()
        or windows_path.drive
        or posix_path.is_absolute()
    ):
        raise ValueError("artifact names must identify safe relative files.")

    parts = tuple(part for part in posix_path.parts if part not in (".", ""))
    if not parts or any(part == ".." for part in parts):
        raise ValueError("artifact names must not contain parent traversal.")
    return "/".join(parts)


def _encode_content(content: object) -> bytes:
    """Return exact binary content or UTF-8 encoded text without transformation."""
    if isinstance(content, str):
        return content.encode("utf-8")
    if isinstance(content, bytes):
        return content
    raise TypeError("artifact content must be str or bytes.")


def _zip_info(filename: str) -> ZipInfo:
    """Return fixed, file-like ZIP metadata for one deterministic artifact entry."""
    info = ZipInfo(filename=filename, date_time=_ZIP_TIMESTAMP)
    info.compress_type = ZIP_STORED
    info.create_system = 3
    info.external_attr = _ZIP_FILE_ATTRIBUTES
    return info
