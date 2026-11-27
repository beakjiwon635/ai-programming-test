from pathlib import Path

import pandas as pd
from analysis import 정제, 반별평균

기준폴더 = Path(__file__).resolve().parent

본 = 정제(pd.read_csv(기준폴더 / "scores_2026.csv"))
미니 = 정제(pd.read_csv(기준폴더 / "mini.csv"))


def test_cleaned_data_has_100_rows():
    assert len(본) == 100


def test_classes_are_two_values():
    assert sorted(본["반"].unique()) == ["1반", "2반"]


def test_grouped_score_sum_matches_total():
    assert 본.groupby("반")["점수"].sum().sum() == 본["점수"].sum()


def test_manual_average_matches():
    assert 반별평균(미니)["1반"] == 80.0


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([str(Path(__file__).resolve()), "-v"]))
