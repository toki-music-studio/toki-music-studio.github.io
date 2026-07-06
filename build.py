#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOKI-刻 公式サイト ビルドスクリプト

songs.json（曲データ）を template.html（デザインの原本）に流し込んで、
公開用の index.html を作ります。

使い方:
    python3 build.py
"""

import html as html_module
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SONGS_FILE = os.path.join(BASE, "songs.json")
TEMPLATE_FILE = os.path.join(BASE, "template.html")
OUTPUT_FILE = os.path.join(BASE, "index.html")
PLACEHOLDER = "<!-- SONG_CARDS -->"

# 曲カードの上に入れる説明コメント（元のindex.htmlにあったものを維持）
CARDS_NOTE = (
    "    <!-- ジャケ画像を使う場合:各カードの <img> の src を images/○○.jpg "
    "に置き換えるだけで表示されます。\n"
    "         画像が見つからない間は「TOKI」のプレースホルダーが表示されます。 -->"
)


def stop(message):
    """日本語のエラーメッセージを表示して終了する"""
    print("×" + " ビルドを中止しました")
    print(message)
    sys.exit(1)


def load_songs():
    if not os.path.exists(SONGS_FILE):
        stop("songs.json が見つかりません。build.py と同じフォルダに置いてください。")
    with open(SONGS_FILE, encoding="utf-8") as f:
        text = f.read()
    try:
        songs = json.loads(text)
    except json.JSONDecodeError as e:
        lines = text.splitlines()
        near = lines[e.lineno - 1].strip() if 0 < e.lineno <= len(lines) else ""
        stop(
            "songs.json の書き方にミスがあるようです。\n"
            f"  怪しい場所: {e.lineno}行目あたり\n"
            f"  その行の内容: {near}\n"
            "  よくある原因: カンマの付け忘れ・付けすぎ、\" \"（引用符）の閉じ忘れ、"
            "{ } や [ ] の対応ミス"
        )
    if not isinstance(songs, list):
        stop("songs.json は [ ] で囲んだ曲のリストにしてください。")
    return songs


def check_song(i, song):
    """1曲分のデータをチェックする。問題があれば日本語で伝えて止まる。"""
    label = f"{i + 1}曲目"
    if not isinstance(song, dict):
        stop(f"{label} が曲データ（{{ }}で囲んだ形）になっていません。")
    if isinstance(song.get("title"), str) and song["title"].strip():
        label = f"{i + 1}曲目「{song['title']}」"
    else:
        stop(f'{label} に "title"（曲名）がありません。')
    for key in ("subtitle", "link", "image"):
        if key not in song:
            stop(f'{label} に "{key}" がありません。空でもよいので "{key}": "" と書いてください。')
        if not isinstance(song[key], str):
            stop(f'{label} の "{key}" は " " で囲んだ文字にしてください。')
    if "latest" in song and not isinstance(song["latest"], bool):
        stop(f'{label} の "latest" は true か false にしてください（" "で囲まない）。')


def render_card(song):
    title = html_module.escape(song["title"], quote=False)
    title_attr = html_module.escape(song["title"], quote=True)
    subtitle = html_module.escape(song["subtitle"], quote=False)
    link = song["link"].strip()
    image = html_module.escape(song["image"], quote=True)

    if link:
        open_tag = (
            f'    <a class="work" href="{html_module.escape(link, quote=True)}"'
            ' target="_blank" rel="noopener">'
        )
    else:
        open_tag = '    <a class="work" href="#">'

    badge = '\n        <span class="badge">LATEST</span>' if song.get("latest") else ""

    return f"""{open_tag}
      <div class="jacket">
        <div class="ph"><div class="mark">TOKI</div><div class="t">{title}</div></div>
        <img src="{image}" alt="{title_attr} ジャケット" onerror="this.remove()">
      </div>
      <div class="work-info">
        <div class="work-title">{title}</div>
        <div class="work-sub">{subtitle}</div>{badge}
      </div>
    </a>"""


def main():
    songs = load_songs()
    if not songs:
        stop("songs.json に曲が1曲もありません。")
    for i, song in enumerate(songs):
        check_song(i, song)

    latest_titles = [s["title"] for s in songs if s.get("latest")]
    if len(latest_titles) > 1:
        stop(
            '"latest": true の曲が複数あります: ' + "、".join(latest_titles) + "\n"
            "  LATESTバッジを付ける曲は1曲だけにして、他は false にしてください。"
        )

    if not os.path.exists(TEMPLATE_FILE):
        stop("template.html が見つかりません。デザインの原本なので、削除しないでください。")
    with open(TEMPLATE_FILE, encoding="utf-8") as f:
        template = f.read()
    if PLACEHOLDER not in template:
        stop(
            f"template.html の中に {PLACEHOLDER} という目印が見つかりません。\n"
            "  template.html を編集した際に消えてしまった可能性があります。"
        )

    cards = "\n\n".join(render_card(s) for s in songs)
    output = template.replace(PLACEHOLDER, CARDS_NOTE + "\n\n" + cards)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"○ index.html を作りました（{len(songs)}曲分の曲カードを生成）")
    if latest_titles:
        print(f"○ LATESTバッジ: {latest_titles[0]}")
    else:
        print("△ LATESTバッジの曲がありません（どれかに \"latest\": true を付けると表示されます）")

    for song in songs:
        image_path = os.path.join(BASE, song["image"])
        if not os.path.exists(image_path):
            print(
                f"△ 「{song['title']}」のジャケット画像（{song['image']}）がまだありません。"
                "画像が届くまでは「TOKI」のプレースホルダーが表示されます。"
            )


if __name__ == "__main__":
    main()
