"""Contract tests for atomic persistence of already-produced binary artifacts."""

import ast
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from src.engines.performance import AtomicBinaryReportWriter, BinaryReportWriter


class AtomicBinaryReportWriterTests(TestCase):
    """Verify exact binary persistence without report or format dependencies."""

    def test_writes_empty_pdf_like_zip_like_and_large_binary_content(self) -> None:
        """Preserve every supplied byte, including empty and large artifacts."""
        with TemporaryDirectory() as directory:
            writer: BinaryReportWriter = AtomicBinaryReportWriter()
            cases = {
                "empty.bin": b"",
                "report.pdf": b"%PDF-1.7\x00\xff",
                "report.zip": b"PK\x03\x04\x00\xff",
                "large.bin": b"0123456789" * 100_000,
            }
            for filename, content in cases.items():
                destination = Path(directory) / "nested" / filename
                writer.write(content, destination)
                self.assertEqual(destination.read_bytes(), content)

    def test_overwrites_existing_destination_and_cleans_temporary_file(self) -> None:
        """Atomically replace an existing artifact without retaining temp siblings."""
        with TemporaryDirectory() as directory:
            destination = Path(directory) / "report.pdf"
            destination.write_bytes(b"old")

            AtomicBinaryReportWriter().write(b"new", destination)

            self.assertEqual(destination.read_bytes(), b"new")
            self.assertEqual(
                tuple(path.name for path in Path(directory).iterdir()),
                ("report.pdf",),
            )

    def test_pre_replacement_failure_preserves_destination_and_cleans_temp(self) -> None:
        """Keep existing bytes intact when writing the temporary replacement fails."""
        with TemporaryDirectory() as directory:
            destination = Path(directory) / "report.zip"
            destination.write_bytes(b"original")

            with patch(
                "src.engines.performance.binary_writers.NamedTemporaryFile",
                side_effect=_failing_temporary_file,
            ):
                with self.assertRaisesRegex(OSError, "unable to write binary report"):
                    AtomicBinaryReportWriter().write(b"replacement", destination)

            self.assertEqual(destination.read_bytes(), b"original")
            self.assertEqual(
                tuple(path.name for path in Path(directory).iterdir()),
                ("report.zip",),
            )

    def test_writer_rejects_intrinsic_misuse(self) -> None:
        """Require bytes and one explicit file-shaped destination path."""
        writer = AtomicBinaryReportWriter()
        with TemporaryDirectory() as directory:
            with self.assertRaises(TypeError):
                writer.write(bytearray(b"content"), Path(directory) / "report.bin")
            with self.assertRaises(TypeError):
                writer.write(b"content", "report.bin")
            with self.assertRaises(ValueError):
                writer.write(b"content", Path())
            with self.assertRaises(ValueError):
                writer.write(b"content", Path(directory))

    def test_writer_has_no_renderer_bundle_or_domain_dependencies(self) -> None:
        """Keep binary persistence independent from artifact production details."""
        with open(
            "src/engines/performance/binary_writers.py",
            encoding="utf-8",
        ) as source_file:
            tree = ast.parse(source_file.read())
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertEqual(imported_modules, {"pathlib", "tempfile"})


def _failing_temporary_file(*args, **kwargs):
    """Return a real temporary file wrapper whose binary writes always fail."""
    temporary_file = NamedTemporaryFile(*args, **kwargs)

    def fail_write(content: bytes) -> int:
        """Raise a controlled filesystem-like error before replacement occurs."""
        raise OSError("simulated binary write failure")

    temporary_file.write = fail_write
    return temporary_file
