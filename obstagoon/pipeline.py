from __future__ import annotations

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import SiteConfig
from .extract.expansion_project import ExpansionProject
from .model.builder import build_model
from .generate.site import SiteGenerator


def build_site(config: SiteConfig) -> None:
    config.ensure()
    project = ExpansionProject(config.project_dir, verbose=config.verbose, wild_encounters_path=config.wild_encounters_path, cache_dir=config.cache_dir, hoenn_dex=config.hoenn_dex)
    model = build_model(project)
    env = Environment(
        loader=FileSystemLoader(str((__import__(__name__.split('.')[0]).__path__[0])) + "/templates"),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    generator = SiteGenerator(config=config, model=model, env=env)
    generator.run()
