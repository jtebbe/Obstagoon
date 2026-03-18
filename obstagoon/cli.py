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
    parser.add_argument("--hoenn-dex", action="store_true", help="Use the Hoenn regional dex order from include/constants/pokedex.h and only include species present in that dex")
    parser.add_argument("--documentation", action="store_true", help="Build the HTML documentation site")
    parser.add_argument("--showdown-export", action="store_true", help="Generate Pokémon Showdown server/client fork payloads after building the site")
    parser.add_argument("--showdown-export-dir", default=None, help="Directory for generated Pokémon Showdown export payloads")
    parser.add_argument("--showdown-canonical-pokedex", default=None, help="Path to an upstream Pokémon Showdown data/pokedex.ts to preserve canonical entry names/forms/order")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    dist_dir = Path(args.dist_dir).resolve() if args.dist_dir else Path(__file__).resolve().parent.parent / "dist"
    wild_encounters_path = Path(args.wild_encounters_json).resolve() if args.wild_encounters_json else None
    cache_dir = Path(args.cache_dir).resolve() if args.cache_dir else None
    showdown_export_dir = Path(args.showdown_export_dir).resolve() if args.showdown_export_dir else None
    showdown_canonical_pokedex_path = Path(args.showdown_canonical_pokedex).resolve() if args.showdown_canonical_pokedex else None
    documentation = args.documentation or not args.showdown_export
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
        hoenn_dex=args.hoenn_dex,
        documentation=documentation,
        showdown_export=args.showdown_export,
        showdown_export_dir=showdown_export_dir,
        showdown_canonical_pokedex_path=showdown_canonical_pokedex_path,
    )
    build_site(config)
    return 0
