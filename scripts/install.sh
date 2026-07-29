#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd -- "${script_dir}/.." && pwd)"
source_dir="${project_root}/pet"
codex_root="${CODEX_HOME:-${HOME}/.codex}"
target_dir="${codex_root}/pets/pingo"

for required_file in pet.json spritesheet.webp; do
  if [[ ! -f "${source_dir}/${required_file}" ]]; then
    echo "Missing required package file: ${source_dir}/${required_file}" >&2
    exit 1
  fi
done

mkdir -p "${target_dir}"
install -m 0644 "${source_dir}/pet.json" "${target_dir}/pet.json"
install -m 0644 "${source_dir}/spritesheet.webp" "${target_dir}/spritesheet.webp"

echo "Installed Pingo to ${target_dir}"
