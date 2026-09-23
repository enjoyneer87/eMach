# -*- coding: utf-8 -*-
"""File-link boxes for the local HTML reports in this folder (gamma_wall_explainer, drive_model_study).

files_box(title, items) renders a list of analysis files. Each item links to the file (relative href for
files inside this folder, so the link also works on another checkout of the repo; absolute file:/// URL for
data outside it), a folder link, a button that copies the Windows path, and a button that copies a
MATLAB/shell command that opens or runs it. Browsers open .py/.m/.csv/.json as text or download
.slx/.mat, so models are meant to be opened with the copied command. COPY_JS is included once per page.
"""
import html
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
FMU_PY = r"D:\KangDH\Thesis\e10\work_lab_pc1\fmu\fmuenv\Scripts\python.exe"


def _href(p: Path) -> str:
    try:
        rel = p.resolve().relative_to(HERE)
        return quote(rel.as_posix())
    except ValueError:
        return "file:///" + quote(p.as_posix(), safe=":/")


def _default_cmd(p: Path) -> str:
    s = str(p)
    ext = p.suffix.lower()
    if ext in (".slx", ".mdl"):
        return "open_system('%s')" % s
    if ext == ".m":
        return "edit('%s')" % s
    if ext == ".mat":
        return "S = load('%s');" % s
    if ext == ".csv":
        return "T = readtable('%s');" % s
    if ext == ".py":
        py = FMU_PY if p.name in ("lab_fmu.py", "lab_gamma_sweep.py", "lab_stage3c.py", "export_lab_model.py") \
            else "python"
        return '%s "%s"' % (py, s)
    return ""


def _cmd_label(p: Path) -> str:
    ext = p.suffix.lower()
    if ext in (".m", ".slx", ".mdl", ".mat", ".csv"):
        return "MATLAB"
    return "실행" if ext == ".py" else "명령"


def item(path, desc="", cmd=None, label=None):
    """One file entry. cmd=None -> default open command by extension; cmd='' -> no command button."""
    return dict(path=Path(path), desc=desc, cmd=cmd, label=label)


def files_box(title, items, note=""):
    rows = []
    for it in items:
        p = it["path"]
        exists = p.exists()
        name = html.escape(it["label"] or p.name)
        cmd = _default_cmd(p) if it["cmd"] is None else it["cmd"]
        link = '<a href="%s">%s</a>' % (_href(p), name) if exists else '<span class="missing">%s (없음)</span>' % name
        folder = '<a class="fold" href="%s" title="폴더 열기">폴더</a>' % _href(p.parent)
        btn = '<button class="cp" data-copy="%s" title="%s">경로</button>' % (html.escape(str(p), quote=True),
                                                                          html.escape(str(p), quote=True))
        if cmd:
            btn += '<button class="cp" data-copy="%s" title="%s">%s</button>' % (
                html.escape(cmd, quote=True), html.escape(cmd, quote=True), _cmd_label(p))
        rows.append('<li>%s <span class="mut">%s</span> <span class="acts">%s %s</span></li>' % (
            link, html.escape(it["desc"]), folder, btn))
    nt = '<p class="mut small">%s</p>' % note if note else ""
    return '<details class="files" open><summary>%s</summary><ul>%s</ul>%s</details>' % (
        html.escape(title), "".join(rows), nt)


FILES_CSS = """
details.files{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:8px;padding:6px 12px;margin:10px 0}
details.files summary{cursor:pointer;font-weight:600;font-size:14px}
details.files ul{margin:6px 0 2px;padding-left:18px}details.files li{margin:3px 0;font-size:13.5px;line-height:1.5}
details.files a{color:var(--acc)}details.files .acts{white-space:nowrap}
details.files a.fold{font-size:12px;margin-left:4px}
button.cp{font:12px system-ui,sans-serif;border:1px solid var(--line);background:var(--bg);color:var(--fg);border-radius:4px;padding:0 6px;margin-left:4px;cursor:pointer}
button.cp.ok{border-color:var(--ok);color:var(--ok)}
.missing{color:var(--bad)}.small{font-size:12.5px}
"""

COPY_JS = """<script>
document.addEventListener('click', function (e) {
  var b = e.target.closest('button.cp'); if (!b) return;
  var t = b.getAttribute('data-copy'), lab = b.dataset.lab || (b.dataset.lab = b.textContent);
  function done() { b.textContent = '복사됨'; b.classList.add('ok'); setTimeout(function () { b.textContent = lab; b.classList.remove('ok'); }, 1200); }
  function fallback() { var a = document.createElement('textarea'); a.value = t; document.body.appendChild(a); a.select();
    try { document.execCommand('copy'); done(); } catch (x) { window.prompt('복사하세요', t); } document.body.removeChild(a); }
  if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(t).then(done, fallback); } else { fallback(); }
});
</script>"""

LINK_NOTE = ("링크는 브라우저가 파일을 열거나 내려받습니다(.py/.m/.csv/.json은 텍스트로 보이고 .slx/.mat는 내려받기). "
             "모델·데이터는 <b>경로</b> 또는 <b>MATLAB</b> 버튼으로 명령을 복사해 MATLAB 명령 창에 붙여 넣으세요. "
             "<b>폴더</b>는 그 폴더의 파일 목록을 엽니다.")
