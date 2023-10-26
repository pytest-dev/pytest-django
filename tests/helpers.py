from pathlib import Path

import pytest


class DjangoPytester(pytest.Pytester):  # type: ignore[misc]
    project_root: Path

    def create_test_module(  # type: ignore[empty-body]
        self,
        test_code: str,
        filename: str = ...,
    ) -> Path:
        ...

    def create_app_file(self, code: str, filename: str) -> Path:  # type: ignore[empty-body]
        ...
