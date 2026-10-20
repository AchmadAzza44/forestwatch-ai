import numpy as np
import pytest

from pipeline.change_detection import DetectionParams, composite, detect_change, ndvi, nbr, valid_mask_from_scl

PIX = 400.0  # 20 m x 20 m = 400 m2; 1 ha = 25 piksel


def scene(shape, nir, red, swir):
    return {"B08": np.full(shape, nir, "float32"), "B04": np.full(shape, red, "float32"), "B12": np.full(shape, swir, "float32")}


def test_index_formulas_known_values():
    assert ndvi(np.array([0.8]), np.array([0.2]))[0] == pytest.approx(0.6, abs=1e-5)
    assert nbr(np.array([0.5]), np.array([0.1]))[0] == pytest.approx(0.6667, abs=1e-3)
    assert ndvi(np.array([0.0]), np.array([0.0]))[0] == 0  # tidak membagi nol


def test_scl_valid_classes():
    scl = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
    assert valid_mask_from_scl(scl).tolist() == [False] * 4 + [True] * 4 + [False] * 4


def test_composite_ignores_clouds_and_counts_valid_obs():
    shape = (2, 2)
    a = {"B04": np.full(shape, 1000.0), "B08": np.full(shape, 4000.0)}
    b = {"B04": np.full(shape, 3000.0), "B08": np.full(shape, 9000.0)}  # pengamatan berawan (dibuang)
    c = {"B04": np.full(shape, 1200.0), "B08": np.full(shape, 4200.0)}
    scl_a, scl_b, scl_c = np.full(shape, 4), np.full(shape, 9), np.full(shape, 4)
    scl_b[0, 0] = 4  # satu piksel pada scene b valid
    out, n = composite([a, b, c], [scl_a, scl_b, scl_c], buffer_px=0)
    assert n.tolist() == [[3, 2], [2, 2]]
    assert out["B04"][1, 1] == pytest.approx(0.11)  # median(1000, 1200) -> 1100 / 10000
    assert out["B08"][0, 0] == pytest.approx(0.42)  # median(4000, 9000, 4200)
    allcloud, n2 = composite([a], [np.full(shape, 9)], buffer_px=0)
    assert np.isnan(allcloud["B04"]).all() and (n2 == 0).all()


def test_composite_validates_shapes():
    with pytest.raises(ValueError):
        composite([], [])
    with pytest.raises(ValueError):
        composite([{"B04": np.zeros((2, 2))}], [np.zeros((3, 3))])


def test_detects_known_clearing_and_ignores_stable_forest_and_small_noise():
    shape = (60, 60)
    before = scene(shape, 0.45, 0.04, 0.10)          # hutan rapat: NDVI ~0.84, NBR ~0.64
    after = scene(shape, 0.45, 0.04, 0.10)
    for k in after:                                    # lahan terbuka 20x20 piksel = 400 piksel = 16 ha
        after[k][10:30, 10:30] = {"B08": 0.20, "B04": 0.15, "B12": 0.25}[k]
    after["B08"][50, 50] = 0.20; after["B04"][50, 50] = 0.15; after["B12"][50, 50] = 0.25  # satu piksel derau
    n = np.ones(shape, "int16")
    res = detect_change(before, after, n, n, PIX, DetectionParams(min_area_ha=1.0))
    assert len(res["clusters"]) == 1
    c = res["clusters"][0]
    assert c["pixels"] == 400 and c["area_ha"] == pytest.approx(16.0)
    assert c["mean_dnbr"] > 0.27 and c["mean_dndvi"] < -0.2
    assert res["changed_ha"] == pytest.approx(16.0) and res["observed_fraction"] == 1.0
    assert not res["mask"][50, 50]


def test_non_forest_before_is_not_reported():
    shape = (40, 40)
    before = scene(shape, 0.25, 0.15, 0.25)           # sudah terbuka sebelumnya (NDVI 0.25)
    after = scene(shape, 0.10, 0.20, 0.30)
    n = np.ones(shape, "int16")
    assert detect_change(before, after, n, n, PIX)["clusters"] == []


def test_pixels_without_valid_observations_are_never_detected():
    shape = (40, 40)
    before, after = scene(shape, 0.45, 0.04, 0.10), scene(shape, 0.20, 0.15, 0.25)
    n_before, n_after = np.ones(shape, "int16"), np.ones(shape, "int16")
    n_after[:, :20] = 0                                # setengah area tertutup awan pada periode akhir
    res = detect_change(before, after, n_before, n_after, PIX)
    assert res["observed_fraction"] == pytest.approx(0.5)
    assert res["mask"][:, :20].sum() == 0 and res["mask"][:, 20:].sum() > 0


def test_thresholds_control_detection_and_are_recorded():
    shape = (40, 40)
    before, after = scene(shape, 0.45, 0.04, 0.10), scene(shape, 0.40, 0.06, 0.13)  # perubahan kecil
    n = np.ones(shape, "int16")
    assert detect_change(before, after, n, n, PIX)["clusters"] == []
    loose = DetectionParams(dnbr_min=0.01, dndvi_max=-0.001)
    res = detect_change(before, after, n, n, PIX, loose)
    assert res["clusters"] and res["params"]["dnbr_min"] == 0.01


def test_cloud_buffer_removes_pixels_around_invalid_ones():
    shape = (11, 11)
    band = {"B04": np.full(shape, 1000.0)}
    scl = np.full(shape, 4)
    scl[5, 5] = 9  # satu piksel awan di tengah
    _, n0 = composite([band], [scl], buffer_px=0)
    _, n3 = composite([band], [scl], buffer_px=3)
    assert (n0 == 0).sum() == 1
    assert (n3 == 0).sum() == 49  # blok 7x7 (piksel awan + buffer 3)
    assert n3[0, 0] == 1  # jauh dari awan tetap valid
