#!/usr/bin/env python3
"""Consolidate Cricsheet IPL Ashwin CSV files into match and delivery tables."""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import tempfile
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TextIO


DEFAULT_URL = "https://cricsheet.org/downloads/ipl_csv2.zip"
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
MATCH_COLUMNS = [
    "match_id",
    "season",
    "match_date",
    "venue",
    "city",
    "team1",
    "team2",
    "toss_winner",
    "toss_decision",
    "winner",
    "winner_runs",
    "winner_wickets",
    "outcome",
    "eliminator",
    "method",
    "player_of_match",
    "event_name",
    "match_number",
]
DELIVERY_COLUMNS = [
    "match_id",
    "innings",
    "over_no",
    "ball_no",
    "batting_team",
    "bowling_team",
    "batter",
    "non_striker",
    "bowler",
    "batter_runs",
    "extra_runs",
    "total_runs",
    "wides",
    "noballs",
    "is_legal_ball",
    "is_wicket",
    "dismissal_kind",
    "player_dismissed",
]
MATCH_INFO_PATTERN = re.compile(r"^(\d+)_info\.csv$")
BALL_FILE_PATTERN = re.compile(r"^(\d+)\.csv$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zip-path",
        type=Path,
        help="Use an existing Cricsheet zip instead of downloading it.",
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("CRICSHEET_ZIP_URL") or DEFAULT_URL,
        help="Cricsheet IPL CSV zip URL (defaults to CRICSHEET_ZIP_URL).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DATA_DIR,
        help="Directory for the two consolidated CSV files.",
    )
    return parser.parse_args()


def download_zip(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ipl-weather-pipeline/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        with destination.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)


def read_match_info(archive: zipfile.ZipFile, member: str, match_id: str) -> dict[str, str]:
    values: dict[str, list[str]] = defaultdict(list)
    result_by: dict[str, str] = {}

    with archive.open(member) as raw_file:
        import io

        text_file = io.TextIOWrapper(raw_file, encoding="utf-8-sig", newline="")
        for row in csv.reader(text_file):
            if len(row) < 3 or row[0] != "info":
                continue
            key = row[1].strip()
            if key == "by" and len(row) >= 4:
                result_by[row[2].strip()] = row[3].strip()
            elif key:
                values[key].append(row[2].strip())

    teams = values.get("team", [])
    if len(teams) != 2:
        raise ValueError(f"expected two team rows, found {len(teams)}")

    date_value = first(values, "date")
    if not date_value:
        raise ValueError("missing match date")
    match_date = datetime.strptime(date_value.replace("/", "-"), "%Y-%m-%d").date()

    return {
        "match_id": match_id,
        "season": first(values, "season"),
        "match_date": match_date.isoformat(),
        "venue": first(values, "venue"),
        "city": first(values, "city"),
        "team1": teams[0],
        "team2": teams[1],
        "toss_winner": first(values, "toss_winner"),
        "toss_decision": first(values, "toss_decision"),
        "winner": first(values, "winner"),
        "winner_runs": result_by.get("runs", ""),
        "winner_wickets": result_by.get("wickets", ""),
        "outcome": first(values, "outcome"),
        "eliminator": first(values, "eliminator"),
        "method": first(values, "method"),
        "player_of_match": first(values, "player_of_match"),
        "event_name": first(values, "event"),
        "match_number": first(values, "match_number"),
    }


def first(values: dict[str, list[str]], key: str) -> str:
    entries = values.get(key, [])
    return entries[0] if entries else ""


def write_deliveries(
    archive: zipfile.ZipFile,
    member: str,
    match_id: str,
    writer: csv.DictWriter,
) -> tuple[int, dict[int, dict[str, int | str]]]:
    import io

    rows_written = 0
    innings_scores: dict[int, dict[str, int | str]] = {}
    with archive.open(member) as raw_file:
        text_file = io.TextIOWrapper(raw_file, encoding="utf-8-sig", newline="")
        reader = csv.DictReader(text_file)
        required = {
            "innings",
            "ball",
            "batting_team",
            "bowling_team",
            "striker",
            "non_striker",
            "bowler",
            "runs_off_bat",
            "extras",
            "wides",
            "noballs",
            "wicket_type",
            "player_dismissed",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing delivery columns: {', '.join(sorted(missing))}")

        for row in reader:
            ball_value = (row.get("ball") or "").strip()
            if "." not in ball_value:
                raise ValueError(f"invalid ball value {ball_value!r}")
            over_no, ball_no = ball_value.split(".", 1)
            batter_runs = int_or_zero(row.get("runs_off_bat"))
            extra_runs = int_or_zero(row.get("extras"))
            wides = int_or_zero(row.get("wides"))
            noballs = int_or_zero(row.get("noballs"))
            primary_dismissal_kind = (row.get("wicket_type") or "").strip()
            other_dismissal_kind = (row.get("other_wicket_type") or "").strip()
            dismissal_kind = primary_dismissal_kind or other_dismissal_kind
            has_wicket = any(
                kind and kind.lower() != "retired hurt"
                for kind in [primary_dismissal_kind, other_dismissal_kind]
            )
            player_dismissed = (row.get("player_dismissed") or "").strip()
            if not player_dismissed:
                player_dismissed = (row.get("other_player_dismissed") or "").strip()

            innings_no = int((row.get("innings") or "").strip())
            batting_team = (row.get("batting_team") or "").strip()
            score = innings_scores.setdefault(
                innings_no,
                {"batting_team": batting_team, "runs": 0, "wickets": 0},
            )
            if score["batting_team"] != batting_team:
                raise ValueError(f"multiple batting teams in innings {innings_no}")
            score["runs"] = int(score["runs"]) + batter_runs + extra_runs
            score["wickets"] = int(score["wickets"]) + sum(
                kind != "" and kind.lower() != "retired hurt"
                for kind in [primary_dismissal_kind, other_dismissal_kind]
            )

            writer.writerow(
                {
                    "match_id": match_id,
                    "innings": innings_no,
                    "over_no": over_no,
                    "ball_no": ball_no,
                    "batting_team": batting_team,
                    "bowling_team": (row.get("bowling_team") or "").strip(),
                    "batter": (row.get("striker") or "").strip(),
                    "non_striker": (row.get("non_striker") or "").strip(),
                    "bowler": (row.get("bowler") or "").strip(),
                    "batter_runs": batter_runs,
                    "extra_runs": extra_runs,
                    "total_runs": batter_runs + extra_runs,
                    "wides": wides,
                    "noballs": noballs,
                    "is_legal_ball": str(wides == 0 and noballs == 0).lower(),
                    "is_wicket": str(has_wicket).lower(),
                    "dismissal_kind": dismissal_kind,
                    "player_dismissed": player_dismissed,
                }
            )
            rows_written += 1

    if rows_written == 0:
        raise ValueError("ball-by-ball file contains no deliveries")
    return rows_written, innings_scores


def set_result_margin(
    match: dict[str, str],
    innings_scores: dict[int, dict[str, int | str]],
) -> None:
    if match["eliminator"] or match["outcome"].lower() == "tie":
        return

    winner = match["winner"]
    if not winner or 1 not in innings_scores or 2 not in innings_scores:
        return
    first = innings_scores[1]
    second = innings_scores[2]
    if first["batting_team"] == winner and second["batting_team"] != winner:
        margin = int(first["runs"]) - int(second["runs"])
        if margin > 0:
            match["winner_runs"] = str(margin)
    elif second["batting_team"] == winner and first["batting_team"] != winner:
        wickets_lost = int(second["wickets"])
        match["winner_wickets"] = str(max(0, 10 - wickets_lost))


def int_or_zero(value: str | None) -> int:
    value = (value or "").strip()
    return int(value) if value else 0


def write_csv_header(output: TextIO, columns: list[str]) -> csv.DictWriter:
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    return writer


def consolidate(zip_path: Path, output_dir: Path) -> tuple[int, int, int, set[str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    match_output = output_dir / "ipl_matches.csv"
    delivery_output = output_dir / "ipl_deliveries.csv"
    temp_match = output_dir / ".ipl_matches.csv.tmp"
    temp_delivery = output_dir / ".ipl_deliveries.csv.tmp"
    errors: list[str] = []
    seasons: set[str] = set()
    match_count = 0
    delivery_count = 0

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        info_files = {
            match_id: name
            for name in names
            if (match := MATCH_INFO_PATTERN.fullmatch(Path(name).name))
            for match_id in [match.group(1)]
        }
        ball_files = {
            match_id: name
            for name in names
            if (match := BALL_FILE_PATTERN.fullmatch(Path(name).name))
            for match_id in [match.group(1)]
        }

        missing_info = sorted(set(ball_files) - set(info_files))
        missing_ball = sorted(set(info_files) - set(ball_files))
        if missing_info or missing_ball:
            details = []
            if missing_info:
                details.append(f"ball files without info files: {', '.join(missing_info[:10])}")
            if missing_ball:
                details.append(f"info files without ball files: {', '.join(missing_ball[:10])}")
            raise ValueError("Cricsheet match file count mismatch: " + "; ".join(details))

        with temp_match.open("w", encoding="utf-8", newline="") as matches_file, temp_delivery.open(
            "w", encoding="utf-8", newline=""
        ) as deliveries_file:
            match_writer = write_csv_header(matches_file, MATCH_COLUMNS)
            delivery_writer = write_csv_header(deliveries_file, DELIVERY_COLUMNS)

            for match_id in sorted(info_files, key=int):
                try:
                    match_row = read_match_info(archive, info_files[match_id], match_id)
                    written, innings_scores = write_deliveries(
                        archive,
                        ball_files[match_id],
                        match_id,
                        delivery_writer,
                    )
                    set_result_margin(match_row, innings_scores)
                    match_writer.writerow(match_row)
                    seasons.add(match_row["season"])
                    match_count += 1
                    delivery_count += written
                except (KeyError, TypeError, ValueError, csv.Error) as error:
                    errors.append(f"{match_id}: {error}")

    if errors:
        temp_match.unlink(missing_ok=True)
        temp_delivery.unlink(missing_ok=True)
        raise ValueError("Failed to parse matches:\n" + "\n".join(errors))

    if match_count != len(ball_files):
        temp_match.unlink(missing_ok=True)
        temp_delivery.unlink(missing_ok=True)
        raise ValueError(
            f"Match count mismatch: wrote {match_count} matches for {len(ball_files)} ball files"
        )

    temp_match.replace(match_output)
    temp_delivery.replace(delivery_output)
    return match_count, delivery_count, len(ball_files), seasons


def main() -> int:
    args = parse_args()
    if args.zip_path:
        zip_path = args.zip_path
        if not zip_path.is_file():
            print(f"Zip file not found: {zip_path}", file=sys.stderr)
            return 2
        return report(zip_path, args.output_dir)

    with tempfile.TemporaryDirectory(prefix="cricsheet_ipl_") as temp_dir:
        zip_path = Path(temp_dir) / "ipl_csv2.zip"
        try:
            print(f"Downloading Cricsheet data from {args.url}")
            download_zip(args.url, zip_path)
            return report(zip_path, args.output_dir)
        except (OSError, urllib.error.URLError, zipfile.BadZipFile, ValueError) as error:
            print(f"Cricsheet consolidation failed: {error}", file=sys.stderr)
            return 1


def report(zip_path: Path, output_dir: Path) -> int:
    try:
        match_count, delivery_count, ball_file_count, seasons = consolidate(zip_path, output_dir)
    except (OSError, zipfile.BadZipFile, ValueError) as error:
        print(f"Cricsheet consolidation failed: {error}", file=sys.stderr)
        return 1

    matches_path = output_dir / "ipl_matches.csv"
    deliveries_path = output_dir / "ipl_deliveries.csv"
    print(f"Matches: {match_count}")
    print(f"Ball-by-ball files: {ball_file_count}")
    print(f"Deliveries: {delivery_count}")
    print(f"Seasons: {', '.join(sorted(seasons))}")
    print(f"Matches CSV: {matches_path} ({matches_path.stat().st_size:,} bytes)")
    print(f"Deliveries CSV: {deliveries_path} ({deliveries_path.stat().st_size:,} bytes)")
    if deliveries_path.stat().st_size >= 100 * 1024 * 1024:
        print("Warning: deliveries CSV exceeds GitHub's 100 MB file limit", file=sys.stderr)
    print("Matches that failed to parse: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
