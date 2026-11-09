#!/usr/bin/env python3
"""plan.md → index.html 빌드 스크립트.

사용법:  pip install markdown && python3 aetherfall/build.py
기획서를 고칠 때는 plan.md만 수정하고 이 스크립트로 index.html을 다시 만든다.
"""
import html
import pathlib
import re

import markdown

HERE = pathlib.Path(__file__).resolve().parent

# ── 11.2 시스템 구성도 (인라인 SVG) ─────────────────────────────────────
ARCH = """
<figure class="diagram" aria-label="시스템 구성도">
<svg viewBox="0 0 760 430" role="img">
  <title>AETHERFALL 시스템 구성도</title>
  <defs>
    <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" class="arrowhead"/>
    </marker>
  </defs>
  <!-- client -->
  <rect class="box accent" x="300" y="10" width="160" height="44" rx="8"/>
  <text x="380" y="30" class="t">UE5 클라이언트</text>
  <text x="380" y="46" class="s">예측·보간·연출(GAS)</text>
  <!-- entry -->
  <rect class="box" x="40" y="100" width="170" height="44" rx="8"/>
  <text x="125" y="120" class="t">인증 서비스</text>
  <text x="125" y="136" class="s">플랫폼 OAuth · JWT</text>
  <rect class="box gold" x="295" y="100" width="170" height="44" rx="8"/>
  <text x="380" y="120" class="t">게이트웨이 (UDP)</text>
  <text x="380" y="136" class="s">암호화 · DDoS 흡수</text>
  <rect class="box" x="550" y="100" width="170" height="44" rx="8"/>
  <text x="635" y="120" class="t">채팅 서비스</text>
  <text x="635" y="136" class="s">Go + NATS</text>
  <!-- zone layer -->
  <rect class="group" x="240" y="180" width="280" height="96" rx="10"/>
  <text x="380" y="198" class="g">존 서버 플릿 (C++ · AetherSim · 20Hz)</text>
  <rect class="box" x="255" y="208" width="78" height="54" rx="6"/>
  <text x="294" y="232" class="t">존 A</text><text x="294" y="248" class="s">판정·AI</text>
  <rect class="box" x="341" y="208" width="78" height="54" rx="6"/>
  <text x="380" y="232" class="t">존 B</text><text x="380" y="248" class="s">핸드오프</text>
  <rect class="box" x="427" y="208" width="78" height="54" rx="6"/>
  <text x="466" y="232" class="t">인스턴스</text><text x="466" y="248" class="s">던전·영토전</text>
  <rect class="box" x="40" y="214" width="170" height="44" rx="8"/>
  <text x="125" y="234" class="t">월드 디렉터</text>
  <text x="125" y="250" class="s">존 배치 · 입장 티켓</text>
  <!-- services -->
  <rect class="group" x="40" y="310" width="480" height="70" rx="10"/>
  <text x="280" y="326" class="g">백엔드 서비스 (Go) — 아이템·재화 이동의 유일한 주체</text>
  <rect class="box" x="55" y="334" width="105" height="36" rx="6"/><text x="107" y="357" class="t">캐릭터</text>
  <rect class="box" x="170" y="334" width="105" height="36" rx="6"/><text x="222" y="357" class="t">경제·거래소</text>
  <rect class="box" x="285" y="334" width="105" height="36" rx="6"/><text x="337" y="357" class="t">길드</text>
  <rect class="box" x="400" y="334" width="105" height="36" rx="6"/><text x="452" y="357" class="t">계정·결제</text>
  <!-- data -->
  <rect class="box violet" x="560" y="310" width="160" height="70" rx="8"/>
  <text x="640" y="334" class="t">PostgreSQL</text>
  <text x="640" y="350" class="s">원장·아이템·시장</text>
  <text x="640" y="366" class="s">+ Redis · ClickHouse</text>
  <rect class="box" x="560" y="214" width="160" height="44" rx="8"/>
  <text x="640" y="234" class="t">모니터링</text>
  <text x="640" y="250" class="s">Prometheus · Grafana</text>
  <text x="380" y="415" class="note">실선: 클라이언트 진입 경로 3개 · 점선: 서버 내부 호출</text>
  <!-- arrows -->
  <path class="ln" d="M330 54 L150 100" marker-end="url(#ah)"/>
  <path class="ln" d="M380 54 L380 100" marker-end="url(#ah)"/>
  <path class="ln" d="M430 54 L610 100" marker-end="url(#ah)"/>
  <path class="ln dash" d="M380 144 L380 180" marker-end="url(#ah)"/>
  <path class="ln dash" d="M210 236 L240 236" marker-end="url(#ah)"/>
  <path class="ln dash" d="M125 144 L125 214" marker-end="url(#ah)"/>
  <path class="ln dash" d="M380 276 L380 310" marker-end="url(#ah)"/>
  <path class="ln dash" d="M520 345 L560 345" marker-end="url(#ah)"/>
  <path class="ln dash" d="M520 236 L560 236" marker-end="url(#ah)"/>
</svg>
</figure>
"""

# ── 13장 Phase 타임라인 ────────────────────────────────────────────────
PHASES = [
    ("0. 사전 기술 데모", -3, 0),
    ("1. 핵심 기술 검증", 1, 8),
    ("2. 게임 핵심 시스템", 7, 18),
    ("3. 온라인 게임 기반", 19, 30),
    ("4. 경제와 월드", 24, 40),
    ("5. 대규모 콘텐츠", 30, 46),
    ("6. 출시 준비", 40, 66),
]
GATES = [(8, "G0"), (18, "GA"), (48, "GB · EA"), (66, "정식 출시")]


def timeline() -> str:
    lo, hi = -3, 66
    span = hi - lo

    def pct(m: float) -> float:
        return (m - lo) / span * 100

    rows = []
    for name, a, b in PHASES:
        start = a - 1 if a > 0 else a  # M1은 0~1 구간에서 시작
        left, width = pct(start), pct(b) - pct(start)
        label = "사전" if b <= 0 else f"M{a}~M{b}"
        rows.append(
            f'<div class="tl-row"><span class="tl-name">{html.escape(name)}</span>'
            f'<span class="tl-track"><span class="tl-bar" style="left:{left:.2f}%;width:{width:.2f}%">'
            f"<em>{label}</em></span></span></div>"
        )
    gates = "".join(
        f'<span class="tl-gate{" end" if m == hi else ""}" style="left:{pct(m):.2f}%"><b>{html.escape(t)}</b><i>M{m}</i></span>'
        for m, t in GATES
    )
    return (
        '<figure class="timeline" aria-label="Phase 일정">'
        f'<div class="tl-gates"><span class="tl-name"></span><span class="tl-track">{gates}</span></div>'
        + "".join(rows)
        + "</figure>"
    )


TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AETHERFALL 기획서 v0.2</title>
<meta name="description" content="AETHERFALL 에테르폴 — 하이 판타지 오픈월드 MMORPG 개발 기획서 v0.2">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600;800&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#f7f6fb; --surface:#ffffff; --surface2:#f0eef7; --text:#1d1830; --muted:#5d5873;
  --line:#dcd8e8; --accent:#0f9e92; --accent-soft:#3FE0D0; --gold:#b9821a; --gold-soft:#F2B544;
  --abyss:#2B1B4F; --code-bg:#f1eff8; --shadow:0 1px 2px rgba(20,10,40,.06),0 6px 24px rgba(20,10,40,.06);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0f0b1c; --surface:#171229; --surface2:#1f1836; --text:#ece9f6; --muted:#a8a2c0;
    --line:#2f2750; --accent:#3FE0D0; --accent-soft:#3FE0D0; --gold:#F2B544; --gold-soft:#F2B544;
    --abyss:#8b6fe0; --code-bg:#130f24; --shadow:none;
  }
}
:root[data-theme="dark"]{
  --bg:#0f0b1c; --surface:#171229; --surface2:#1f1836; --text:#ece9f6; --muted:#a8a2c0;
  --line:#2f2750; --accent:#3FE0D0; --accent-soft:#3FE0D0; --gold:#F2B544; --gold-soft:#F2B544;
  --abyss:#8b6fe0; --code-bg:#130f24; --shadow:none;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:16px}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.75 "Noto Sans KR",system-ui,-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;word-break:keep-all;overflow-wrap:break-word}
a{color:var(--accent)}
.hero{position:relative;overflow:hidden;background:radial-gradient(1200px 400px at 70% -10%,rgba(63,224,208,.28),transparent 60%),radial-gradient(800px 360px at 10% 120%,rgba(242,181,68,.22),transparent 60%),linear-gradient(160deg,#1a1033,#2B1B4F 55%,#120c25);color:#f3f0ff;padding:56px 16px 44px}
.hero-in{max-width:1180px;margin:0 auto}
.hero .ring{position:absolute;right:-60px;top:-40px;width:320px;height:320px;opacity:.35}
.hero .kicker{letter-spacing:.24em;font-size:12px;color:#3FE0D0;font-weight:700}
.hero h1{font-family:"Noto Serif KR",serif;font-weight:800;font-size:clamp(30px,6vw,56px);line-height:1.15;margin:.2em 0 .25em}
.hero h1 small{display:block;font-size:.42em;font-weight:600;color:#F2B544;letter-spacing:.02em;margin-top:.35em}
.hero p{margin:0;color:#cfc8ea}
.hero .tag{font-family:"Noto Serif KR",serif;font-size:18px;color:#fff;margin:14px 0 6px}
.layout{max-width:1180px;margin:0 auto;padding:0 16px;display:grid;grid-template-columns:240px minmax(0,1fr);gap:40px}
nav.toc{position:sticky;top:0;align-self:start;max-height:100vh;overflow:auto;padding:24px 0;font-size:13.5px}
nav.toc b{display:block;font-size:12px;letter-spacing:.14em;color:var(--muted);margin-bottom:8px}
nav.toc ol{list-style:none;margin:0;padding:0}
nav.toc a{display:block;padding:4px 10px;border-left:2px solid var(--line);color:var(--muted);text-decoration:none}
nav.toc a:hover,nav.toc a.on{color:var(--text);border-left-color:var(--accent)}
.themebtn{margin-top:16px;background:var(--surface);color:var(--text);border:1px solid var(--line);border-radius:999px;padding:5px 12px;font:inherit;font-size:12.5px;cursor:pointer}
main{min-width:0;padding:16px 0 80px}
main h1{display:none}
.meta{color:var(--muted);margin:0}
main h2{font-family:"Noto Serif KR",serif;font-size:26px;margin:56px 0 12px;padding-top:12px;border-top:1px solid var(--line)}
main h3{font-size:18.5px;margin:34px 0 10px;color:var(--text)}
main h3::before{content:"";display:inline-block;width:8px;height:8px;border:2px solid var(--accent);border-radius:50%;margin-right:9px;vertical-align:2px}
main h4{font-size:16px;margin:28px 0 8px}
p,li{max-width:78ch}
.tw{overflow-x:auto;margin:12px 0 18px;border:1px solid var(--line);border-radius:10px;background:var(--surface);box-shadow:var(--shadow)}
table{border-collapse:collapse;width:100%;font-size:13.5px;line-height:1.6}
th,td{padding:9px 12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
th{background:var(--surface2);font-weight:700;white-space:nowrap;position:sticky;top:0}
tr:last-child td{border-bottom:0}
td:first-child{font-weight:500;min-width:6.5em}
.wide table{min-width:1100px}
.mid table{min-width:760px}
pre{background:var(--code-bg);border:1px solid var(--line);border-radius:10px;padding:14px 16px;overflow:auto;font-size:12.5px;line-height:1.6}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.92em}
:not(pre)>code{background:var(--code-bg);padding:1px 5px;border-radius:4px}
.formula{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--gold);border-radius:10px;padding:16px 18px;font-family:"Noto Serif KR",serif;font-size:16px;overflow-x:auto;white-space:nowrap;margin:12px 0 16px}
.frac{display:inline-flex;flex-direction:column;vertical-align:middle;text-align:center;font-size:.86em;margin:0 3px}
.frac span:first-child{border-bottom:1px solid currentColor;padding:0 4px}
.sw{display:inline-block;width:.85em;height:.85em;border-radius:3px;background:var(--c);vertical-align:-1px;margin:0 4px 0 2px;border:1px solid rgba(127,127,127,.4)}
.zone{display:inline-block;padding:1px 8px;border-radius:999px;font-weight:700;font-size:12.5px;white-space:nowrap}
.z1{background:#d6ecff;color:#0b4d8a}.z2{background:#d8f3dc;color:#1b6b34}.z3{background:#fff1c2;color:#7a5700}.z4{background:#ffd9d6;color:#9b1c13}.z5{background:#2a2438;color:#e6defa}
ul.task{list-style:none;padding-left:4px}
.diagram{margin:14px 0 20px;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px;overflow-x:auto}
.diagram svg{display:block;width:100%;min-width:620px;height:auto}
.diagram .box{fill:var(--surface2);stroke:var(--line);stroke-width:1.2}
.diagram .box.accent{stroke:var(--accent);stroke-width:2}
.diagram .box.gold{stroke:var(--gold);stroke-width:2}
.diagram .box.violet{stroke:var(--abyss);stroke-width:2}
.diagram .group{fill:none;stroke:var(--muted);stroke-dasharray:4 4;stroke-width:1}
.diagram text{text-anchor:middle;fill:var(--text);font-family:inherit}
.diagram .t{font-size:13px;font-weight:700}
.diagram .s{font-size:11px;fill:var(--muted)}
.diagram .g{font-size:11.5px;fill:var(--muted);font-weight:500}
.diagram .note{font-size:11px;fill:var(--muted)}
.diagram .ln{stroke:var(--muted);stroke-width:1.4;fill:none}
.diagram .dash{stroke-dasharray:5 4}
.diagram .arrowhead{fill:var(--muted)}
.timeline{margin:14px 0 20px;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px;overflow-x:auto}
.tl-row,.tl-gates{display:grid;grid-template-columns:150px minmax(420px,1fr);align-items:center;gap:12px;min-height:30px}
.tl-name{font-size:13px;font-weight:500}
.tl-track{position:relative;height:22px;border-left:1px dashed var(--line)}
.tl-bar{position:absolute;top:2px;height:18px;border-radius:5px;background:linear-gradient(90deg,var(--accent),var(--accent-soft));display:flex;align-items:center;overflow:hidden}
.tl-bar em{font-style:normal;font-size:11px;font-weight:700;color:#06302c;padding:0 6px;white-space:nowrap}
.tl-gates{min-height:38px}
.tl-gates .tl-track{height:36px;border-left:0}
.tl-gate{position:absolute;bottom:0;transform:translateX(-50%);text-align:center;font-size:11px;line-height:1.25;white-space:nowrap}
.tl-gate b{display:block;color:var(--gold)}
.tl-gate i{font-style:normal;color:var(--muted)}
.tl-gate.end{transform:translateX(-100%);text-align:right}.tl-gate.end::after{margin:2px 0 0 auto}
.tl-gate::after{content:"";display:block;width:2px;height:6px;margin:2px auto 0;background:var(--gold)}
footer{color:var(--muted);font-size:13px;border-top:1px solid var(--line);margin-top:56px;padding-top:16px}
@media (max-width: 900px){
  .layout{grid-template-columns:1fr;gap:0}
  nav.toc{position:static;max-height:none;padding:16px 0 0}
  nav.toc ol{display:flex;gap:6px;overflow-x:auto;padding-bottom:6px}
  nav.toc a{border:1px solid var(--line);border-radius:999px;padding:3px 10px;white-space:nowrap}
  main h2{font-size:22px}
}
@media print{nav.toc,.themebtn{display:none}.layout{display:block}.hero{padding:24px}.tw{overflow:visible}.wide table,.mid table{min-width:0}}
</style>
</head>
<body>
<header class="hero">
  <svg class="ring" viewBox="0 0 200 200" aria-hidden="true"><g fill="none" stroke="#3FE0D0" stroke-width="3"><path d="M100 18a82 82 0 0 1 74 47"/><path d="M182 100a82 82 0 0 1-40 70"/><path d="M118 181a82 82 0 0 1-82-34"/><path d="M22 112a82 82 0 0 1 48-88"/></g><circle cx="100" cy="100" r="46" fill="none" stroke="#F2B544" stroke-width="2" stroke-dasharray="20 9"/></svg>
  <div class="hero-in">
    <div class="kicker">GAME DESIGN DOCUMENT · v0.2</div>
    <h1>AETHERFALL<small>에테르폴 — 하이 판타지 오픈월드 MMORPG 개발 기획서</small></h1>
    <p class="tag">"하늘이 무너진 날, 세계는 다시 쓰였다"</p>
    <p>2026년 11월 9일 · @성연호 · 버전 0.2 (검토 반영)</p>
  </div>
</header>
<div class="layout">
  <nav class="toc" aria-label="목차">
    <b>목차</b>
    <ol>{toc}</ol>
    <button class="themebtn" type="button" id="themeBtn">테마 전환</button>
  </nav>
  <main>
{body}
    <footer>AETHERFALL 기획서 v0.2 · 설계 초안이며 수치는 프로토타입과 부하 테스트로 확정한다.</footer>
  </main>
</div>
<script>
(function(){
  var root=document.documentElement,btn=document.getElementById('themeBtn');
  try{var t=localStorage.getItem('af-theme');if(t)root.setAttribute('data-theme',t);}catch(e){}
  btn.addEventListener('click',function(){
    var cur=root.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
    var next=cur==='dark'?'light':'dark';root.setAttribute('data-theme',next);
    try{localStorage.setItem('af-theme',next);}catch(e){}
  });
  var links=[].slice.call(document.querySelectorAll('nav.toc a'));
  var map=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1));});
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){
      links.forEach(function(l){l.classList.remove('on')});
      var i=map.indexOf(e.target);if(i>=0)links[i].classList.add('on');}});},{rootMargin:'0px 0px -75% 0px'});
    map.forEach(function(s){if(s)io.observe(s)});
  }
})();
</script>
</body>
</html>
"""


def build() -> None:
    src = (HERE / "plan.md").read_text(encoding="utf-8")
    md = markdown.Markdown(extensions=["tables", "fenced_code", "attr_list", "sane_lists"])
    body = md.convert(src)

    # 표를 스크롤 래퍼로 감싸고, 열 수에 따라 최소 폭을 준다
    def wrap(m: re.Match) -> str:
        table = m.group(0)
        head = re.search(r"<thead>.*?</thead>", table, re.S)
        cols = head.group(0).count("<th") if head else 0
        cls = "tw wide" if cols >= 7 else "tw mid" if cols >= 5 else "tw"
        return f'<div class="{cls}">{table}</div>'

    body = re.sub(r"<table>.*?</table>", wrap, body, flags=re.S)
    # 체크리스트
    body = body.replace("<li>[ ] ", '<li>☐ ')
    body = re.sub(r"<ul>(\s*<li>☐)", r'<ul class="task">\1', body)
    body = body.replace("<!--ARCH_DIAGRAM-->", ARCH).replace("<!--TIMELINE-->", timeline())

    toc = "".join(
        f'<li><a href="#{i}">{html.escape(re.sub(r"<[^>]+>", "", t))}</a></li>'
        for i, t in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    )
    out = TEMPLATE.replace("{toc}", toc).replace("{body}", body)
    (HERE / "index.html").write_text(out, encoding="utf-8")
    print(f"wrote {HERE / 'index.html'} ({len(out):,} bytes)")


if __name__ == "__main__":
    build()
