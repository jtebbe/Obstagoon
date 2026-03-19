from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from obstagoon.model.schema import ObstagoonModel, ItemRecord
from obstagoon.trainer_editor import (
    BROWSER_APP_HTML,
    _parse_pokemon_block_editor,
    _serialize_pokemon_block,
    apply_form_state_to_metadata,
    load_trainer_editor_references,
    load_trainer_sections,
    save_trainer_sections,
    trainer_section_to_form_state,
)


def _empty_model() -> ObstagoonModel:
    return ObstagoonModel(
        species={},
        moves={},
        abilities={},
        items={
            'ITEM_FULL_RESTORE': ItemRecord(item_id='ITEM_FULL_RESTORE', name='Full Restore', pocket='POCKET_ITEMS'),
            'ITEM_SITRUS_BERRY': ItemRecord(item_id='ITEM_SITRUS_BERRY', name='Sitrus Berry', pocket='POCKET_BERRIES'),
            'ITEM_BICYCLE': ItemRecord(item_id='ITEM_BICYCLE', name='Bicycle', pocket='POCKET_KEY_ITEMS'),
        },
        types={},
        encounters=[],
        sprites=[],
        species_to_national={},
        national_to_species={},
        forms={},
        trainers={},
    )


def test_load_trainer_editor_references_parses_enums_and_defines(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'include/constants').mkdir(parents=True)
    (project / 'include').mkdir(exist_ok=True)
    (project / 'include/constants/trainers.h').write_text(
        'enum __attribute__((packed)) TrainerPicID {\n'
        '    TRAINER_PIC_RED,\n'
        '    TRAINER_PIC_SCHOOL_KID_F,\n'
        '    TRAINER_PIC_FRONT_COUNT,\n'
        '};\n\n'
        'enum TrainerClassID {\n'
        '    TRAINER_CLASS_SCHOOL_KID,\n'
        '    TRAINER_CLASS_COUNT,\n'
        '};\n\n'
        '#define TRAINER_ENCOUNTER_MUSIC_GIRL 1\n',
        encoding='utf-8',
    )
    (project / 'include/battle_transition.h').write_text(
        'enum MugshotColor { MUGSHOT_COLOR_NONE, MUGSHOT_COLOR_YELLOW, MUGSHOT_COLOR_BLUE };\n',
        encoding='utf-8',
    )
    (project / 'include/constants/battle.h').write_text(
        '#define STARTING_STATUS_DEFINITIONS \\\nX(STARTING_STATUS_SEA_OF_FIRE_PLAYER) \\\nX(STARTING_STATUS_SPIKES_PLAYER_L3)\n',
        encoding='utf-8',
    )
    (project / 'include/constants/battle_ai.h').write_text(
        '#define AI_FLAG_CHECK_BAD_MOVE (1 << 0)\n#define AI_FLAG_WILL_SUICIDE (1 << 1)\n',
        encoding='utf-8',
    )
    (project / 'include/trainer_pools.h').write_text(
        'enum PoolRulesets { POOL_RULESET_NONE, POOL_RULESET_SMOGON, POOL_RULESET_COUNT };\n',
        encoding='utf-8',
    )

    refs = load_trainer_editor_references(project, _empty_model())
    assert refs['trainer_pics'] == ['Red', 'School Kid F']
    assert refs['trainer_classes'] == ['School Kid']
    assert refs['encounter_music'] == ['Girl']
    assert refs['mugshot_colors'] == ['Blue', 'Yellow']
    assert refs['starting_statuses'] == ['Sea Of Fire Player', 'Spikes Player L3']
    assert refs['ai_flags'] == ['Check Bad Move', 'Will Suicide']
    assert refs['pool_rules'] == ['Smogon']
    assert 'Full Restore' in refs['items']
    assert refs['battle_type_options'] == ['Singles', 'Doubles']


def test_trainer_editor_round_trip_updates_controlled_fields(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'src/data').mkdir(parents=True)
    trainers_path = project / 'src/data/trainers.party'
    trainers_path.write_text(
        '=== TRAINER_KAREN_1 ===\n'
        'Name: KAREN\n'
        'Pic: School Kid F\n'
        'Class: School Kid\n'
        'Items: Full Restore / Full Restore\n'
        'Music: Girl\n'
        'Double Battle: No\n'
        'AI: Check Bad Move\n\n'
        'Abra\n'
        '- Psychic\n',
        encoding='utf-8',
    )

    sections = load_trainer_sections(project)
    assert len(sections) == 1
    section = sections[0]
    state = trainer_section_to_form_state(section)
    assert state['items'][:2] == ['Full Restore', 'Full Restore']
    assert state['battle_field'] == 'Double Battle'
    assert state['battle_value'] == 'No'

    apply_form_state_to_metadata(section, {
        'name': 'Karen',
        'pic': 'School Kid F',
        'class_name': 'School Kid',
        'gender': 'Female',
        'items': ['Full Restore', 'None', 'None'],
        'music': 'Girl',
        'battle_field': 'Double Battle',
        'battle_value': 'Yes',
        'mugshot': 'Yellow',
        'starting_statuses': ['Sea Of Fire Player', 'Spikes Player L3'],
        'pool_rules': 'Doubles',
        'party_size': '3',
        'ai_flags': ['Check Bad Move', 'Will Suicide'],
    })
    save_trainer_sections(project, sections)
    output = trainers_path.read_text(encoding='utf-8')
    assert 'Gender: Female' in output
    assert 'Items: Full Restore' in output
    assert 'Double Battle: Yes' in output
    assert 'Mugshot: Yellow' in output
    assert 'Starting Status: Sea Of Fire Player / Spikes Player L3' in output
    assert 'Party Pool: Yes' not in output
    assert 'Pool Rules: Doubles' in output
    assert 'Party Size: 3' in output
    assert 'AI: Check Bad Move / Will Suicide' in output
    assert 'Abra\n- Psychic' in output


def test_browser_backend_bootstrap_and_save(tmp_path: Path) -> None:
    from obstagoon.config import SiteConfig
    from obstagoon.trainer_editor import _TrainerEditorBackend

    project = tmp_path / 'proj'
    (project / 'include/constants').mkdir(parents=True)
    (project / 'include').mkdir(exist_ok=True)
    (project / 'src/data').mkdir(parents=True)
    (project / 'graphics/trainers/front_pics').mkdir(parents=True)
    (project / 'data/maps/TestTown').mkdir(parents=True)
    (project / 'data/maps/TestTown/scripts.inc').write_text('battle TRAINER_KAREN_1', encoding='utf-8')
    (project / 'graphics/trainers/front_pics/school_kid_f.png').write_text('x', encoding='utf-8')
    (project / 'src/data/trainers.party').write_text(
        '=== TRAINER_KAREN_1 ===\n'
        'Name: KAREN\n'
        'Pic: School Kid F\n\n'
        'Abra\n'
        '- Psychic\n',
        encoding='utf-8',
    )

    config = SiteConfig(project_dir=project, dist_dir=tmp_path / 'dist', site_title='Test', trainer_editor=True)
    config.ensure()
    backend = _TrainerEditorBackend(config=config, model=_empty_model())

    bootstrap = backend.bootstrap_payload()
    assert bootstrap['trainers'][0]['display_id'] == 'KAREN_1'
    assert bootstrap['trainers'][0]['location'] == 'Test Town'

    state = backend.get_trainer_state('KAREN_1')
    assert state['pic'] == 'School Kid F'
    assert state['location'] == 'Test Town'

    backend.save_trainer_state('KAREN_1', {
        'name': 'Karen',
        'pic': 'School Kid F',
        'class_name': '',
        'gender': 'Female',
        'items': ['None', 'None', 'None'],
        'music': '',
        'battle_field': 'Double Battle',
        'battle_value': 'No',
        'mugshot': 'None',
        'starting_statuses': [],
        'pool_rules': 'None',
        'party_size': '',
        'ai_flags': [],
    })
    saved = (project / 'src/data/trainers.party').read_text(encoding='utf-8')
    assert 'Gender: Female' in saved
    assert 'Pic: School Kid F' in saved


def test_legacy_battle_type_is_preserved_and_uses_singles_doubles(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'src/data').mkdir(parents=True)
    (project / 'data/maps/Route101').mkdir(parents=True)
    (project / 'data/maps/Route101/scripts.inc').write_text('battle TRAINER_KAREN_1', encoding='utf-8')
    trainers_path = project / 'src/data/trainers.party'
    trainers_path.write_text(
        '=== TRAINER_KAREN_1 ===\n'
        'Battle Type: Singles\n\n'
        'Abra\n'
        '- Psychic\n',
        encoding='utf-8',
    )

    sections = load_trainer_sections(project)
    section = sections[0]
    state = trainer_section_to_form_state(section)
    assert state['battle_field'] == 'Battle Type'
    assert state['battle_value'] == 'Singles'
    assert state['location'] == 'Route101' or state['location'] == 'Route 101'

    apply_form_state_to_metadata(section, {
        'name': '',
        'pic': '',
        'class_name': '',
        'gender': '',
        'items': ['None', 'None', 'None'],
        'music': '',
        'battle_field': 'Battle Type',
        'battle_value': 'Doubles',
        'mugshot': 'None',
        'starting_statuses': [],
        'pool_rules': 'None',
        'party_size': '',
        'ai_flags': [],
    })
    save_trainer_sections(project, sections)
    output = trainers_path.read_text(encoding='utf-8')
    assert 'Battle Type: Doubles' in output
    assert 'Double Battle:' not in output


def test_metadata_key_and_name_casing_are_preserved(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'src/data').mkdir(parents=True)
    trainers_path = project / 'src/data/trainers.party'
    trainers_path.write_text(
        '=== TRAINER_KAREN_1 ===\n'
        'Name: KAREN\n'
        'AI: Check Bad Move\n\n'
        'Abra\n'
        '- Psychic\n',
        encoding='utf-8',
    )

    section = load_trainer_sections(project)[0]
    state = trainer_section_to_form_state(section)
    assert state['name'] == 'KAREN'

    apply_form_state_to_metadata(section, {
        'name': 'KAREN',
        'pic': '',
        'class_name': '',
        'gender': '',
        'items': ['None', 'None', 'None'],
        'music': '',
        'battle_field': 'Double Battle',
        'battle_value': 'No',
        'mugshot': 'None',
        'starting_statuses': [],
        'pool_rules': 'None',
        'party_size': '',
        'ai_flags': ['Check Bad Move'],
    })
    save_trainer_sections(project, [section])
    output = trainers_path.read_text(encoding='utf-8')
    assert 'Name: KAREN' in output
    assert 'AI: Check Bad Move' in output
    assert 'Ai:' not in output


def test_backend_bootstrap_sorts_trainers_alphabetically(tmp_path: Path) -> None:
    from obstagoon.config import SiteConfig
    from obstagoon.trainer_editor import _TrainerEditorBackend

    project = tmp_path / 'proj'
    (project / 'include/constants').mkdir(parents=True)
    (project / 'include').mkdir(exist_ok=True)
    (project / 'src/data').mkdir(parents=True)
    (project / 'src/data/trainers.party').write_text(
        '=== TRAINER_ZED_1 ===\nName: ZED\n\nPikachu\n- Thunderbolt\n\n'
        '=== TRAINER_ASH_1 ===\nName: ASH\n\nBulbasaur\n- Tackle\n',
        encoding='utf-8',
    )

    config = SiteConfig(project_dir=project, dist_dir=tmp_path / 'dist', site_title='Test', trainer_editor=True)
    config.ensure()
    backend = _TrainerEditorBackend(config=config, model=_empty_model())
    ids = [entry['display_id'] for entry in backend.bootstrap_payload()['trainers']]
    assert ids == ['ASH_1', 'ZED_1']


def test_save_trainer_sections_preserves_original_file_order(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'src/data').mkdir(parents=True)
    trainers_path = project / 'src/data/trainers.party'
    trainers_path.write_text(
        '=== TRAINER_ZED_1 ===\nName: ZED\n\nPikachu\n- Thunderbolt\n\n'
        '=== TRAINER_ASH_1 ===\nName: ASH\n\nBulbasaur\n- Tackle\n',
        encoding='utf-8',
    )

    sections = load_trainer_sections(project)
    apply_form_state_to_metadata(sections[0], {
        'name': 'ASH',
        'pic': '',
        'class_name': '',
        'gender': '',
        'items': ['None', 'None', 'None'],
        'music': '',
        'battle_field': 'Double Battle',
        'battle_value': 'No',
        'mugshot': 'None',
        'starting_statuses': [],
        'pool_rules': 'None',
        'party_size': '',
        'ai_flags': [],
    })
    save_trainer_sections(project, sections)
    output = trainers_path.read_text(encoding='utf-8')
    assert output.index('=== TRAINER_ZED_1 ===') < output.index('=== TRAINER_ASH_1 ===')


def test_save_trainer_sections_preserves_header_preamble(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'src/data').mkdir(parents=True)
    trainers_path = project / 'src/data/trainers.party'
    trainers_path.write_text(
        """// header comment
#include "constants/trainers.h"

=== TRAINER_NONE ===
Name: NONE

=== TRAINER_KAREN_1 ===
Name: KAREN

Abra
- Psychic
""",
        encoding='utf-8',
    )

    sections = load_trainer_sections(project)
    apply_form_state_to_metadata(sections[0], {
        'name': 'KAREN',
        'pic': '',
        'class_name': '',
        'gender': '',
        'items': ['None', 'None', 'None'],
        'music': '',
        'battle_field': 'Double Battle',
        'battle_value': 'No',
        'mugshot': 'None',
        'starting_statuses': [],
        'pool_rules': 'None',
        'party_size': '',
        'ai_flags': [],
    })
    save_trainer_sections(project, sections)
    output = trainers_path.read_text(encoding='utf-8')
    assert output.startswith('// header comment\n#include "constants/trainers.h"\n\n=== TRAINER_NONE ===')
    assert '=== TRAINER_NONE ===\nName: NONE\n\n=== TRAINER_KAREN_1 ===' in output
    assert output.count('=== TRAINER_NONE ===') == 1


def test_save_trainer_sections_preserves_everything_through_trainer_none(tmp_path: Path) -> None:
    project = tmp_path / 'proj'
    (project / 'src/data').mkdir(parents=True)
    trainers_path = project / 'src/data/trainers.party'
    original_prefix = """// header comment
#define SOME_MACRO 1

=== TRAINER_NONE ===
Name: NONE
Class: Placeholder

Custom Placeholder Mon
- Splash
"""
    trainers_path.write_text(
        original_prefix + """

=== TRAINER_BOB_1 ===
Name: BOB

Pikachu
- Thunderbolt
""",
        encoding='utf-8',
    )

    sections = load_trainer_sections(project)
    assert [section.trainer_id for section in sections] == ['TRAINER_BOB_1']
    apply_form_state_to_metadata(sections[0], {
        'name': 'BOB',
        'pic': '',
        'class_name': '',
        'gender': '',
        'items': ['None', 'None', 'None'],
        'music': '',
        'battle_field': 'Double Battle',
        'battle_value': 'No',
        'mugshot': 'None',
        'starting_statuses': [],
        'pool_rules': 'None',
        'party_size': '',
        'ai_flags': [],
    })
    save_trainer_sections(project, sections)

    output = trainers_path.read_text(encoding='utf-8')
    assert output.startswith(original_prefix.rstrip("\n") + "\n\n=== TRAINER_BOB_1 ===")


def test_backend_bootstrap_includes_all_trainer_pics_from_refs_and_sections(tmp_path: Path) -> None:
    from obstagoon.config import SiteConfig
    from obstagoon.trainer_editor import _TrainerEditorBackend

    project = tmp_path / 'proj'
    (project / 'include/constants').mkdir(parents=True)
    (project / 'include').mkdir(exist_ok=True)
    (project / 'src/data').mkdir(parents=True)
    (project / 'include/constants/trainers.h').write_text(
        """enum __attribute__((packed)) TrainerPicID {
    TRAINER_PIC_DRAGON_TAMER,
    TRAINER_PIC_LEADER_WINONA,
    TRAINER_PIC_FRONT_COUNT,
};
""",
        encoding='utf-8',
    )
    (project / 'src/data/trainers.party').write_text(
        """=== TRAINER_WINONA_1 ===
Pic: Leader Winona

Altaria
- Fly
""",
        encoding='utf-8',
    )
    config = SiteConfig(project_dir=project, dist_dir=tmp_path / 'dist', site_title='Test', trainer_editor=True)
    config.ensure()
    backend = _TrainerEditorBackend(config=config, model=_empty_model())
    assert backend.references['trainer_pics'] == ['Dragon Tamer', 'Leader Winona']


def test_species_details_do_not_let_form_aliases_overwrite_base_species() -> None:
    from obstagoon.trainer_editor import _species_details

    base_tauros = SimpleNamespace(
        species_id='SPECIES_TAUROS',
        name='Tauros',
        base_species=None,
        form_name='',
        gender_ratio='',
        types=['Normal'],
        abilities=['Intimidate', 'Anger Point', 'Sheer Force'],
        learnsets=SimpleNamespace(teachable=[]),
        stats={'hp': 75, 'atk': 100, 'def': 95, 'spa': 40, 'spd': 70, 'spe': 110},
    )
    aqua_tauros = SimpleNamespace(
        species_id='SPECIES_TAUROS_PALDEA_AQUA',
        name='Tauros',
        base_species='SPECIES_TAUROS',
        form_name='Paldea Aqua',
        gender_ratio='',
        types=['Fighting', 'Water'],
        abilities=['Intimidate', 'Anger Point', 'Cud Chew'],
        learnsets=SimpleNamespace(teachable=[]),
        stats={'hp': 75, 'atk': 110, 'def': 105, 'spa': 30, 'spd': 70, 'spe': 100},
    )
    base_linoone = SimpleNamespace(
        species_id='SPECIES_LINOONE',
        name='Linoone',
        base_species=None,
        form_name='',
        gender_ratio='',
        types=['Normal'],
        abilities=['Pickup', 'Gluttony', 'Quick Feet'],
        learnsets=SimpleNamespace(teachable=[]),
        stats={'hp': 78, 'atk': 70, 'def': 61, 'spa': 50, 'spd': 61, 'spe': 100},
    )
    galar_linoone = SimpleNamespace(
        species_id='SPECIES_LINOONE_GALAR',
        name='Linoone',
        base_species='SPECIES_LINOONE',
        form_name='Galar',
        gender_ratio='',
        types=['Dark', 'Normal'],
        abilities=['Pickup', 'Gluttony', 'Quick Feet'],
        learnsets=SimpleNamespace(teachable=[]),
        stats={'hp': 78, 'atk': 70, 'def': 61, 'spa': 50, 'spd': 61, 'spe': 100},
    )

    model = SimpleNamespace(species={
        'SPECIES_TAUROS': base_tauros,
        'SPECIES_TAUROS_PALDEA_AQUA': aqua_tauros,
        'SPECIES_LINOONE': base_linoone,
        'SPECIES_LINOONE_GALAR': galar_linoone,
    })
    site_generator = SimpleNamespace(_display_graphics_for_species=lambda _rec: {})

    details = _species_details(site_generator, model)

    assert details['Tauros']['types'] == ['Normal']
    assert details['Tauros-Paldea-Aqua']['types'] == ['Fighting', 'Water']
    assert details['Linoone']['types'] == ['Normal']
    assert details['Linoone-Galar']['types'] == ['Dark', 'Normal']
    assert details['SPECIES_TAUROS']['types'] == ['Normal']
    assert details['SPECIES_TAUROS_PALDEA_AQUA']['types'] == ['Fighting', 'Water']
    assert details['tauros-paldea-aqua']['types'] == ['Fighting', 'Water']
    assert details['linoone-galar']['types'] == ['Dark', 'Normal']


def test_trainer_editor_held_items_exclude_key_items_and_round_trip(tmp_path: Path) -> None:
    from obstagoon.trainer_editor import _parse_pokemon_block_editor, _serialize_pokemon_block

    refs = load_trainer_editor_references(tmp_path / 'proj_missing_headers', _empty_model())
    assert 'Full Restore' in refs['held_items']
    assert 'Sitrus Berry' in refs['held_items']
    assert 'Bicycle' not in refs['held_items']

    mon = _parse_pokemon_block_editor('''Slaking @ Sitrus Berry
Level: 57
- Slack Off
''')
    assert mon['held_item'] == 'Sitrus Berry'
    assert mon['ball'] == ''
    assert _serialize_pokemon_block(mon).splitlines()[0] == 'Slaking @ Sitrus Berry'


def test_trainer_editor_species_define_aliases_map_unknown_species_to_canonical_forms(tmp_path: Path) -> None:
    from obstagoon.config import SiteConfig
    from obstagoon.trainer_editor import _TrainerEditorBackend

    project = tmp_path / 'proj'
    (project / 'include/constants').mkdir(parents=True)
    (project / 'include').mkdir(exist_ok=True)
    (project / 'src/data').mkdir(parents=True)
    (project / 'include/constants/species.h').write_text(
        """#define SPECIES_TORNADUS SPECIES_TORNADUS_INCARNATE
#define SPECIES_TORNADUS_INCARNATE 641
#define SPECIES_LANDORUS SPECIES_LANDORUS_INCARNATE
#define SPECIES_LANDORUS_INCARNATE 645
#define SPECIES_LANDORUS_THERIAN 1102
""",
        encoding='utf-8',
    )
    (project / 'src/data/trainers.party').write_text(
        """=== TRAINER_TEST_1 ===
Name: TEST

Tornadus (M) @ Covert Cloak
Ability: Prankster
- Tailwind

Landorus-Therian (M) @ Choice Scarf
Ability: Intimidate
- U-turn
""",
        encoding='utf-8',
    )

    model = _empty_model()
    tornadus = SimpleNamespace(
        species_id='SPECIES_TORNADUS_INCARNATE',
        name='Tornadus',
        base_species=None,
        form_name='Incarnate',
        gender_ratio='',
        types=['Flying'],
        abilities=['Prankster'],
        learnsets=SimpleNamespace(teachable=[]),
        stats={'hp': 79, 'atk': 115, 'def': 70, 'spa': 125, 'spd': 80, 'spe': 111},
        graphics={},
    )
    landorus_therian = SimpleNamespace(
        species_id='SPECIES_LANDORUS_THERIAN',
        name='Landorus',
        base_species='SPECIES_LANDORUS_INCARNATE',
        form_name='Therian',
        gender_ratio='',
        types=['Ground', 'Flying'],
        abilities=['Intimidate'],
        learnsets=SimpleNamespace(teachable=[]),
        stats={'hp': 89, 'atk': 145, 'def': 90, 'spa': 105, 'spd': 80, 'spe': 91},
        graphics={},
    )
    model.species = {
        'SPECIES_TORNADUS_INCARNATE': tornadus,
        'SPECIES_LANDORUS_THERIAN': landorus_therian,
    }

    config = SiteConfig(project_dir=project, dist_dir=tmp_path / 'dist', site_title='Test', trainer_editor=True)
    config.ensure()
    backend = _TrainerEditorBackend(config=config, model=model)

    refs = backend.references['species_aliases']
    assert refs['Tornadus'] == 'Tornadus-Incarnate'
    assert refs['SPECIES_TORNADUS'] == 'Tornadus-Incarnate'

    state = backend.get_trainer_state('TEST_1')
    assert state['pokemon'][0]['species'] == 'Tornadus-Incarnate'
    assert state['pokemon'][1]['species'] == 'Landorus-Therian'



def test_party_pool_tags_round_trip_with_multiple_tags() -> None:
    block = (
        "Whimsicott @ Covert Cloak\n"
        "Ability: Prankster\n"
        "EVs: 252 HP / 252 Def / 4 SpA\n"
        "Bold Nature\n"
        "IVs: 0 Atk\n"
        "Tags: Lead / Prankster / Speed Control\n"
        "- Tailwind\n"
        "- Encore\n"
    )

    mon = _parse_pokemon_block_editor(block)
    assert mon['tags'] == ['Lead', 'Prankster', 'Speed Control']

    serialized = _serialize_pokemon_block(mon)
    assert serialized is not None
    assert 'Tags: Lead / Prankster / Speed Control' in serialized


def test_browser_tag_checkbox_attribute_matches_collection_selector() -> None:
    assert "querySelectorAll('[data-tag-box]:checked')" in BROWSER_APP_HTML
    assert "setAttribute('data-tag-box','1')" in BROWSER_APP_HTML


def test_browser_repopulate_uses_seed_tags_on_initial_render() -> None:
    assert "function repopulateMonDependentOptions(card,seedMon=null)" in BROWSER_APP_HTML
    assert "const selectedTags=new Set(mon.tags||[])" in BROWSER_APP_HTML
    assert "repopulateMonDependentOptions(card,mon);" in BROWSER_APP_HTML
