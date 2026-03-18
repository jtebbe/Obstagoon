from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Evolution:
    method: str
    param: str | None
    target_species: str
    method_label: str
    target_species_id: str | None = None


@dataclass(slots=True)
class LearnsetBucket:
    level_up: list[dict[str, Any]] = field(default_factory=list)
    egg: list[str] = field(default_factory=list)
    teachable: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class SpeciesRecord:
    species_id: str
    national_dex: int | None
    name: str
    category: str | None = None
    description: str | None = None
    types: list[str] = field(default_factory=list)
    abilities: list[str] = field(default_factory=list)
    ability_slots: list[str | None] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)
    catch_rate: str | None = None
    exp_yield: str | None = None
    gender_ratio: str | None = None
    growth_rate: str | None = None
    egg_groups: list[str] = field(default_factory=list)
    graphics: dict[str, Any] = field(default_factory=dict)
    evolutions: list[Evolution] = field(default_factory=list)
    learnsets: LearnsetBucket = field(default_factory=LearnsetBucket)
    forms: list[str] = field(default_factory=list)
    base_species: str | None = None
    form_name: str | None = None
    form_index: int | None = None
    form_changes: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class MoveRecord:
    move_id: str
    name: str
    description: str | None = None
    type: str | None = None
    power: str | None = None
    accuracy: str | None = None
    pp: str | None = None
    category: str | None = None
    flags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AbilityRecord:
    ability_id: str
    name: str
    description: str | None = None


@dataclass(slots=True)
class ItemLocation:
    location: str
    source: str


@dataclass(slots=True)
class ItemRecord:
    item_id: str
    name: str
    description: str | None = None
    pocket: str | None = None
    price: str | None = None
    locations: list[ItemLocation] = field(default_factory=list)


@dataclass(slots=True)
class EncounterSlot:
    species: str
    min_level: str | None = None
    max_level: str | None = None
    rate: str | None = None
    method: str | None = None


@dataclass(slots=True)
class EncounterArea:
    map_name: str
    display_name: str
    encounters: dict[str, list[EncounterSlot]] = field(default_factory=dict)


@dataclass(slots=True)
class SpriteAsset:
    species_id: str
    kind: str
    source: str
    resolved_path: str | None = None


@dataclass(slots=True)
class TrainerPokemonRecord:
    species_id: str | None
    species_name: str
    picture: str | None = None
    types: list[str] = field(default_factory=list)
    ability: str | None = None
    tera_type: str | None = None
    evs: dict[str, str] = field(default_factory=dict)
    ivs: dict[str, str] = field(default_factory=dict)
    held_item: str | None = None
    moves: list[str] = field(default_factory=list)
    nickname: str | None = None
    level: str | None = None


@dataclass(slots=True)
class TrainerRecord:
    trainer_id: str
    name: str
    picture: str | None = None
    location: str | None = None
    battle_type: str | None = None
    has_party_pool: bool = False
    party_size: str | None = None
    pool_rules: str | None = None
    pokemon: list[TrainerPokemonRecord] = field(default_factory=list)
    class_name: str | None = None
    raw_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ObstagoonModel:
    species: dict[str, SpeciesRecord]
    moves: dict[str, MoveRecord]
    abilities: dict[str, AbilityRecord]
    items: dict[str, ItemRecord]
    types: dict[str, str]
    encounters: list[EncounterArea]
    sprites: list[SpriteAsset]
    species_to_national: dict[str, int]
    national_to_species: dict[int, str]
    forms: dict[str, list[str]]
    trainers: dict[str, TrainerRecord] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
