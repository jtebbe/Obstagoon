from obstagoon.normalize import evolution_label, infer_form_name, normalize_move_metric




def test_infer_form_name():
    assert infer_form_name('SPECIES_DEOXYS_ATTACK', 'SPECIES_DEOXYS') == 'Attack'


def test_evolution_label():
    assert evolution_label('EVO_ITEM', 'ITEM_FIRE_STONE') == 'Use item: Fire Stone'


def test_normalize_move_metric_zero_and_one_render_as_dash():
    assert normalize_move_metric(0) is None
    assert normalize_move_metric("0") is None
    assert normalize_move_metric(1) is None
    assert normalize_move_metric("1") is None
    assert normalize_move_metric(5) == "5"
