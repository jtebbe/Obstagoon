from pathlib import Path

from obstagoon.extract.parsers.sprites import parse_sprite_assets
from obstagoon.model.builder import build_model


class _Project:
    def __init__(self, payload: dict):
        self._payload = payload
        self.hoenn_dex = False
        self.config = type("Cfg", (), {"hoenn_dex": False})()

    def load_all(self):
        return self._payload


def test_species_count_uses_representative_dex_entries_plus_non_dex_roots() -> None:
    payload = {
        'species_to_national': {
            'SPECIES_MEOWSTIC_M': 678,
            'SPECIES_MEOWSTIC_F': 678,
            'SPECIES_MEOWSTIC_M_MEGA': 678,
            'SPECIES_MEOWSTIC_F_MEGA': 678,
            'SPECIES_DINOZORK': None,
        },
        'form_species_tables': {
            'sMeowsticFormSpeciesIdTable': [
                'SPECIES_MEOWSTIC_M',
                'SPECIES_MEOWSTIC_F',
                'SPECIES_MEOWSTIC_M_MEGA',
                'SPECIES_MEOWSTIC_F_MEGA',
            ],
        },
        'species': {
            'SPECIES_MEOWSTIC_M': {'speciesName': 'Meowstic', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': [], 'formSpeciesIdTableIndex': 0},
            'SPECIES_MEOWSTIC_F': {'speciesName': 'Meowstic', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': [], 'formSpeciesIdTableIndex': 1},
            'SPECIES_MEOWSTIC_M_MEGA': {'speciesName': 'Meowstic', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': [], 'formSpeciesIdTableIndex': 2},
            'SPECIES_MEOWSTIC_F_MEGA': {'speciesName': 'Meowstic', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': [], 'formSpeciesIdTableIndex': 3},
            'SPECIES_DINOZORK': {'speciesName': 'Dinozork', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': []},
        },
        'moves': {}, 'abilities': {}, 'items': {}, 'types': {}, 'encounters': [], 'sprites': {}, 'trainers': [], 'hoenn_dex_order': [], 'sprite_diagnostics': {},
    }
    model = build_model(_Project(payload))
    assert model.metadata['species_count'] == 2


def test_representative_species_prefers_base_form_over_mega() -> None:
    payload = {
        'species_to_national': {
            'SPECIES_MEOWSTIC_M': 678,
            'SPECIES_MEOWSTIC_F': 678,
            'SPECIES_MEOWSTIC_F_MEGA': 678,
        },
        'form_species_tables': {
            'sMeowsticFormSpeciesIdTable': [
                'SPECIES_MEOWSTIC_M',
                'SPECIES_MEOWSTIC_F',
                'SPECIES_MEOWSTIC_F_MEGA',
            ],
        },
        'species': {
            'SPECIES_MEOWSTIC_M': {'speciesName': 'Meowstic', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': [], 'formSpeciesIdTableIndex': 0},
            'SPECIES_MEOWSTIC_F': {'speciesName': 'Meowstic', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': [], 'formSpeciesIdTableIndex': 1},
            'SPECIES_MEOWSTIC_F_MEGA': {'speciesName': 'Meowstic', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': [], 'formSpeciesIdTableIndex': 2},
        },
        'moves': {}, 'abilities': {}, 'items': {}, 'types': {}, 'encounters': [], 'sprites': {}, 'trainers': [], 'hoenn_dex_order': [], 'sprite_diagnostics': {},
    }
    model = build_model(_Project(payload))
    assert model.national_to_species[678] == 'SPECIES_MEOWSTIC_M'


def test_nested_subform_mega_dir_beats_shared_mega_dir(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'graphics/pokemon/tatsugiri/mega').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/tatsugiri/mega/front.png').write_text('curly-mega')
    (project / 'graphics/pokemon/tatsugiri/droopy/mega').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/tatsugiri/droopy/mega/front.png').write_text('droopy-mega')
    (project / 'graphics/pokemon/tatsugiri/stretchy/mega').mkdir(parents=True, exist_ok=True)
    (project / 'graphics/pokemon/tatsugiri/stretchy/mega/front.png').write_text('stretchy-mega')

    species = {
        'SPECIES_TATSUGIRI_CURLY_MEGA': {'graphics': {'frontPic': 'gMonFrontPic_TatsugiriCurlyMega'}},
        'SPECIES_TATSUGIRI_DROOPY_MEGA': {'graphics': {'frontPic': 'gMonFrontPic_TatsugiriDroopyMega'}},
        'SPECIES_TATSUGIRI_STRETCHY_MEGA': {'graphics': {'frontPic': 'gMonFrontPic_TatsugiriStretchyMega'}},
    }

    sprites = parse_sprite_assets(project, species)
    assert sprites['SPECIES_TATSUGIRI_CURLY_MEGA']['frontPic'] == 'graphics/pokemon/tatsugiri/mega/front.png'
    assert sprites['SPECIES_TATSUGIRI_DROOPY_MEGA']['frontPic'] == 'graphics/pokemon/tatsugiri/droopy/mega/front.png'
    assert sprites['SPECIES_TATSUGIRI_STRETCHY_MEGA']['frontPic'] == 'graphics/pokemon/tatsugiri/stretchy/mega/front.png'


def test_same_national_dex_group_links_include_mega_forms_for_base_and_variant() -> None:
    payload = {
        'species_to_national': {
            'SPECIES_TATSUGIRI_CURLY': 978,
            'SPECIES_TATSUGIRI_DROOPY': 978,
            'SPECIES_TATSUGIRI_STRETCHY': 978,
            'SPECIES_TATSUGIRI_CURLY_MEGA': 978,
            'SPECIES_TATSUGIRI_DROOPY_MEGA': 978,
            'SPECIES_TATSUGIRI_STRETCHY_MEGA': 978,
        },
        'form_species_tables': {
            'sTatsugiriFormSpeciesIdTable': [
                'SPECIES_TATSUGIRI_CURLY',
                'SPECIES_TATSUGIRI_DROOPY',
                'SPECIES_TATSUGIRI_STRETCHY',
            ],
        },
        'species': {
            'SPECIES_TATSUGIRI_CURLY': {'speciesName': 'Tatsugiri', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': [], 'formSpeciesIdTableIndex': 0},
            'SPECIES_TATSUGIRI_DROOPY': {'speciesName': 'Tatsugiri', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': [], 'formSpeciesIdTableIndex': 1},
            'SPECIES_TATSUGIRI_STRETCHY': {'speciesName': 'Tatsugiri', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': [], 'formSpeciesIdTableIndex': 2},
            'SPECIES_TATSUGIRI_CURLY_MEGA': {'speciesName': 'Tatsugiri', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': []},
            'SPECIES_TATSUGIRI_DROOPY_MEGA': {'speciesName': 'Tatsugiri', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': []},
            'SPECIES_TATSUGIRI_STRETCHY_MEGA': {'speciesName': 'Tatsugiri', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': []},
        },
        'moves': {}, 'abilities': {}, 'items': {}, 'types': {}, 'encounters': [], 'sprites': {}, 'trainers': [], 'hoenn_dex_order': [], 'sprite_diagnostics': {},
    }
    model = build_model(_Project(payload))
    assert 'SPECIES_TATSUGIRI_CURLY_MEGA' in model.species['SPECIES_TATSUGIRI_CURLY'].forms
    assert 'SPECIES_TATSUGIRI_DROOPY_MEGA' in model.species['SPECIES_TATSUGIRI_CURLY'].forms
    assert 'SPECIES_TATSUGIRI_STRETCHY_MEGA' in model.species['SPECIES_TATSUGIRI_CURLY'].forms
    assert 'SPECIES_TATSUGIRI_CURLY_MEGA' in model.species['SPECIES_TATSUGIRI_DROOPY'].forms


def test_same_national_dex_group_links_include_meowstic_mega_forms() -> None:
    payload = {
        'species_to_national': {
            'SPECIES_MEOWSTIC_M': 678,
            'SPECIES_MEOWSTIC_F': 678,
            'SPECIES_MEOWSTIC_M_MEGA': 678,
            'SPECIES_MEOWSTIC_F_MEGA': 678,
        },
        'form_species_tables': {
            'sMeowsticFormSpeciesIdTable': ['SPECIES_MEOWSTIC_M', 'SPECIES_MEOWSTIC_F'],
        },
        'species': {
            'SPECIES_MEOWSTIC_M': {'speciesName': 'Meowstic', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': [], 'formSpeciesIdTableIndex': 0},
            'SPECIES_MEOWSTIC_F': {'speciesName': 'Meowstic', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': [], 'formSpeciesIdTableIndex': 1},
            'SPECIES_MEOWSTIC_M_MEGA': {'speciesName': 'Meowstic', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': []},
            'SPECIES_MEOWSTIC_F_MEGA': {'speciesName': 'Meowstic', 'graphics': {}, 'types': [], 'abilities': [], 'eggGroups': [], 'stats': {}, 'evolutions': []},
        },
        'moves': {}, 'abilities': {}, 'items': {}, 'types': {}, 'encounters': [], 'sprites': {}, 'trainers': [], 'hoenn_dex_order': [], 'sprite_diagnostics': {},
    }
    model = build_model(_Project(payload))
    assert 'SPECIES_MEOWSTIC_M_MEGA' in model.species['SPECIES_MEOWSTIC_M'].forms
    assert 'SPECIES_MEOWSTIC_F_MEGA' in model.species['SPECIES_MEOWSTIC_M'].forms
    assert 'SPECIES_MEOWSTIC_M_MEGA' in model.species['SPECIES_MEOWSTIC_F'].forms
