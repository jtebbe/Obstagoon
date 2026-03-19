from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from obstagoon.config import SiteConfig
from obstagoon.model.builder import build_model
from obstagoon.trainer_editor import _TrainerEditorBackend, _species_display_name


class DummyProject:
    def __init__(self, payload: dict):
        self.payload = payload

    def load_all(self) -> dict:
        return self.payload


def _write_bgr555_palette(path: Path, colors: list[tuple[int, int, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = bytearray()
    for r, g, b in colors:
        value = ((b * 31 // 255) << 10) | ((g * 31 // 255) << 5) | (r * 31 // 255)
        raw.extend(int(value).to_bytes(2, "little"))
    path.write_bytes(bytes(raw))


def _png_from_bytes(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGBA")


def test_trainer_editor_shiny_preview_differs_from_normal(tmp_path: Path) -> None:
    payload = {
        "species_to_national": {"SPECIES_BAGON": 371},
        "form_species_tables": {},
        "species": {
            "SPECIES_BAGON": {
                "speciesName": "Bagon",
                "types": ["TYPE_DRAGON"],
                "abilities": ["ABILITY_ROCK_HEAD"],
                "graphics": {
                    "frontPic": "graphics/pokemon/bagon/front.png",
                    "palette": "graphics/pokemon/bagon/normal.pal",
                    "shinyPalette": "graphics/pokemon/bagon/shiny.pal",
                },
                "stats": {}, "evolutions": [], "levelUpLearnset": [], "eggMoves": [], "teachableLearnset": [],
            },
        },
        "moves": {},
        "abilities": {"ABILITY_ROCK_HEAD": {"name": "Rock Head"}},
        "items": {},
        "encounters": [],
        "trainers": [],
        "types": {"TYPE_DRAGON": "TYPE_DRAGON"},
        "validation": {},
        "sprite_diagnostics": {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / "proj"
    sprite_path = project_dir / "graphics/pokemon/bagon/front.png"
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("P", (4, 4))
    img.putpalette([0, 0, 0, 255, 0, 0] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            img.putpixel((x, y), 0)
    img.putpixel((1, 1), 1)
    img.save(sprite_path)
    _write_bgr555_palette(project_dir / "graphics/pokemon/bagon/normal.pal", [(0, 0, 0), (30, 144, 255)])
    _write_bgr555_palette(project_dir / "graphics/pokemon/bagon/shiny.pal", [(0, 0, 0), (144, 238, 144)])
    (project_dir / "src/data").mkdir(parents=True, exist_ok=True)
    (project_dir / "src/data/trainers.party").write_text("=== TRAINER_TEST ===\nName: TEST\n\nBagon\n", encoding="utf-8")

    backend = _TrainerEditorBackend(SiteConfig(project_dir=project_dir, dist_dir=tmp_path / "dist", site_title="Test"), model)
    normal_payload = backend.pokemon_sprite_response("Bagon", "No")
    shiny_payload = backend.pokemon_sprite_response("Bagon", "Yes")

    assert normal_payload is not None
    assert shiny_payload is not None
    normal_img = _png_from_bytes(normal_payload[0])
    shiny_img = _png_from_bytes(shiny_payload[0])
    assert normal_img.getpixel((1, 1))[:3] != shiny_img.getpixel((1, 1))[:3]
    assert normal_payload[0] != shiny_payload[0]


def test_trainer_editor_form_preview_uses_form_palette_and_canonical_labels(tmp_path: Path) -> None:
    payload = {
        "species_to_national": {"SPECIES_ARCEUS": 493, "SPECIES_ARCEUS_DARK": 493, "SPECIES_DEOXYS_ATTACK": 386},
        "form_species_tables": {"SPECIES_ARCEUS": ["SPECIES_ARCEUS", "SPECIES_ARCEUS_DARK"]},
        "species": {
            "SPECIES_ARCEUS": {
                "speciesName": "Arceus",
                "types": ["TYPE_NORMAL"],
                "abilities": ["ABILITY_MULTITYPE"],
                "graphics": {
                    "frontPic": "graphics/pokemon/arceus/anim_front.png",
                    "palette": "graphics/pokemon/arceus/normal/normal.pal",
                },
                "stats": {}, "evolutions": [], "levelUpLearnset": [], "eggMoves": [], "teachableLearnset": [],
            },
            "SPECIES_ARCEUS_DARK": {
                "speciesName": "Arceus",
                "types": ["TYPE_DARK"],
                "abilities": ["ABILITY_MULTITYPE"],
                "graphics": {
                    "frontPic": "graphics/pokemon/arceus/anim_front.png",
                    "palette": "graphics/pokemon/arceus/dark/normal.pal",
                },
                "stats": {}, "evolutions": [], "levelUpLearnset": [], "eggMoves": [], "teachableLearnset": [],
            },
            "SPECIES_DEOXYS_ATTACK": {
                "speciesName": "Deoxys",
                "types": ["TYPE_PSYCHIC"],
                "abilities": ["ABILITY_PRESSURE"],
                "graphics": {"frontPic": "graphics/pokemon/deoxys/attack/front.png"},
                "stats": {}, "evolutions": [], "levelUpLearnset": [], "eggMoves": [], "teachableLearnset": [],
            },
        },
        "moves": {},
        "abilities": {"ABILITY_MULTITYPE": {"name": "Multitype"}, "ABILITY_PRESSURE": {"name": "Pressure"}},
        "items": {},
        "encounters": [],
        "trainers": [],
        "types": {"TYPE_NORMAL": "TYPE_NORMAL", "TYPE_DARK": "TYPE_DARK", "TYPE_PSYCHIC": "TYPE_PSYCHIC"},
        "validation": {},
        "sprite_diagnostics": {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / "proj"
    sprite_path = project_dir / "graphics/pokemon/arceus/anim_front.png"
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("P", (4, 4))
    img.putpalette([0, 0, 0, 255, 0, 0] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            img.putpixel((x, y), 0)
    img.putpixel((1, 1), 1)
    img.putpixel((1, 0), 1)
    img.save(sprite_path)
    _write_bgr555_palette(project_dir / "graphics/pokemon/arceus/normal/normal.pal", [(0, 0, 0), (255, 0, 0)])
    _write_bgr555_palette(project_dir / "graphics/pokemon/arceus/dark/normal.pal", [(0, 0, 0), (255, 255, 255)])
    (project_dir / "src/data").mkdir(parents=True, exist_ok=True)
    (project_dir / "src/data/trainers.party").write_text("=== TRAINER_TEST ===\nName: TEST\n\nArceus\n", encoding="utf-8")

    backend = _TrainerEditorBackend(SiteConfig(project_dir=project_dir, dist_dir=tmp_path / "dist", site_title="Test"), model)
    dark_payload = backend.pokemon_sprite_response("Arceus-Dark", "No")
    assert dark_payload is not None
    dark_img = _png_from_bytes(dark_payload[0])
    assert dark_img.size == (4, 2)
    assert dark_img.getpixel((1, 1))[:3] == (255, 255, 255)
    assert _species_display_name(model.species["SPECIES_ARCEUS_DARK"], model) == "Arceus-Dark"
    assert _species_display_name(model.species["SPECIES_DEOXYS_ATTACK"], model) == "Deoxys-Attack"


def test_trainer_editor_preview_resolves_form_raster_near_palette_for_non_raster_frontpic(tmp_path: Path) -> None:
    payload = {
        "species_to_national": {"SPECIES_CHARIZARD_GMAX": 6},
        "form_species_tables": {},
        "species": {
            "SPECIES_CHARIZARD_GMAX": {
                "speciesName": "Charizard",
                "types": ["TYPE_FIRE", "TYPE_FLYING"],
                "abilities": ["ABILITY_BLAZE"],
                "graphics": {
                    "frontPic": "graphics/pokemon/charizard/gmax/front.4bpp.lz",
                    "palette": "graphics/pokemon/charizard/gmax/normal.pal",
                },
                "stats": {}, "evolutions": [], "levelUpLearnset": [], "eggMoves": [], "teachableLearnset": [],
            },
        },
        "moves": {},
        "abilities": {"ABILITY_BLAZE": {"name": "Blaze"}},
        "items": {},
        "encounters": [],
        "trainers": [],
        "types": {"TYPE_FIRE": "TYPE_FIRE", "TYPE_FLYING": "TYPE_FLYING"},
        "validation": {},
        "sprite_diagnostics": {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / "proj"
    gmax_dir = project_dir / "graphics/pokemon/charizard/gmax"
    gmax_dir.mkdir(parents=True, exist_ok=True)
    (gmax_dir / "front.4bpp.lz").write_bytes(b"not-a-real-png")
    img = Image.new("P", (4, 4))
    img.putpalette([0, 0, 0, 255, 120, 0] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            img.putpixel((x, y), 0)
    img.putpixel((1, 1), 1)
    img.save(gmax_dir / "front.png")
    _write_bgr555_palette(gmax_dir / "normal.pal", [(0, 0, 0), (255, 120, 0)])
    (project_dir / "src/data").mkdir(parents=True, exist_ok=True)
    (project_dir / "src/data/trainers.party").write_text("=== TRAINER_TEST ===\nName: TEST\n\nCharizard-Gmax\n", encoding="utf-8")

    backend = _TrainerEditorBackend(SiteConfig(project_dir=project_dir, dist_dir=tmp_path / "dist", site_title="Test"), model)
    payload = backend.pokemon_sprite_response("Charizard-Gmax", "No")

    assert payload is not None
    out = _png_from_bytes(payload[0])
    assert out.getpixel((1, 1))[:3] == (255, 120, 0)


def test_trainer_editor_shiny_preview_uses_form_specific_palette_path(tmp_path: Path) -> None:
    payload = {
        "species_to_national": {"SPECIES_ARCEUS_DARK": 493},
        "form_species_tables": {},
        "species": {
            "SPECIES_ARCEUS_DARK": {
                "speciesName": "Arceus",
                "types": ["TYPE_DARK"],
                "abilities": ["ABILITY_MULTITYPE"],
                "graphics": {
                    "frontPic": "graphics/pokemon/arceus/anim_front.png",
                    "palette": "graphics/pokemon/arceus/dark/normal.pal",
                    "shinyPalette": "graphics/pokemon/arceus/dark/shiny.pal",
                },
                "stats": {}, "evolutions": [], "levelUpLearnset": [], "eggMoves": [], "teachableLearnset": [],
            },
        },
        "moves": {},
        "abilities": {"ABILITY_MULTITYPE": {"name": "Multitype"}},
        "items": {},
        "encounters": [],
        "trainers": [],
        "types": {"TYPE_DARK": "TYPE_DARK"},
        "validation": {},
        "sprite_diagnostics": {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / "proj"
    sprite_path = project_dir / "graphics/pokemon/arceus/anim_front.png"
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("P", (4, 4))
    img.putpalette([0, 0, 0, 255, 255, 255] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            img.putpixel((x, y), 0)
    img.putpixel((1, 1), 1)
    img.putpixel((1, 0), 1)
    img.save(sprite_path)
    _write_bgr555_palette(project_dir / "graphics/pokemon/arceus/dark/normal.pal", [(0, 0, 0), (255, 255, 255)])
    _write_bgr555_palette(project_dir / "graphics/pokemon/arceus/dark/shiny.pal", [(0, 0, 0), (255, 215, 0)])
    (project_dir / "src/data").mkdir(parents=True, exist_ok=True)
    (project_dir / "src/data/trainers.party").write_text("=== TRAINER_TEST ===\nName: TEST\n\nArceus-Dark\n", encoding="utf-8")

    backend = _TrainerEditorBackend(SiteConfig(project_dir=project_dir, dist_dir=tmp_path / "dist", site_title="Test"), model)
    normal_payload = backend.pokemon_sprite_response("Arceus-Dark", "No")
    shiny_payload = backend.pokemon_sprite_response("Arceus-Dark", "Yes")

    assert normal_payload is not None and shiny_payload is not None
    normal_img = _png_from_bytes(normal_payload[0])
    shiny_img = _png_from_bytes(shiny_payload[0])
    assert normal_img.getpixel((1, 1))[:3] != shiny_img.getpixel((1, 1))[:3]


def test_trainer_editor_preview_prefers_form_front_near_palette_over_base_front(tmp_path: Path) -> None:
    payload = {
        "species_to_national": {"SPECIES_ALAKAZAM": 65, "SPECIES_ALAKAZAM_MEGA": 65},
        "form_species_tables": {"SPECIES_ALAKAZAM": ["SPECIES_ALAKAZAM", "SPECIES_ALAKAZAM_MEGA"]},
        "species": {
            "SPECIES_ALAKAZAM": {
                "speciesName": "Alakazam",
                "types": ["TYPE_PSYCHIC"],
                "abilities": ["ABILITY_SYNCHRONIZE"],
                "graphics": {
                    "frontPic": "graphics/pokemon/alakazam/front.png",
                    "palette": "graphics/pokemon/alakazam/normal.pal",
                },
                "stats": {}, "evolutions": [], "levelUpLearnset": [], "eggMoves": [], "teachableLearnset": [],
            },
            "SPECIES_ALAKAZAM_MEGA": {
                "speciesName": "Alakazam",
                "types": ["TYPE_PSYCHIC"],
                "abilities": ["ABILITY_TRACE"],
                "graphics": {
                    "frontPic": "graphics/pokemon/alakazam/front.png",
                    "palette": "graphics/pokemon/alakazam/mega/normal.pal",
                    "shinyPalette": "graphics/pokemon/alakazam/mega/shiny.pal",
                },
                "stats": {}, "evolutions": [], "levelUpLearnset": [], "eggMoves": [], "teachableLearnset": [],
            },
        },
        "moves": {},
        "abilities": {"ABILITY_SYNCHRONIZE": {"name": "Synchronize"}, "ABILITY_TRACE": {"name": "Trace"}},
        "items": {},
        "encounters": [],
        "trainers": [],
        "types": {"TYPE_PSYCHIC": "TYPE_PSYCHIC"},
        "validation": {},
        "sprite_diagnostics": {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / "proj"
    base_dir = project_dir / "graphics/pokemon/alakazam"
    mega_dir = base_dir / "mega"
    mega_dir.mkdir(parents=True, exist_ok=True)

    base = Image.new("P", (4, 4))
    base.putpalette([0, 0, 0, 255, 255, 0] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            base.putpixel((x, y), 0)
    base.putpixel((1, 1), 1)
    base.save(base_dir / "front.png")

    mega = Image.new("P", (4, 4))
    mega.putpalette([0, 0, 0, 0, 255, 255] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            mega.putpixel((x, y), 0)
    mega.putpixel((2, 2), 1)
    mega.save(mega_dir / "front.png")

    _write_bgr555_palette(base_dir / "normal.pal", [(0, 0, 0), (255, 255, 0)])
    _write_bgr555_palette(mega_dir / "normal.pal", [(0, 0, 0), (0, 255, 255)])
    _write_bgr555_palette(mega_dir / "shiny.pal", [(0, 0, 0), (255, 0, 255)])
    (project_dir / "src/data").mkdir(parents=True, exist_ok=True)
    (project_dir / "src/data/trainers.party").write_text("=== TRAINER_TEST ===\nName: TEST\n\nAlakazam-Mega\n", encoding="utf-8")

    backend = _TrainerEditorBackend(SiteConfig(project_dir=project_dir, dist_dir=tmp_path / "dist", site_title="Test"), model)
    normal_payload = backend.pokemon_sprite_response("Alakazam-Mega", "No")
    shiny_payload = backend.pokemon_sprite_response("Alakazam-Mega", "Yes")

    assert normal_payload is not None and shiny_payload is not None
    normal_img = _png_from_bytes(normal_payload[0])
    shiny_img = _png_from_bytes(shiny_payload[0])
    # form-specific front should be used, not the base front
    assert normal_img.getpixel((2, 2))[:3] == (0, 255, 255)
    assert normal_img.getpixel((1, 1))[3] == 0
    # shiny should recolor the form-specific sprite
    assert shiny_img.getpixel((2, 2))[:3] == (255, 0, 255)

def test_trainer_editor_preview_matches_documentation_logic_for_alcremie_pattern_variant(tmp_path: Path) -> None:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    payload = {
        'species_to_national': {'SPECIES_ALCREMIE_FLOWER_MATCHA_CREAM': 869},
        'form_species_tables': {},
        'species': {
            'SPECIES_ALCREMIE_FLOWER_MATCHA_CREAM': {
                'speciesName': 'Alcremie',
                'types': ['TYPE_FAIRY'],
                'abilities': ['ABILITY_SWEET_VEIL'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/alcremie/front.png',
                    'palette': 'graphics/pokemon/alcremie/flower/matcha_cream/normal.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_SWEET_VEIL': {'name': 'Sweet Veil'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_FAIRY': 'TYPE_FAIRY'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'

    base_sprite = project_dir / 'graphics/pokemon/alcremie/front.png'
    base_sprite.parent.mkdir(parents=True, exist_ok=True)
    base = Image.new('P', (4, 4))
    base.putpalette([0, 0, 0, 255, 0, 0] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            base.putpixel((x, y), 0)
    base.putpixel((1, 1), 1)
    base.save(base_sprite)

    flower_sprite = project_dir / 'graphics/pokemon/alcremie/flower/front.png'
    flower_sprite.parent.mkdir(parents=True, exist_ok=True)
    flower = Image.new('P', (4, 4))
    flower.putpalette([0, 0, 0, 255, 0, 0, 0, 255, 0] + [0] * (768 - 9))
    for x in range(4):
        for y in range(4):
            flower.putpixel((x, y), 0)
    flower.putpixel((1, 1), 1)
    flower.putpixel((2, 1), 2)
    flower.save(flower_sprite)

    _write_bgr555_palette(project_dir / 'graphics/pokemon/alcremie/flower/normal.pal', [(0, 0, 0), (255, 0, 0), (0, 255, 0)])
    _write_bgr555_palette(project_dir / 'graphics/pokemon/alcremie/flower/matcha_cream/normal.pal', [(0, 0, 0), (0, 0, 255), (0, 197, 0)])
    (project_dir / 'src/data').mkdir(parents=True, exist_ok=True)
    (project_dir / 'src/data/trainers.party').write_text('=== TRAINER_TEST ===\nName: TEST\n\nAlcremie-Flower-Matcha-Cream\n', encoding='utf-8')

    backend = _TrainerEditorBackend(SiteConfig(project_dir=project_dir, dist_dir=tmp_path / 'dist_preview', site_title='Test'), model)
    payload = backend.pokemon_sprite_response('Alcremie-Flower-Matcha-Cream', 'No')
    assert payload is not None
    preview = _png_from_bytes(payload[0])
    assert preview.getpixel((1, 1))[:3] == (0, 0, 255)
    assert preview.getpixel((2, 1))[:3] == (0, 189, 0)


def test_trainer_editor_shiny_preview_differs_for_rgba_bagon(tmp_path: Path) -> None:
    payload = {
        'species_to_national': {'SPECIES_BAGON': 371},
        'form_species_tables': {},
        'species': {
            'SPECIES_BAGON': {
                'speciesName': 'Bagon',
                'types': ['TYPE_DRAGON'],
                'abilities': ['ABILITY_ROCK_HEAD'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/bagon/front.png',
                    'palette': 'graphics/pokemon/bagon/normal.pal',
                    'shinyPalette': 'graphics/pokemon/bagon/shiny.pal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_ROCK_HEAD': {'name': 'Rock Head'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_DRAGON': 'TYPE_DRAGON'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    sprite_path = project_dir / 'graphics/pokemon/bagon/front.png'
    sprite_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGBA', (4, 4), (0, 0, 0, 255))
    img.putpixel((1, 1), (48, 160, 255, 255))
    img.save(sprite_path)
    _write_bgr555_palette(project_dir / 'graphics/pokemon/bagon/normal.pal', [(0, 0, 0), (48, 160, 255)])
    _write_bgr555_palette(project_dir / 'graphics/pokemon/bagon/shiny.pal', [(0, 0, 0), (120, 255, 120)])
    (project_dir / 'src/data').mkdir(parents=True, exist_ok=True)
    (project_dir / 'src/data/trainers.party').write_text('=== TRAINER_TEST ===\nName: TEST\n\nBagon\n', encoding='utf-8')

    backend = _TrainerEditorBackend(SiteConfig(project_dir=project_dir, dist_dir=tmp_path / 'dist', site_title='Test'), model)
    normal_payload = backend.pokemon_sprite_response('Bagon', 'No')
    shiny_payload = backend.pokemon_sprite_response('Bagon', 'Yes')
    assert normal_payload is not None and shiny_payload is not None
    normal_img = _png_from_bytes(normal_payload[0])
    shiny_img = _png_from_bytes(shiny_payload[0])
    assert normal_img.getpixel((1, 1))[:3] == (48, 160, 255)
    assert shiny_img.getpixel((1, 1))[:3] != normal_img.getpixel((1, 1))[:3]


def test_trainer_editor_preview_uses_pal_sibling_when_graphics_reference_gbapal_for_form_and_shiny(tmp_path: Path) -> None:
    payload = {
        'species_to_national': {'SPECIES_CAMERUPT_MEGA': 323},
        'form_species_tables': {},
        'species': {
            'SPECIES_CAMERUPT_MEGA': {
                'speciesName': 'Camerupt',
                'types': ['TYPE_FIRE', 'TYPE_GROUND'],
                'abilities': ['ABILITY_SHEER_FORCE'],
                'graphics': {
                    'frontPic': 'graphics/pokemon/camerupt/front.png',
                    'palette': 'graphics/pokemon/camerupt/mega/normal.gbapal',
                    'shinyPalette': 'graphics/pokemon/camerupt/mega/shiny.gbapal',
                },
                'stats': {}, 'evolutions': [], 'levelUpLearnset': [], 'eggMoves': [], 'teachableLearnset': [],
            },
        },
        'moves': {}, 'abilities': {'ABILITY_SHEER_FORCE': {'name': 'Sheer Force'}}, 'items': {}, 'encounters': [], 'trainers': [],
        'types': {'TYPE_FIRE': 'TYPE_FIRE', 'TYPE_GROUND': 'TYPE_GROUND'}, 'validation': {}, 'sprite_diagnostics': {},
    }
    model = build_model(DummyProject(payload))
    project_dir = tmp_path / 'proj'
    base_dir = project_dir / 'graphics/pokemon/camerupt'
    mega_dir = base_dir / 'mega'
    mega_dir.mkdir(parents=True, exist_ok=True)

    base = Image.new('P', (4, 4))
    base.putpalette([0, 0, 0, 255, 255, 0] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            base.putpixel((x, y), 0)
    base.putpixel((1, 1), 1)
    base.save(base_dir / 'front.png')

    mega = Image.new('P', (4, 4))
    mega.putpalette([0, 0, 0, 220, 80, 40] + [0] * (768 - 6))
    for x in range(4):
        for y in range(4):
            mega.putpixel((x, y), 0)
    mega.putpixel((2, 2), 1)
    mega.save(mega_dir / 'front.png')

    _write_bgr555_palette(mega_dir / 'normal.pal', [(0, 0, 0), (220, 80, 40)])
    _write_bgr555_palette(mega_dir / 'shiny.pal', [(0, 0, 0), (40, 120, 255)])
    # Only .gbapal is referenced by graphics; trainer editor should resolve the .pal siblings.
    (mega_dir / 'normal.gbapal').write_bytes(b'ignored')
    (mega_dir / 'shiny.gbapal').write_bytes(b'ignored')
    (project_dir / 'src/data').mkdir(parents=True, exist_ok=True)
    (project_dir / 'src/data/trainers.party').write_text('''=== TRAINER_TEST ===
Name: TEST

Camerupt-Mega
''', encoding='utf-8')

    backend = _TrainerEditorBackend(SiteConfig(project_dir=project_dir, dist_dir=tmp_path / 'dist', site_title='Test'), model)
    normal_payload = backend.pokemon_sprite_response('Camerupt-Mega', 'No')
    shiny_payload = backend.pokemon_sprite_response('Camerupt-Mega', 'Yes')
    assert normal_payload is not None and shiny_payload is not None
    normal_img = _png_from_bytes(normal_payload[0])
    shiny_img = _png_from_bytes(shiny_payload[0])
    assert normal_img.getpixel((2, 2))[:3] == (220, 80, 40)
    assert normal_img.getpixel((1, 1))[3] == 0
    assert shiny_img.getpixel((2, 2))[:3] == (32, 115, 255)
    assert shiny_img.getpixel((2, 2))[:3] != normal_img.getpixel((2, 2))[:3]
