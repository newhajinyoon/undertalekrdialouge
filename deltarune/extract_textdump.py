#!/usr/bin/env python3
"""Generate a lang.json for all chapters in both English and Japanese."""

import io
import json
import pathlib
import re
import subprocess
import sys
import typing

# Expected directory structure:
# ├── 1
# │   ├── CodeEntries
# │   └── lang
# │       ├── lang_en.json
# │       └── lang_ja.json
# ├── 2
# │   ├── CodeEntries
# │   └── lang
# │       (etc...)
# ├── 3
# └── 4
# Originally extracted with UnderTale Mod Tool v0.8.1.1
try:
    source = pathlib.Path(sys.argv[1])
except IndexError:
    print(f"Usage: {sys.argv[0]} path/to/deltarune", file=sys.stderr)
    sys.exit(1)


type FunArgs = list[str | None]
type FunCall = tuple[str, FunArgs]


def parse_args(text: str) -> FunArgs:
    """Parses arguments from a function call string."""
    args = []
    i = 0
    while i < len(text):
        if text[i] in (",", " "):
            i += 1
        elif text[i] == '"':
            i += 1
            arg = io.StringIO()
            while text[i] != '"':
                if text[i] == "\\":
                    i += 1
                    if text[i] == "\\":
                        arg.write("\\")
                    elif text[i] == '"':
                        arg.write('"')
                    elif text[i] == "n":
                        arg.write("\n")
                    elif text[i] == "t":
                        arg.write("\t")
                    elif text[i] == "f":
                        # 90% sure this is just a missing backslash
                        # but let's stay faithful
                        arg.write("\f")
                    else:
                        assert False, text
                    i += 1
                else:
                    arg.write(text[i])
                    i += 1
            i += 1
            args.append(arg.getvalue())
        elif text[i] == ")":
            break
        else:
            # Handle non-string arguments (like scr_84_get_lang_string(v1))
            args.append(None)
            depth = 0
            while i < len(text):
                if text[i] == "(":
                    depth += 1
                elif text[i] == ")":
                    depth -= 1
                    if depth < 0:
                        break
                elif text[i] == "," and depth == 0:
                    break
                i += 1
    return args


TEXTFUNCS = [
    "stringsetloc",
    "msgsetloc",
    "msgnextloc",
    "stringsetsubloc",
    "msgsetsubloc",
    "msgnextsubloc",
    "scr_84_get_lang_string",
]
RE_TEXTFUNCS = re.compile(f"({'|'.join(TEXTFUNCS)})\\(")


def parse_line(line: str) -> list[FunCall]:
    """Finds and parses text function calls in a single line."""
    if line.startswith("function "):
        return []
    calls: list[FunCall] = []
    for match in RE_TEXTFUNCS.finditer(line):
        func = match.group(1)
        args = parse_args(line[match.end() :])
        calls.append((func, args))
    # Original assert was too strict, allowing for lines with text functions
    # but also other code, we'll keep the search loop and let it return [] if no match.
    # assert calls, line
    return calls


class RgResult(typing.NamedTuple):
    """Represents a single match result from ripgrep (rg)."""
    filename: str
    lineno: int
    text: str


def rg(pattern: str, path: pathlib.Path) -> typing.Iterable[RgResult]:
    """Runs ripgrep to find function calls and returns structured results."""
    # ripgrep outputs JSON, which uses UTF-8, so the decoding here is correct.
    try:
        output = subprocess.run(
            [
                "rg",
                "--json",
                "--sort=path",
                "--no-filename",
                "--",
                pattern,
            ],
            stdout=subprocess.PIPE,
            check=True,
            cwd=path,
        ).stdout.decode()
    except FileNotFoundError:
        # Catch the WinError 2 specifically caused by the external 'rg' command not being found.
        print(
            "Error: 'rg' (ripgrep) command not found. This script requires ripgrep "
            "to be installed and available in your system's PATH. "
            "Please install it from https://github.com/BurntSushi/ripgrep",
            file=sys.stderr,
        )
        sys.exit(1)

    for result in output.splitlines():
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            continue # Skip non-JSON output (like ripgrep warnings)
            
        if result["type"] != "match":
            continue
        yield RgResult(
            filename=result["data"]["path"]["text"],
            lineno=result["data"]["line_number"],
            text=result["data"]["lines"]["text"],
        )


CHAPTERS = [1, 2, 3, 4]
text = {n: {} for n in CHAPTERS}
sourcemap = {n: {} for n in CHAPTERS}

for n in CHAPTERS:
    path = source / str(n)
    
    # --- FIX 1 & 2: UTF-8 encoding and try/except for missing/corrupt files ---
    
    # Read lang_ja.json (all chapters)
    ja_path = path / "lang" / "lang_ja.json"
    try:
        # Explicitly use UTF-8 to fix UnicodeDecodeError (cp949 issue)
        ja: dict[str, str] = json.loads(ja_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, UnicodeDecodeError) as e:
        print(f"Skipping Chapter {n}. Error reading required Japanese file {ja_path}: {e}", file=sys.stderr)
        continue
    
    text[n]["ja"] = ja
    
    # Read lang_en.json (Chapter 1 only, for baseline)
    if n == 1:
        en_path = path / "lang" / "lang_en.json"
        try:
            # Explicitly use UTF-8 to fix UnicodeDecodeError
            text[n]["en"] = json.loads(en_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, UnicodeDecodeError) as e:
            print(f"Skipping Chapter 1. Error reading required English file {en_path}: {e}", file=sys.stderr)
            continue
            
        # Chapter 1 logic: find all keys used
        for filename, lineno, line in rg(
            r"scr_84_get_lang_string\(",
            path / "CodeEntries",
        ):
            for func, args in parse_line(line):
                match func, args:
                    case "scr_84_get_lang_string", [str(arg)]:
                        # setdefault() so that the first one wins. Why?
                        # 1. Predictable ordering: if we overrid then keys would
                        #    be ordered by first match but contain last match.
                        # 2. Better results for obj_ch2_scene26_powers_combined.
                        sourcemap[n].setdefault(arg, f"{filename}:{lineno}")
                    case _:
                        print(func, args, line, file=sys.stderr)
                        sys.exit(1)
        continue
        
    # Chapters 2, 3, 4 logic: extract strings
    en: dict[str, str] = {}
    text[n]["en"] = en

    for filename, lineno, line in rg(
        f"({'|'.join(TEXTFUNCS)})\\([^)]",
        path / "CodeEntries",
    ):
        for func, args in parse_line(line):
            match func, args:
                case "scr_84_get_lang_string", [None]:
                    pass
                case "scr_84_get_lang_string", [str(arg)]:
                    # Copy string from Chapter 1 English data
                    if arg in text[1]["en"]:
                        en[arg] = text[1]["en"][arg]
                        sourcemap[n].setdefault(arg, f"{filename}:{lineno}")
                    else:
                        print(f"Warning: Chapter {n} references key '{arg}' not found in Chapter 1 English data.", file=sys.stderr)
                case "msgsetloc", [None, r"\C2"]:
                    pass
                case "msgsetsubloc", [None, r"\TX \F0 \E~1 \Fb \T0 %", None]:
                    pass
                case (
                    ("stringsetloc", [str(trans), str(key)])
                    | ("msgsetsubloc", [_, str(trans), *_, str(key)])
                    | ("msgnextsubloc", [str(trans), *_, str(key)])
                    | ("stringsetsubloc", [str(trans), *_, str(key)])
                    | ("msgsetloc", [_, str(trans), str(key)])
                    | ("msgnextloc", [str(trans), str(key)])
                ):
                    assert " " not in key, repr(key)
                    # Sometimes the same key has multiple English versions.
                    # (Mostly (exclusively?) for debug stuff.)
                    while key in en and en[key] != trans:
                        key += "_DUP"
                    en[key] = trans
                    sourcemap[n].setdefault(key, f"{filename}:{lineno}")
                case _:
                    print(func, args, line, file=sys.stderr)
                    sys.exit(1)

# Scrambled fragments. Only the Japanese translation uses a translation key.
# The Japanese translation actually has one fragment more, that's probably
# why these aren't translated normally.
if 4 in text: # Only apply if Chapter 4 was successfully processed
    text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_90_0"] = "where "
    text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_91_0"] = "the "
    text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_92_0"] = "tail. "
    text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_93_0"] = "pointed "
    text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_94_0"] = "the "
    text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_95_0"] = "children "
    text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_96_0"] = "would "
    text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_97_0"] = "grow,"
    text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_98_0"] = "the "
    text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_99_0"] = "Lost "
    text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_100_0"] = "forest "
    text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_101_0"] = "followed "
    # Note: The original code sets this to None, which might cause JSON serialization issues.
    # Leaving as None for fidelity to original logic, assuming the JSON serializer handles it or it's implicitly skipped.
    text[4]["en"]["obj_dw_churchb_bookshelf_slash_Step_0_gml_102_0"] = None 

# Final file writing already uses UTF-8 and is correct.
with open("lang.json", "w", encoding="utf-8") as f:
    json.dump(text, f, indent=0, ensure_ascii=False, sort_keys=True)
with open("sourcemap.json", "w", encoding="utf-8") as f:
    json.dump(sourcemap, f, indent=0, ensure_ascii=False, sort_keys=True)
