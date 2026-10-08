from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests

from nl_data_agent.paths import project_root, resolve_under_root


class EtlToolkit:
    """Extract, transform, and load helpers using project-relative paths."""

    def _resolve_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        return resolve_under_root(*candidate.parts)

    def extract_load(self, url: str, output_folder: str, format: str) -> str:
        output_dir = self._resolve_path(output_folder)
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = output_dir / f"extracted_data.{format}"

        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and "results" in data:
                df = pd.json_normalize(data["results"])
            elif isinstance(data, list):
                df = pd.json_normalize(data)
            else:
                df = pd.json_normalize(data)

            fmt = format.lower().strip()
            if fmt == "csv":
                df.to_csv(filename, index=False)
            elif fmt == "json":
                df.to_json(filename, orient="records", lines=True)
            elif fmt == "parquet":
                df.to_parquet(filename, index=False)
            else:
                return f"Unsupported format: {format}"

            return f"Data successfully extracted and saved to {filename}"
        except requests.exceptions.RequestException as exc:
            return f"Failed to extract data: {exc}"

    def preview_file(self, file_path: str) -> str:
        path = self._resolve_path(file_path)
        extension = path.suffix.lower()

        if extension == ".csv":
            df = pd.read_csv(path)
        elif extension == ".json":
            df = pd.read_json(path, lines=True)
        elif extension == ".parquet":
            df = pd.read_parquet(path)
        else:
            return f"Unsupported file format: {extension}"

        return str(df.head(3))

    def execute_code(self, code: str) -> str:
        try:
            # Run with cwd at project root so relative paths in generated code work.
            previous = os.getcwd()
            os.chdir(project_root())
            try:
                exec(code, {"pd": pd, "pandas": pd, "os": os})
            finally:
                os.chdir(previous)
            return "Code executed successfully."
        except Exception as exc:
            return f"Failed to execute code: {exc}"
