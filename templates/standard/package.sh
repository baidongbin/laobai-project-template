#!/bin/sh
set -eu

cd -- "$(dirname -- "$0")"
project=$(basename "$PWD")
head=$(git rev-parse --verify 'HEAD^{commit}')
revision=$(git rev-parse --short "$head")
output="./$project-$revision.zip"

[ ! -d "$output" ] || { echo "输出路径是目录：$output" >&2; exit 1; }
temporary=$(mktemp ./.package.XXXXXX)
trap 'rm -f -- "$temporary"' EXIT HUP INT TERM
git archive --format=zip --prefix="$project/" "$head" > "$temporary"
mv -f -- "$temporary" "$output"

for old in ./"$project"-*.zip; do
    if [ "$old" != "$output" ] && [ -f "$old" ] && [ ! -L "$old" ]; then
        rm -- "$old"
    fi
done
echo "已打包：${output}（仅包含已提交内容）"
