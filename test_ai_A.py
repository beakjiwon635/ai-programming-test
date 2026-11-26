import pytest

from load_scores import load_scores


def test_load_scores_keeps_valid_rows_and_ignores_header_and_blank_lines(tmp_path):
	path = tmp_path / "scores.csv"
	path.write_text(
		"이름,점수\n홍길동,85\n\n 김철수 , 0 \n이영희,100\n",
		encoding="utf-8-sig",
	)

	kept, skipped = load_scores(path)

	assert kept == [("홍길동", 85), ("김철수", 0), ("이영희", 100)]
	assert skipped == []


@pytest.mark.parametrize("score", [0, 100])
def test_load_scores_accepts_score_boundaries(tmp_path, score):
	path = tmp_path / "boundary.csv"
	path.write_text(f"name,score\n학생,{score}\n", encoding="utf-8")

	assert load_scores(path) == ([("학생", score)], [])


def test_load_scores_records_invalid_rows_with_line_numbers_and_reasons(tmp_path):
	path = tmp_path / "invalid.csv"
	path.write_text(
		"name,score\n"
		"only-one-column\n"
		"too,many,columns\n"
		"   ,80\n"
		"학생,   \n"
		"학생,abc\n"
		"학생,-1\n"
		"학생,101\n"
		"정상,75\n",
		encoding="utf-8",
	)

	kept, skipped = load_scores(path)

	assert kept == [("정상", 75)]
	assert skipped == [
		(2, "only-one-column", "열 개수가 2가 아님"),
		(3, "too,many,columns", "열 개수가 2가 아님"),
		(4, "   ,80", "이름이 비어 있음"),
		(5, "학생,   ", "점수가 비어 있음"),
		(6, "학생,abc", "점수가 정수가 아님"),
		(7, "학생,-1", "점수가 0~100 밖"),
		(8, "학생,101", "점수가 0~100 밖"),
	]


def test_load_scores_raises_file_not_found_for_missing_path(tmp_path):
	with pytest.raises(FileNotFoundError):
		load_scores(tmp_path / "missing.csv")


def test_load_scores_returns_empty_results_for_header_only_file(tmp_path):
	path = tmp_path / "header-only.csv"
	path.write_text("name,score\n", encoding="utf-8")

	assert load_scores(path) == ([], [])
