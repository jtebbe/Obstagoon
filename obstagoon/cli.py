from __future__ import annotations

import argparse
from pathlib import Path

from .config import SiteConfig
from .pipeline import build_site


def main() -> int:
    parser = argparse.ArgumentParser("Obstagoon - expansion documentation builder")
    parser.add_argument("project_dir", help="Directory of the pokeemerald-expansion project")
    parser.add_argument("--title", default="pokeemerald-expansion", help="Website title")
    parser.add_argument("--dist-dir", default=None, help="Output directory")
    parser.add_argument("--site-url", default=None, help="Base site URL")
    parser.add_argument("--copy-assets", action="store_true", help="Copy located assets into dist/assets")
    parser.add_argument("--wild-encounters-json", default=None, help="Path to generated wild encounter JSON")
    parser.add_argument("--verbose", action="store_true", help="Print progress")
    parser.add_argument("--cache-dir", default=None, help="Directory for persistent caches")
    parser.add_argument("--pillow-transparency", action="store_true", help="Enable Pillow-based PNG transparency and anim_front/front_anim top-half cropping for graphics/pokemon/*.png assets")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    dist_dir = Path(args.dist_dir).resolve() if args.dist_dir else Path(__file__).resolve().parent.parent / "dist"
    wild_encounters_path = Path(args.wild_encounters_json).resolve() if args.wild_encounters_json else None
    cache_dir = Path(args.cache_dir).resolve() if args.cache_dir else None
    config = SiteConfig(
        project_dir=project_dir,
        dist_dir=dist_dir,
        site_title=args.title,
        site_url=args.site_url,
        copy_assets=args.copy_assets,
        verbose=args.verbose,
        wild_encounters_path=wild_encounters_path,
        cache_dir=cache_dir,
        pillow_transparency=args.pillow_transparency,
    )
    build_site(config)
    return 0
