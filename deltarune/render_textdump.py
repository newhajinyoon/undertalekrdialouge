#!/usr/bin/env python3
"""Convert lang.json to the data we want to show on the page."""

import html
import io
import json
import re
import sys
import typing


def render(text: str | None, msgid: str, lang: str) -> str | None:
    if not text:
        return None
    if text in ("/*", "/＊") and "shop" in msgid:
        return ""
    out = io.StringIO()
    color = "W"
    i = 0

    # 디버그: 알 수 없는 이스케이프에서 종료할지 여부 (개발 시 True로 바꿔서 엄격하게 검사 가능)
    DEBUG_EXIT_ON_UNKNOWN = False

    while i < len(text):
        match text[i]:
            case "\\":
                # 경계 체크
                if i + 1 >= len(text):
                    break

                ch = text[i + 1]

                # 기존에 처리하던 케이스들
                if ch == "c":
                    prev_color = color
                    # \cX 형태 처리 (X가 없을 수 있으므로 경계 체크)
                    if i + 2 < len(text):
                        color = text[i + 2]
                        if color == "0":
                            color = "W"
                        if color not in "RBYGOASVIW":
                            # 알 수 없는 색이면 경고를 찍고 기본으로 복원
                            print(f"Warning: Invalid color '{color}' in {lang}:{msgid} -> {text}", file=sys.stderr)
                            color = "W"
                        # 스팬 열기/닫기
                        if color != prev_color:
                            if prev_color != "W":
                                out.write("</span>")
                            if color != "W":
                                out.write(f'<span class="{color}">')
                        i += 3
                        continue
                    else:
                        # \c 뒤에 문자가 부족하면 그냥 무시
                        print(f"Warning: Truncated color escape in {lang}:{msgid} -> {text}", file=sys.stderr)
                        i += 2
                        continue

                if ch in ("O", "I"):
                    out.write('<span class="picture">[IMG]</span>')
                    # 원래 의도대로 공백 건너뛰기 시도
                    i += 2
                    while i < len(text) and text[i] in (" ", "\u3000"):
                        i += 1
                    continue

                if ch in ("M", "E", "T", "F", "S", "s", "a", "f", "C", "U", "m"):
                    # 메시지 수식자들: 현재는 무시(원래 코드처럼)
                    i += 2
                    continue

                # \\ -> \
                if ch == "\\":
                    out.write("\\")
                    i += 2
                    continue

                # \ + space -> space
                if ch == " ":
                    out.write(" ")
                    i += 2
                    continue

                # 만약 다음 문자가 비 ASCII(예: 한글)라면 백슬래시는 아마 잘못 들어간 경우.
                # 안전하게 백슬래시를 무시하고 문자를 그대로 출력.
                if ord(ch) >= 0x80:
                    print(f"Warning: Strange escape '\\{ch}' (non-ascii) in {lang}:{msgid} -> {text}", file=sys.stderr)
                    out.write(ch)
                    i += 2
                    continue

                # 알려진 다른 특수 처리(필요하면 여기에 추가)
                # ...

                # 알 수 없는 이스케이프 코드 처리: 종료 대신 경고를 찍고 가능한 한 안전하게 처리
                msg = f"Unhandled escape '\\{ch}' in {lang}:{msgid} -> {text}"
                print("\n--- WARNING:", msg, file=sys.stderr)
                if DEBUG_EXIT_ON_UNKNOWN:
                    print("Exiting due to DEBUG_EXIT_ON_UNKNOWN=True", file=sys.stderr)
                    sys.exit(1)
                # 기본: 백슬래시를 무시하고 다음 문자를 그대로 출력
                out.write(ch)
                i += 2
                continue

            case "/" if msgid == "obj_dw_churchb_rotatingtower_slash_Create_0_gml_90_0":
                break

            case "/" if not msgid.startswith(
                (
                    "obj_controller_city_mice2_slash_Draw_0_gml_28_0",
                    "obj_fusionmenu_slash_Draw_0_gml_181_0",
                    "obj_overworldc_slash_Draw_0_gml_37_0",
                    "obj_overworldc_slash_Draw_0_gml_69_0",
                    "scr_armorinfo_slash_scr_armorinfo_gml_433_0_b",
                    "scr_armorinfo_slash_scr_armorinfo_gml_553_0",
                    "scr_armorinfo_slash_scr_armorinfo_gml_791_0",
                    "scr_armorinfo_slash_scr_armorinfo_gml_791_0",
                    "scr_spellinfo_slash_scr_spellinfo_gml_109_0",
                    "obj_overworldc_slash_Draw_0_gml_68_0",
                    "obj_credits_2_slash_Step_0_gml_177_0",
                    "obj_npc_room_slash_Other_10_gml_982_0",
                    "obj_b1power_slash_Step_0_gml_154_0",
                    "scr_armorinfo_slash_scr_armorinfo_gml_539_0",
                    "scr_credit_slash_scr_credit_gml_64_0_b",
                    "scr_credit_slash_scr_credit_gml_78_0",
                    "scr_credit_slash_scr_credit_gml_95_0",
                    "scr_text_slash_scr_text_gml_11097_0",
                )
            ):
                rest = text[i + 1 :]
                # 허용되는 꼴만 통과시키되, 그렇지 않으면 경고만 찍고 루프 종료
                if re.match(r'^[%/~1\s]*$', rest):
                    break
                else:
                    print(f"Warning: Unexpected trailing after '/' in {lang}:{msgid} -> {text!r}", file=sys.stderr)
                    # 원래는 assert로 죽였는데, 이제는 가능한 안전하게 남은 문자열을 무시하고 종료
                    break

            case "&" if (
                msgid.startswith(
                    (
                        "scr_credit",
                        "obj_credits",
                        "scr_monstersetup",
                        "scr_monstersetup_slash_scr_monstersetup_gml_1612_0",
                        "scr_monstersetup_slash_scr_monstersetup_gml_1614_0",
                        "obj_mike_minigame_tv",
                        "obj_fusionmenu",
                        "obj_b1rocks1",
                        "scr_quiztext",
                        "obj_b3bs_lancerget_lancer",
                        "obj_shop2_slash_Create",
                    )
                )
                and msgid
                not in [
                    "scr_monstersetup_slash_scr_monstersetup_gml_27_0",
                    "obj_fusionmenu_slash_Draw_0_gml_182_0",
                ]
                and not msgid.startswith(("obj_credits_ch4",))
            ):
                out.write("&amp;")

            case "#" if msgid.startswith(
                (
                    "obj_readable_room1",
                    "obj_npc_room_animated_slash_Other_10_gml_41_0",
                    "obj_npc_room_animated_slash_Other_10_gml_57_0",
                )
            ):
                out.write("#")

            case "#" if msgid.startswith("obj_bloxer_enemy_slash_Step_0_gml_135_1"):
                out.write(" ")

            case "&" | "#":
                out.write("\n")

            case "\t":
                out.write(" ")

            case "^":
                if i + 1 < len(text) and text[i + 1].isdigit():
                    i += 1

            case "%" if (
                msgid.startswith(
                    (
                        "scr_weaponinfo",
                        "scr_armorinfo",
                        "scr_iteminfo",
                        "scr_itemdesc",
                        "scr_monstersetup",
                    )
                )
                and not msgid.startswith(("scr_itemdesc_oldtype",))
                or msgid
                in [
                    "scr_text_slash_scr_text_gml_1886_0",
                    "scr_text_slash_scr_text_gml_8925_0",
                    "scr_text_slash_scr_text_gml_8926_0",
                    "obj_battlecontroller_slash_Draw_0_gml_171_0",
                    "obj_battlecontroller_slash_Draw_0_gml_280_0",
                    "obj_fusionmenu_slash_Step_0_gml_144_0",
                    "obj_shop_ch2_spamton_slash_Create_0_gml_89_0",
                    "obj_npc_room_slash_Other_10_gml_982_0",
                ]
            ):
                out.write("%")

            case "%":
                rest = text[i + 1 :]
                # 허용되는 꼴인지 확인. 아니면 경고만 찍고 '%'를 출력하고 계속 진행
                if rest in ("", "%", "%%", "/%"):
                    break
                else:
                    print(f"Warning: Unexpected text after '%' in {lang}:{msgid} -> {text!r}", file=sys.stderr)
                    out.write("%")
                    i += 1
                    continue

            case ">":
                out.write("&gt;")

            case "<":
                out.write("&lt;")

            case "`":
                if i + 1 < len(text):
                    out.write(text[i + 1] if text[i + 1] != "&" else "&amp;")
                    i += 1

            case "~" if i + 1 < len(text) and text[i + 1].isdigit():
                assert text[i + 1] in "12345"
                out.write(f'<span class="param">~{text[i + 1]}</span>')
                i += 1

            case "N" if msgid == "obj_dw_church_intro_guei_slash_Step_0_gml_169_0":
                out.write("Ñ")

            case char:
                out.write(char)
        i += 1

    if color != "W":
        out.write("</span>")
    rendered = out.getvalue()
    if (
        lang == "en"
        and rendered.startswith("* ")
        and "\n" in rendered
        and r"\C" not in text
    ):
        rendered = re.sub(r"\n *([^*])", "\n  \\1", rendered)
    if lang == "en" and rendered.startswith("* "):
        rendered = (
            '<div class="indented">'
            + rendered.replace("\n", '</div><div class="indented">')
            + "</div>"
        )
    return rendered



RE_STRETCH = re.compile(r"(\[[^\]]*\])")


def your_____long(text: str, id: str) -> str:
    text = text.replace("-", "")
    pieces = []
    for piece in RE_STRETCH.split(text):
        if not piece.startswith("["):
            pieces.append(f'<span style="display: inline-block;">{piece}</span>')
            continue
        assert piece[-1] == "]"
        assert piece[2] == ":"
        width = int(piece[1])
        text = piece[3:-1].replace(" ", "\N{NO-BREAK SPACE}")
        pieces.append(
            f'<span style="transform: scaleX(calc({width}/{len(text)})); '
            + f"width: {width * 8}px; "
            + "overflow-wrap: normal; "
            + 'transform-origin: top left; display: inline-block;">'
            + text
            + "</span>"
        )

    out = "".join(pieces)
    if id.endswith("_1"):
        out = f'<span class="B">{out}</span>'
    return out


postfixes = [
    "gml",
    "Draw",
    "Step",
    "Create",
    "Other",
    "Alarm",
    "Destroy",
    "Collision",
    "slash",
]


def groupify(ident: str) -> str:
    ident = ident.replace("_DUP", "")

    if ident.endswith(("_b", "_c")):
        ident = ident[:-2]

    for name in [
        "obj_sneo_kristhrown_slash_Collision",
        "obj_ralseithrown_slash_Collision",
        "obj_werewire_kristhrown_slash_Collision",
        "obj_caradventure_object_slash_Collision",
        "obj_queen_kristhrown_slash_Collision",
        "obj_queen_ralseithrown_slash_Collision",
    ]:
        # Postfixed with UUIDs for some reason
        if ident.startswith(name):
            ident = name

    while True:
        # rsplit이 _가 없는 경우 에러를 일으킬 수 있으므로 확인
        if "_" not in ident:
            break
        rest, end = ident.rsplit("_", 1)
        if end == "" or end.isdigit() or end in postfixes:
            ident = rest
        else:
            break

    if "_slash_" in ident and len(set(ident.split("_slash_"))) == 1:
        ident = ident.split("_slash_")[0]

    return ident


EVENTS = [
    "PreCreate",
    "Create",
    "Draw",
    "Step",
    "KeyPress",
    "Mouse",
    "Other",
    "Alarm",
    "Destroy",
    "CleanUp",
]

# sourcemap을 전역 변수로 접근하기 위해 선언
sourcemap: dict[str, dict[str, str]] = {}
# n을 전역 변수로 접근하기 위해 선언
n: str = ""

def smartsort(key: str):
    global n, sourcemap # 전역 변수 사용 선언
    
    pieces = key.split("_")
    for i, piece in enumerate(pieces):
        if piece.isdigit():
            # Natsort of integers (particularly line numbers)
            pieces[i] = piece.rjust(16, "0")
        if piece in EVENTS:
            # Try to order GameMaker events, e.g. Create text is usually
            # shown earlier than Alarm text
            pieces[i] = str(EVENTS.index(piece)).rjust(3, "0")

    # Further sort by the actual line order in the files
    if "gml" in pieces:
        assert pieces.count("gml") == 1
        # (using `n` here is mildly criminal)
        # n이 설정되었고, sourcemap[n]에 key가 있는지 확인
        if n and n in sourcemap and key in sourcemap[n]:
            filename, lineno = sourcemap[n][key].split(":")
            lineno = int(lineno)
        else:
            filename = "zzzzzz"
            lineno = 9999999
        pieces.insert(pieces.index("gml") + 1, str(lineno).rjust(10, "0"))
        # Some translation keys that indicate the same file belong to different files
        # e.g. DEVICE_MENU_slash_Create_0_gml_107_0 and DEVICE_MENU_slash_Create_0_gml_17_0
        # are on similar lines in different files and we don't want them together
        pieces.insert(pieces.index("gml") + 1, filename)

    return pieces


# --- [!수정된 부분!] ---
# Literal 타입에 'ko' 추가
lang_str_type = typing.Literal["en", "ja", "ko"]

lang: dict[str, dict[lang_str_type, dict[str, str]]] = json.load(
    open("lang.json", encoding="utf-8")
)

# Load Korean data and merge it
ko_chapters = ["1", "2", "3", "4"]
for chap in ko_chapters:
    ko_filename = f"{chap}.json"
    try:
        with open(ko_filename, encoding="utf-8") as f:
            ko_data = json.load(f)
        
        if chap not in lang:
            # If chapter isn't in lang.json, create a stub for it
            print(f"Note: Chapter {chap} not found in lang.json, creating new entry for Korean.", file=sys.stderr)
            lang[chap] = {"en": {}, "ja": {}}
        
        # Add the loaded Korean data under the 'ko' key
        lang[chap]["ko"] = ko_data
    
    except FileNotFoundError:
        print(f"Warning: {ko_filename} not found, skipping Korean data for chapter {chap}.", file=sys.stderr)
        if chap in lang and "ko" not in lang[chap]:
            lang[chap]["ko"] = {} # Add empty dict to prevent errors later
    except json.JSONDecodeError as e:
        print(f"Warning: Error decoding {ko_filename} (Error: {e}), skipping Korean data for chapter {chap}.", file=sys.stderr)
        if chap in lang and "ko" not in lang[chap]:
            lang[chap]["ko"] = {} # Add empty dict
# --- [!수정된 부분 끝!] ---


sourcemap = json.load(
    open("sourcemap.json", encoding="utf-8")
)
rendered: dict[
    str, dict[str, dict[str, dict[lang_str_type, str | None]]]
] = {}

# 'n'을 루프 밖에서 전역 변수로 설정
for n_loop in lang:
    n = n_loop # smartsort에서 사용할 전역 변 n 설정
    rendered[n] = {}
    
    # Ensure 'ko' key exists, even if empty, to prevent KeyErrors
    if "ko" not in lang[n]:
        lang[n]["ko"] = {}
        
    ks = sorted(lang[n]["en"].keys() | lang[n]["ja"].keys() | lang[n]["ko"].keys(), key=smartsort)
    for k in ks:
        if k == "date":
            continue
        en = lang[n]["en"].get(k)
        ja = lang[n]["ja"].get(k)
        ko = lang[n]["ko"].get(k)
        group = groupify(k)
        if (en and en.strip(" \\C234")) or (ja and ja.strip(" \\C234")) or (ko and ko.strip(" \\C234")):
            ren = render(en, k, "en")
            rja = render(ja, k, "ja")
            rko = render(ko, k, "ko")
            if k.startswith("scr_rhythmgame_notechart_"):
                # TODO: stretch Japanese text (different syntax, can't assume font width...)
                if ren: # ren이 None이 아닐 때만 실행
                    ren = your_____long(ren, k)
            if (ren and ren.strip()) or (rja and rja.strip()) or (rko and rko.strip()):
                rendered[n].setdefault(group, {})
                rendered[n][group][k] = {"en": ren, "ja": rja, "ko": rko}

# Mainly for reference in the git diff.
# Easier for other programs to ingest than the JS file below.
with open("rendered.json", "w", encoding="utf-8") as f:
    json.dump(rendered, f, indent=0, ensure_ascii=False)

# https://v8.dev/blog/cost-of-javascript-2019#json
# TL;DR: JSON parsed from a string literal is faster than an object literal.
# This saves ~60ms in the node.js CLI on my laptop.
with open("rendered.json.js", "w", encoding="utf-8") as f:
    as_json = json.dumps(
        rendered, indent=None, ensure_ascii=False, separators=(",", ":")
    )
    f.write("var rendered = JSON.parse('")
    f.write(as_json.replace("\\", "\\\\").replace("'", "\\'"))
    f.write("');")


def plainify_html(text: str) -> str:
    text = text.replace('</div><div class="indented">', "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return text


# This renders poorly on mobile devices...
# It's OK if this and the chapter headers look like shit but
# let's not do box characters beyond that.
HEADER = """
 ▄██████████████████████████████████████████████████████▄
██▀                                                  ▀██
██   █   █ █  ▄                                ███ █ █ ███  ██
██  ███ ███ █ ███ █♥︎█ █▀█ █ ██ ████ ███     █   █   █   ██
██  ███ █▄▄ █  █  █▀█ █   ████ ██ █ █▄▄  ▄  █  █ █  █   ██
██                                                     ██
██         unofficial deltarune text dump              ██
██                                                     ██
▀██▄  https://hushbugger.github.io/deltarune/text/   ▄██▀
  ▀██▄                                           ▄██▀
    ▀██████████████████████████████████████████████▀


"""

CHAPTER = """

▀▀██▄▄▄▄ ● ▄▄▄▄██▀▀
    ▲ CHAPTER % ▲
          ▼

"""


def render_plain(lang: lang_str_type) -> str:
    # duplicated logic from index.html
    out = io.StringIO()
    out.write(HEADER)
    dedup = {}
    # rendered가 비어있지 않은지 확인
    if not rendered:
        print("Warning: 'rendered' dictionary is empty. No text to output.", file=sys.stderr)
        return ""
        
    for chap, groups in rendered.items():
        out.write(CHAPTER.replace("%", chap))
        for title, group in groups.items():
            pending_title = title.replace("_slash_", "/")
            for key, contents in group.items():
                content = contents.get(lang) # .get()으로 안전하게 접근
                if not content:
                    continue
                if dedup.get(key) == content:
                    continue
                dedup[key] = content
                if pending_title:
                    out.write("\n")
                    out.write("=" * len(pending_title))
                    out.write("\n")
                    out.write(pending_title)
                    out.write("\n")
                    out.write("=" * len(pending_title))
                    out.write("\n\n")
                    pending_title = None
                out.write(plainify_html(content))
                out.write("\n\n")

    return out.getvalue().strip("\n") + "\n"


with open("DELTARUNE.txt", "w", encoding="utf-8") as f:
    # CRLF for max compatibility (maybe somebody's using notepad.exe on Windows 7).
    # BOM since it seems the most portable/reliable way to indicate encoding.
    f.write("\N{BYTE ORDER MARK}" + render_plain("en").replace("\n", "\r\n"))

with open("DELTARUNE_ja.txt", "w", encoding="utf-8") as f:
    f.write("\N{BYTE ORDER MARK}" + render_plain("ja").replace("\n", "\r\n"))

with open("DELTARUNE_ko.txt", "w", encoding="utf-8") as f:
    f.write("\N{BYTE ORDER MARK}" + render_plain("ko").replace("\n", "\r\n"))

print("Text dump successfully generated.")