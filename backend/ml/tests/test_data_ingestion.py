from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.data_ingestion import ingest_csv, load_csv, report_shape, validate_columns


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    path = tmp_path / "sample.csv"
    pd.DataFrame({
        "id": [1, 2, 3],
        "name": ["a", "b", "c"],
        "value": [0.1, 0.2, 0.3],
    }).to_csv(path, index=False)
    return path


@pytest.fixture
def header_only_csv(tmp_path: Path) -> Path:
    path = tmp_path / "header_only.csv"
    path.write_text("id,name,value\n")
    return path


@pytest.fixture
def truly_empty_csv(tmp_path: Path) -> Path:
    path = tmp_path / "truly_empty.csv"
    path.write_text("")
    return path


@pytest.fixture
def malformed_csv(tmp_path: Path) -> Path:
    path = tmp_path / "garbage.csv"
    path.write_bytes(b"\x89PNG\r\n\x1a\n")
    return path


class TestLoadCsv:
    def test_loads_csv_with_defaults(self, sample_csv: Path):
        df = load_csv(sample_csv)
        assert list(df.columns) == ["id", "name", "value"]
        assert len(df) == 3

    def test_loads_csv_with_custom_kwargs(self, sample_csv: Path):
        df = load_csv(sample_csv, usecols=["id", "name"])
        assert list(df.columns) == ["id", "name"]
        assert len(df) == 3

    @pytest.mark.parametrize("bad_path", [
        "/nonexistent/path.csv",
        Path("/tmp/does_not_exist_12345.csv"),
    ])
    def test_raises_on_missing_file(self, bad_path):
        with pytest.raises(FileNotFoundError, match="CSV not found"):
            load_csv(bad_path)


class TestValidateColumns:
    def test_passes_when_all_columns_present(self, sample_csv: Path):
        df = pd.read_csv(sample_csv)
        result = validate_columns(df, ["id", "name"])
        assert result == ["id", "name"]

    def test_raises_on_missing_column(self, sample_csv: Path):
        df = pd.read_csv(sample_csv)
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_columns(df, ["id", "nope"])

    def test_raises_on_multiple_missing(self, sample_csv: Path):
        df = pd.read_csv(sample_csv)
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_columns(df, ["a", "b", "c"])

    def test_empty_required_list(self, sample_csv: Path):
        df = pd.read_csv(sample_csv)
        assert validate_columns(df, []) == []


class TestReportShape:
    def test_prints_shape_without_name(self, sample_csv: Path, capsys):
        df = pd.read_csv(sample_csv)
        report_shape(df)
        captured = capsys.readouterr()
        assert "3 rows x 3 columns" in captured.out

    def test_prints_shape_with_name(self, sample_csv: Path, capsys):
        df = pd.read_csv(sample_csv)
        report_shape(df, name="test.csv")
        captured = capsys.readouterr()
        assert "Dataset test.csv: 3 rows x 3 columns" in captured.out


class TestIngestCsv:
    def test_ingest_no_validation(self, sample_csv: Path, capsys):
        df = ingest_csv(sample_csv)
        assert list(df.columns) == ["id", "name", "value"]
        assert len(df) == 3
        captured = capsys.readouterr()
        assert "rows" in captured.out and "columns" in captured.out

    def test_ingest_with_validation(self, sample_csv: Path, capsys):
        df = ingest_csv(sample_csv, required=["id", "name"])
        assert len(df) == 3

    def test_ingest_fails_validation(self, sample_csv: Path):
        with pytest.raises(ValueError, match="Missing required columns"):
            ingest_csv(sample_csv, required=["missing_col"])

    def test_ingest_missing_file(self):
        with pytest.raises(FileNotFoundError, match="CSV not found"):
            ingest_csv("/tmp/nope.csv")


class TestEdgeCases:
    def test_header_only_csv_returns_empty_frame(self, header_only_csv: Path):
        df = load_csv(header_only_csv)
        assert df.empty

    def test_header_only_csv_passes_validation(self, header_only_csv: Path):
        df = load_csv(header_only_csv)
        assert validate_columns(df, ["id", "name"]) == ["id", "name"]

    def test_header_only_csv_fails_validation(self, header_only_csv: Path):
        df = load_csv(header_only_csv)
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_columns(df, ["missing_col"])

    def test_truly_empty_csv_raises(self, truly_empty_csv: Path):
        with pytest.raises(pd.errors.EmptyDataError):
            load_csv(truly_empty_csv)

    def test_malformed_csv_raises(self, malformed_csv: Path):
        with pytest.raises((pd.errors.ParserError, UnicodeDecodeError)):
            load_csv(malformed_csv)
