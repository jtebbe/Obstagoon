from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SiteConfig:
    project_dir: Path
    dist_dir: Path
    site_title: str
    site_url: str | None = None
    copy_assets: bool = False
    verbose: bool = False
    wild_encounters_path: Path | None = None
    cache_dir: Path | None = None
    pillow_transparency: bool = False

    def ensure(self) -> None:
        self.dist_dir.mkdir(parents=True, exist_ok=True)
        if self.cache_dir is None:
            self.cache_dir = self.dist_dir / '.obstagoon-cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
