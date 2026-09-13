#!/usr/bin/env python3
"""마케팅 스크린샷 목업 생성: HTML 생성 → 헤드리스 Chrome 렌더링.

슬라이드마다 layout 이 달라 배치가 다양함:
  hero-bleed  : 헤드라인 상단 중앙 + 정면 대형 폰, 하단 블리드
  left-text   : 좌측 정렬 텍스트 + 오른쪽으로 기운 폰
  text-bottom : 폰 상단 + 텍스트 하단
  flat-rotate : 평면 회전(-5°) 폰, 하단 블리드
  dark        : 다크 배경 반전 + 정면 폰
"""
import subprocess, sys, pathlib, tempfile

# 사용법: 이 파일을 프로젝트 scripts/ 로 복사한 뒤 SRC, W/H, SHOTS 를 수정하고 실행
# 원본(raw) 캡처 폴더. 언어별로 나뉜다.
LANG = (sys.argv[1] if len(sys.argv) > 1 else "en")
SRC = pathlib.Path.cwd() / "docs" / "marketing" / "screenshots" / LANG
OUT = SRC / "marketing"
WORK = pathlib.Path(__file__).parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# ⚠️ 이 앱의 App Store Connect 제출 규격은 **1242x2688** 이다.
#    6.9" 시뮬레이터 원본(1320x2868)은 raw 캡처용이고, 여기서 바로 제출 규격으로 그린다.
W, H = 1242, 2688

SHOTS = [
    ("01-keyboard-in-messages.png", "hero-bleed",  "Works in every app",
     "Tap once,<br>it types itself",      "Your snippets sit right on the keyboard"),
    ("02-template-fill.png",        "left-text",   "Templates",
     "Fill the blank,<br>send it",        "One line, a different name every time"),
    ("03-snippet-stack.png",        "text-bottom", "Snippet stacks",
     "Several values,<br>one key",        "Every slot has a name, so you know what is next"),
    ("04-keyboard-size.png",        "flat-rotate", "Made to fit",
     "The height<br>you want",            "Match your system keyboard, or give it more room"),
    ("05-all-snippets.png",         "dark",        "All in one place",
     "Everything you<br>type again",      "Grouped, searchable, and never leaves your phone"),
]

BASE_CSS = f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:{W}px; height:{H}px; overflow:hidden; }}
/* ⚠️ 이 앱의 기존 마케팅 이미지가 어두운 바탕이다. 밝게 바꾸면 스토어 페이지에서
   이 판만 남의 앱처럼 보인다. 바탕·글자색은 여기서만 정한다. */
body {{ background:#0d0d0e; font-family:-apple-system, "Apple SD Gothic Neo", sans-serif; position:relative; }}
.eyebrow {{ font-size:44px; font-weight:700; color:#0A84FF; letter-spacing:-0.5px; }}
.headline {{ font-size:96px; font-weight:800; color:#f2f2f4; letter-spacing:-2px; line-height:1.22; }}
.sub {{ font-size:46px; font-weight:500; color:#8e8e95; letter-spacing:-1px; line-height:1.4; }}
.phone {{ background:#17171a; border-radius:104px; border:3px solid #3a3a3e; padding:22px;
  box-shadow: 50px 80px 110px rgba(0,0,0,.5), 16px 26px 44px rgba(0,0,0,.35); }}
.phone img {{ width:100%; display:block; border-radius:84px; }}
"""

LAYOUTS = {
    # 1) 정면 대형, 하단 블리드
    "hero-bleed": """
.eyebrow { text-align:center; margin-top:230px; }
.headline { text-align:center; margin-top:34px; padding:0 70px; }
.sub { text-align:center; margin-top:52px; }
.wrap { display:flex; justify-content:center; margin-top:150px; }
.phone { width:1000px; }
""",
    # 2) 좌측 정렬 텍스트 + 오른쪽 기울기, 오른쪽 블리드
    "left-text": """
.eyebrow { text-align:left; margin:250px 0 0 114px; }
.headline { text-align:left; margin:30px 0 0 110px; }
.sub { text-align:left; margin:48px 0 0 114px; }
.wrap { perspective:2600px; perspective-origin:30% 30%; position:absolute; left:300px; top:990px; }
.phone { width:840px; transform:rotateY(16deg) rotateX(2deg); }
""",
    # 3) 폰 상단, 텍스트 하단
    "text-bottom": """
.wrap { perspective:2800px; perspective-origin:50% 40%; display:flex; justify-content:center; margin-top:170px; }
.phone { width:880px; transform:rotateY(-10deg) rotateX(2deg); }
.eyebrow { text-align:center; margin-top:100px; }
.headline { text-align:center; margin-top:26px; padding:0 70px; }
.sub { text-align:center; margin-top:48px; }
""",
    # 4) 평면 회전, 좌측 치우침 + 하단 블리드
    "flat-rotate": """
.eyebrow { text-align:center; margin-top:210px; }
.headline { text-align:center; margin-top:34px; padding:0 70px; }
.sub { text-align:center; margin-top:52px; }
.wrap { position:absolute; left:120px; top:1010px; }
.phone { width:1010px; transform:rotate(-6deg); }
""",
    # 5) 다크 배경 반전 + 정면
    "dark": """
body { background:#131316; }
.eyebrow { text-align:center; margin-top:230px; }
.headline { color:#f5f5f7; text-align:center; margin-top:34px; padding:0 70px; }
.sub { color:#77777d; text-align:center; margin-top:52px; }
.wrap { display:flex; justify-content:center; margin-top:150px; }
.phone { width:930px; border-color:#48484e;
  box-shadow: 0 0 160px rgba(80,140,255,.22), 40px 70px 110px rgba(0,0,0,.55); }
""",
}

# text-bottom 은 폰이 먼저 오는 DOM 순서
# 눈썹글(파란 한 줄)이 헤드라인 위에 선다. 기존 마케팅 이미지가 그 모양이다.
BODY_TEXT_FIRST = ('<div class="eyebrow">{eyebrow}</div><div class="headline">{headline}</div>'
                   '<div class="sub">{sub}</div><div class="wrap"><div class="phone"><img src="{img}"></div></div>')
BODY_PHONE_FIRST = ('<div class="wrap"><div class="phone"><img src="{img}"></div></div>'
                    '<div class="eyebrow">{eyebrow}</div><div class="headline">{headline}</div><div class="sub">{sub}</div>')

HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
{base}{layout}
</style></head><body>{body}</body></html>"""

def main(only=None):
    OUT.mkdir(parents=True, exist_ok=True)
    for fname, layout, eyebrow, headline, sub in SHOTS:
        if only and fname != only:
            continue
        body_tpl = BODY_PHONE_FIRST if layout == "text-bottom" else BODY_TEXT_FIRST
        body = body_tpl.format(eyebrow=eyebrow, headline=headline, sub=sub, img=(SRC / fname).as_uri())
        # ⚠️ 중간 HTML 은 scripts/ 가 아니라 임시 폴더에 쓴다. 예전에는 여기 남아서
        #    산출물이 저장소에 같이 올라갔다.
        html_path = pathlib.Path(tempfile.gettempdir()) / ("clipkb-shot-" + fname.replace(".png", ".html"))
        html_path.write_text(HTML.format(base=BASE_CSS, layout=LAYOUTS[layout], body=body), encoding="utf-8")
        out_png = OUT / fname
        subprocess.run([CHROME, "--headless=new", f"--screenshot={out_png}",
                        f"--window-size={W},{H}", "--force-device-scale-factor=1",
                        "--hide-scrollbars", "--disable-gpu", html_path.as_uri()],
                       check=True, capture_output=True)
        print(f"rendered {out_png}")

if __name__ == "__main__":
    # python3 scripts/make_marketing_screenshots.py [언어] [파일 하나만]
    main(sys.argv[2] if len(sys.argv) > 2 else None)
