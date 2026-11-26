"""명세서 6칸을 바탕으로 작성한 pytest 단위 테스트 (B).

A와 동일하게 기존 load_scores.py의 load_scores 함수를 검사합니다.
이 파일에는 load_scores 구현 코드가 없습니다.

실행: python -m pytest -v test_ai_B.py
"""

import csv
from pathlib import Path

import pytest

from load_scores import load_scores


def make_csv(tmp_path, content, encoding="utf-8"):
    path = tmp_path / "test_scores.csv"
    path.write_text(content, encoding=encoding)
    return path


# 1. 정상 입력

def test_normal_scores_and_decimal(tmp_path):
    path = make_csv(tmp_path, "name,score\n김하나,88\n이둘,88.5\n박셋,75\n")
    assert load_scores(path) == (
        [("김하나", 88.0), ("이둘", 88.5), ("박셋", 75.0)], []
    )


def test_header_only_returns_empty_lists(tmp_path):
    path = make_csv(tmp_path, "name,score\n")
    assert load_scores(path) == ([], [])


def test_utf8_bom_is_allowed(tmp_path):
    path = make_csv(tmp_path, "name,score\n학생,90\n", encoding="utf-8-sig")
    assert load_scores(path) == ([("학생", 90.0)], [])


def test_quoted_comma_and_whitespace(tmp_path):
    path = make_csv(tmp_path, 'name,score\n"김,학생",89\n  학생  ,  77  \n')
    assert load_scores(path) == ([("김,학생", 89.0), ("학생", 77.0)], [])


def test_original_csv_is_not_modified(tmp_path):
    path = make_csv(tmp_path, "name,score\n학생,80\n누락,\n")
    before = path.read_bytes()
    load_scores(path)
    assert path.read_bytes() == before


# 2. 예외: 파일·헤더·CSV 형식 오류

def test_missing_file_raises_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_scores(tmp_path / "missing.csv")


@pytest.mark.parametrize("header", ["", "score,name", "Name,score", "name,score,age"])
def test_wrong_header_raises_error(tmp_path, header):
    path = make_csv(tmp_path, header + "\n학생,80\n")
    with pytest.raises(ValueError):
        load_scores(path)


def test_invalid_csv_quotes_raise_error(tmp_path):
    path = make_csv(tmp_path, 'name,score\n"닫히지 않은 이름,80\n')
    with pytest.raises(csv.Error):
        load_scores(path)


def test_invalid_encoding_raises_error(tmp_path):
    path = tmp_path / "invalid.csv"
    path.write_bytes(b"name,score\n\xff,80\n")
    with pytest.raises(UnicodeDecodeError):
        load_scores(path)


# 3. 잘못된 행 제외 및 이유·줄 번호 기록

def test_wrong_column_count_is_skipped(tmp_path):
    path = make_csv(tmp_path, "name,score\n하나\n둘,70,추가\n셋,90\n")
    kept, skipped = load_scores(path)
    assert kept == [("셋", 90.0)]
    assert [number for number, reason in skipped] == [2, 3]
    assert all("열 개수" in reason for number, reason in skipped)


@pytest.mark.parametrize("bad_row", [",90", "학생,"])
def test_missing_name_or_score_is_skipped(tmp_path, bad_row):
    path = make_csv(tmp_path, f"name,score\n{bad_row}\n정상,80\n")
    kept, skipped = load_scores(path)
    assert kept == [("정상", 80.0)]
    assert len(skipped) == 1
    assert skipped[0][0] == 2
    assert "누락" in skipped[0][1]


@pytest.mark.parametrize("bad_score", ["결석", "abc", "7 2"])
def test_non_numeric_score_is_skipped(tmp_path, bad_score):
    path = make_csv(tmp_path, f"name,score\n학생,{bad_score}\n정상,80\n")
    kept, skipped = load_scores(path)
    assert kept == [("정상", 80.0)]
    assert len(skipped) == 1
    assert "숫자가 아닌" in skipped[0][1]


def test_duplicate_name_keeps_first_valid_score(tmp_path):
    path = make_csv(tmp_path, "name,score\n학생,80\n학생,90\n")
    kept, skipped = load_scores(path)
    assert kept == [("학생", 80.0)]
    assert skipped == [(3, "중복 이름")]


def test_invalid_first_score_does_not_block_later_valid_score(tmp_path):
    path = make_csv(tmp_path, "name,score\n학생,105\n학생,80\n")
    kept, skipped = load_scores(path)
    assert kept == [("학생", 80.0)]
    assert skipped == [(2, "점수 범위 오류")]


def test_multiline_record_reports_ending_line_number(tmp_path):
    path = make_csv(tmp_path, 'name,score\n"홍\n길동",abc\n정상,70\n')
    kept, skipped = load_scores(path)
    assert kept == [("정상", 70.0)]
    assert skipped == [(3, "숫자가 아닌 점수")]


# 4. 경계값: 0점과 100점 포함, 소수 허용, 유한수만 인정

@pytest.mark.parametrize("score,expected", [("0", 0.0), ("100", 100.0), ("88.5", 88.5)])
def test_valid_boundaries(tmp_path, score, expected):
    path = make_csv(tmp_path, f"name,score\n학생,{score}\n")
    assert load_scores(path) == ([("학생", expected)], [])


@pytest.mark.parametrize("score", ["-0.1", "100.1", "105", "NaN", "Infinity", "-inf"])
def test_invalid_boundaries_are_skipped(tmp_path, score):
    path = make_csv(tmp_path, f"name,score\n학생,{score}\n정상,80\n")
    kept, skipped = load_scores(path)
    assert kept == [("정상", 80.0)]
    assert skipped == [(2, "점수 범위 오류")]


def test_mixed_rows_keep_valid_and_record_invalid(tmp_path):
    path = make_csv(
        tmp_path,
        'name,score\n김하나,88\n초과,105\n누락,\n"최,네번",77\n'
        '김하나,91\n마이너스,-5\n문자,결석\n열,30,추가\n',
    )
    kept, skipped = load_scores(path)
    assert kept == [("김하나", 88.0), ("최,네번", 77.0)]
    assert [number for number, reason in skipped] == [3, 4, 6, 7, 8, 9]
    assert all(reason for number, reason in skipped)
