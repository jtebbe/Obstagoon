from obstagoon.normalize import evolution_label, infer_form_name


def test_infer_form_name():
    assert infer_form_name('SPECIES_DEOXYS_ATTACK', 'SPECIES_DEOXYS') == 'Attack'


def test_evolution_label():
    assert evolution_label('EVO_ITEM', 'ITEM_FIRE_STONE') == 'Use item: Fire Stone'
