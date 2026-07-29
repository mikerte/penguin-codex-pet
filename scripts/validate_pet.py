#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PET_DIRECTORY = PROJECT_ROOT / "pet"
MANIFEST_PATH = PET_DIRECTORY / "pet.json"
CHECKSUM_PATH = PROJECT_ROOT / "checksums.sha256"

EXPECTED_MANIFEST = {
    "id": "pingo",
    "displayName": "Pingo",
    "spriteVersionNumber": 2,
    "spritesheetPath": "spritesheet.webp",
}
EXPECTED_SIZE = (1536, 2288)
CELL_SIZE = (192, 208)
EXPECTED_USED_COLUMNS = {
    0: set(range(7)),
    1: set(range(8)),
    2: set(range(8)),
    3: set(range(4)),
    4: set(range(5)),
    5: set(range(8)),
    6: set(range(6)),
    7: set(range(6)),
    8: set(range(6)),
    9: set(range(8)),
    10: set(range(8)),
}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load_manifest() -> dict[str, object]:
    if not MANIFEST_PATH.is_file():
        fail(f"missing manifest: {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"could not read pet.json: {error}")

    for key, expected in EXPECTED_MANIFEST.items():
        if payload.get(key) != expected:
            fail(f"pet.json {key!r} must be {expected!r}, got {payload.get(key)!r}")

    description = payload.get("description")
    if not isinstance(description, str) or not description.strip():
        fail("pet.json description must be a non-empty string")
    return payload


def expected_checksum() -> str:
    if not CHECKSUM_PATH.is_file():
        fail("missing checksums.sha256")
    entries = [
        line.split()
        for line in CHECKSUM_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    for digest, relative_path in entries:
        if relative_path.replace("\\", "/") == "pet/spritesheet.webp":
            return digest.lower()
    fail("checksums.sha256 has no pet/spritesheet.webp entry")


def validate_atlas(atlas_path: Path) -> str:
    if not atlas_path.is_file():
        fail(f"missing spritesheet: {atlas_path.relative_to(PROJECT_ROOT)}")

    digest = hashlib.sha256(atlas_path.read_bytes()).hexdigest()
    if digest != expected_checksum():
        fail(f"spritesheet checksum mismatch: expected {expected_checksum()}, got {digest}")

    try:
        with Image.open(atlas_path) as opened:
            if opened.format != "WEBP":
                fail(f"spritesheet format must be WEBP, got {opened.format}")
            if opened.mode != "RGBA":
                fail(f"spritesheet mode must be RGBA, got {opened.mode}")
            rgba = opened.convert("RGBA")
    except OSError as error:
        fail(f"could not open spritesheet: {error}")

    if rgba.size != EXPECTED_SIZE:
        fail(f"spritesheet must be {EXPECTED_SIZE}, got {rgba.size}")
    cell_width, cell_height = CELL_SIZE
    for row in range(11):
        for column in range(8):
            box = (
                column * cell_width,
                row * cell_height,
                (column + 1) * cell_width,
                (row + 1) * cell_height,
            )
            alpha_bbox = rgba.crop(box).getchannel("A").getbbox()
            should_be_used = column in EXPECTED_USED_COLUMNS[row]
            if should_be_used and alpha_bbox is None:
                fail(f"required cell r{row}c{column} is empty")
            if not should_be_used and alpha_bbox is not None:
                fail(f"unused cell r{row}c{column} is not transparent")

    transparent_rgb_residue = sum(
        1
        for red, green, blue, alpha in rgba.get_flattened_data()
        if alpha == 0 and (red != 0 or green != 0 or blue != 0)
    )
    if transparent_rgb_residue:
        fail(
            "spritesheet contains "
            f"{transparent_rgb_residue} RGB pixels hidden under full transparency"
        )

    visible_chroma_pixels = sum(
        1
        for red, green, blue, alpha in rgba.get_flattened_data()
        if alpha > 0 and red < 16 and green > 239 and blue < 16
    )
    if visible_chroma_pixels:
        fail(f"spritesheet contains {visible_chroma_pixels} visible chroma-key pixels")
    return digest


def main() -> None:
    manifest = load_manifest()
    spritesheet_path = PET_DIRECTORY / str(manifest["spritesheetPath"])
    digest = validate_atlas(spritesheet_path)
    print("PASS: Pingo is a valid Codex v2 pet package")
    print(f"atlas={spritesheet_path.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"dimensions={EXPECTED_SIZE[0]}x{EXPECTED_SIZE[1]}")
    print(f"sha256={digest}")


if __name__ == "__main__":
    main()
