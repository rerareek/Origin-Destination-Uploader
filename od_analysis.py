"""
JICT Origin & Destination Analysis — Backend Logic
Division  : Business Development & Marketing Intelligence (BDMI)
"""

import pandas as pd
import pycountry

TOP_N = 13


def compute_teu(df: pd.DataFrame) -> pd.DataFrame:
    df["FULL_IMPORT"] = (
        df["SIZED_20_FULL_DISC"]
        + df["SIZED_40_FULL_DISC"] * 2
        + df["SIZED_45_FULL_DISC"] * 2.25
    )
    df["EMPTY_IMPORT"] = (
        df["SIZED_20_EMPTY_DISC"]
        + df["SIZED_40_EMPTY_DISC"] * 2
        + df["SIZED_45_EMPTY_DISC"] * 2.25
    )
    df["TOTAL_IMPORT"] = df["FULL_IMPORT"] + df["EMPTY_IMPORT"]

    df["FULL_EXPORT"] = (
        df["SIZED_20_FULL_LOAD"]
        + df["SIZED_40_FULL_LOAD"] * 2
        + df["SIZED_45_FULL_LOAD"] * 2.25
    )
    df["EMPTY_EXPORT"] = (
        df["SIZED_20_EMPTY_LOAD"]
        + df["SIZED_40_EMPTY_LOAD"] * 2
        + df["SIZED_45_EMPTY_LOAD"] * 2.25
    )
    df["TOTAL_EXPORT"] = df["FULL_EXPORT"] + df["EMPTY_EXPORT"]
    return df


def convert_country(code: str) -> str:
    try:
        return pycountry.countries.get(alpha_2=code.upper()).name.upper()
    except Exception:
        return code.upper()


def group_by_country(df: pd.DataFrame):
    grouped = df.groupby("COUNTRY", as_index=False).sum(numeric_only=True)
    grouped["COUNTRY_NAME"] = grouped["COUNTRY"].apply(convert_country)

    total_import = grouped["TOTAL_IMPORT"].sum()
    total_export = grouped["TOTAL_EXPORT"].sum()

    grouped["%IMPORT"] = (grouped["TOTAL_IMPORT"] / total_import) * 100
    grouped["%EXPORT"] = (grouped["TOTAL_EXPORT"] / total_export) * 100

    return grouped, total_import, total_export


def top13(data: pd.DataFrame, percent_col: str, top_n: int = TOP_N, exclude_indonesia: bool = True) -> pd.DataFrame:
    top = data.sort_values(percent_col, ascending=False).reset_index(drop=True)
    top_df = top.head(top_n).copy()

    if exclude_indonesia and "INDONESIA" in top_df["COUNTRY_NAME"].values:
        top_df = top_df[top_df["COUNTRY_NAME"] != "INDONESIA"]
        top_df = pd.concat([top_df, top.iloc[top_n:top_n + 1]])

    top13_df = top_df.head(top_n).reset_index(drop=True)

    others = data[~data["COUNTRY_NAME"].isin(top13_df["COUNTRY_NAME"])]
    others_sum = others[
        ["FULL_IMPORT", "EMPTY_IMPORT", "TOTAL_IMPORT",
         "FULL_EXPORT", "EMPTY_EXPORT", "TOTAL_EXPORT"]
    ].sum()

    total_import = data["TOTAL_IMPORT"].sum()
    total_export = data["TOTAL_EXPORT"].sum()

    others_row = pd.DataFrame([{
        "COUNTRY_NAME": "OTHERS",
        "FULL_IMPORT":   others_sum["FULL_IMPORT"],
        "EMPTY_IMPORT":  others_sum["EMPTY_IMPORT"],
        "TOTAL_IMPORT":  others_sum["TOTAL_IMPORT"],
        "FULL_EXPORT":   others_sum["FULL_EXPORT"],
        "EMPTY_EXPORT":  others_sum["EMPTY_EXPORT"],
        "TOTAL_EXPORT":  others_sum["TOTAL_EXPORT"],
        "%IMPORT": (others_sum["TOTAL_IMPORT"] / total_import) * 100 if total_import else 0,
        "%EXPORT": (others_sum["TOTAL_EXPORT"] / total_export) * 100 if total_export else 0,
    }])

    return pd.concat([top13_df, others_row], ignore_index=True)


# ─── RUSSIA PORT-LEVEL ANALYSIS ──────────────────────────────
PORT_MAPPING = {
    "RUFIP": "VLADIVOSTOK",
    "RUVVO": "VLADIVOSTOK (COMMERCIAL PORT)",
    "RULED": "ST. PETERSBURG",
    "RUVFP": "VLADIVOSTOK",
    "RUVLV": "VLADIVOSTOK",
    "RUVST": "VLADIVOSTOK",
}

def analyze_russia(df: pd.DataFrame):
    """
    Filter rows for Russia (COUNTRY == 'RU'), group by PORT,
    and return (import_df, export_df) broken down per port.
    """
    df_ru = df[df["COUNTRY"].str.upper() == "RU"].copy()

    if df_ru.empty:
        return pd.DataFrame(), pd.DataFrame()

    df_ru["COUNTRY_NAME"] = "RUSSIA"
    grouped = df_ru.groupby(["COUNTRY_NAME", "PORT"], as_index=False).sum(numeric_only=True)
    grouped["PORT_NAME"] = grouped["PORT"].map(PORT_MAPPING).fillna(grouped["PORT"])

    total_import = grouped["TOTAL_IMPORT"].sum()
    total_export = grouped["TOTAL_EXPORT"].sum()

    grouped["%IMPORT"] = (grouped["TOTAL_IMPORT"] / total_import * 100) if total_import else 0
    grouped["%EXPORT"] = (grouped["TOTAL_EXPORT"] / total_export * 100) if total_export else 0

    import_ru = grouped[
        ["COUNTRY_NAME", "PORT", "PORT_NAME", "FULL_IMPORT", "EMPTY_IMPORT", "TOTAL_IMPORT", "%IMPORT"]
    ].sort_values("%IMPORT", ascending=False).reset_index(drop=True)

    export_ru = grouped[
        ["COUNTRY_NAME", "PORT", "PORT_NAME", "FULL_EXPORT", "EMPTY_EXPORT", "TOTAL_EXPORT", "%EXPORT"]
    ].sort_values("%EXPORT", ascending=False).reset_index(drop=True)

    return import_ru, export_ru
