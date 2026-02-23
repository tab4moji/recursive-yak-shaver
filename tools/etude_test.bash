#!/usr/bin/env -S bash -ic 'source "$0"'

# コードフレームワーク(セットアップ)
set -euo pipefail
set +m
shopt -s lastpipe # mapfile による配列化

# コードフレームワーク(first input)
input="./"
input_filename="*.py"

# スクリプトコード: cheat ファイル一覧
find "${input}" -type f -name "${input_filename}" | mapfile -t script_output

# コードフレームワーク(output -> input) + コードフレームワーク(ループ):BEGIN
inputs=("${script_output[@]}")
for input in "${inputs[@]}"; do

# スクリプトコード: cheat ファイルサイズ
du -b "${input}" | sed 's/\t/ /'

# コードフレームワーク(output -> input) + コードフレームワーク(ループ):END
done | read -r -d '' script_output || true

# コードフレームワーク(output -> input)
input="${script_output}"

# スクリプトコード: cheat 最大ファイル
echo "${input}" | sort -nr | head -1 | cut -d' ' -f2 | read -r script_output

# コードフレームワーク(output -> input)
input="${script_output}"

# スクリプトコード: cheat コマンド実行 (pylint)
pylint "${input}" | read -r -d '' script_output || true

# コードフレームワーク(結果出力)
echo "${script_output}"
