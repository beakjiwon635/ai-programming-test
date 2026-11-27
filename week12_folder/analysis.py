from pathlib import Path

import pandas as pd

기준폴더 = Path(__file__).resolve().parent


def 정제(df):
    df = df.copy()
    print("시작:", len(df))

    # 점수가 비어 있는 행을 삭제한다.
    df = df.dropna(subset=["점수"])
    print("빈 칸 제거:", len(df))

    # 모든 열이 완전히 같은 중복 행은 하나만 남긴다.
    df = df.drop_duplicates()
    print("중복 제거:", len(df))

    # 반과 과목 값 앞뒤의 공백을 제거한다.
    df["반"] = df["반"].str.strip()
    df["과목"] = df["과목"].str.strip()

    # 점수가 0~100 범위인 행만 남긴다.
    df = df[(df["점수"] >= 0) & (df["점수"] <= 100)]
    print("범위 밖 제거:", len(df))

    return df


def 반별평균(df):
    통계표 = df.groupby("반")["점수"].agg(
        ["count", "mean", "median", "max"]
    ).round(2)
    print("반별 통계표:")
    print(통계표)
    return 통계표["mean"]


if __name__ == "__main__":
    df = 정제(pd.read_csv(기준폴더 / "scores_2026.csv"))
    print(sorted(df["반"].unique()))
    print(sorted(df["과목"].unique()))

    수학_df = df[df["과목"] == "수학"]
    print("수학 행 수:", len(수학_df))

    print("반별 점수 평균:")
    print(df.groupby("반")["점수"].mean())

    print("과목·반별 점수 평균:")
    print(df.groupby(["과목", "반"])["점수"].mean())

    반별평균(df)
    print(df.groupby("반")["점수"].sum().sum())
    print(df["점수"].sum())

    print(df.groupby("반")["점수"].count().sum())
    print(len(df))

    print(df[(df["반"] == "1반") & (df["과목"] == "수학")]["점수"])

    print(len(df[(df["반"] == "1반") & (df["점수"] >= 90)]))

    미니 = 정제(pd.read_csv(기준폴더 / "mini.csv"))
    print(반별평균(미니))
