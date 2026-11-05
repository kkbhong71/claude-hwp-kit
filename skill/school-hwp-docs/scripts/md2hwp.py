# -*- coding: utf-8 -*-
"""
md2hwp.py  -  마크다운(.md) 텍스트를 '꾸며진' 한글 문서(.hwp)로 변환

사용법:
    python md2hwp.py 내용.md                 -> 내용.hwp 생성
    python md2hwp.py 내용.md 보고서.hwp       -> 보고서.hwp 생성
    python md2hwp.py 내용.md 보고서.hwp --show  -> 변환 후 한글 창 띄우기
    python md2hwp.py 내용.md 보고서.hwp --pdf   -> 같은 이름의 PDF도 함께 저장

지원 문법과 꾸밈:
    # 제목        -> 남색 제목 상자 (흰 글씨, 가운데)
    ## 1. 중제목   -> 번호 칸 + 연한 바탕 제목 띠
    ### 소제목     -> ■ 표시 + 굵은 글씨
    - 항목         -> ○ 글머리표 (내어쓰기)
    1. 항목        -> 번호 문단 (내어쓰기)
    > 인용         -> ※ 참고 문구 (회색 작은 글씨)
    | a | b |     -> 표 (머리행 남색, 줄무늬 행, '합계' 행 강조)
    빈 줄 / ---    -> 무시 (문단 간격은 자동으로 조정)

(단순한 이전 버전은 md2hwp_basic.py 에 보관되어 있습니다.)
"""
import os
import re
import sys
import traceback

# ===== 디자인 설정 (여기만 고치면 전체 문서 분위기가 바뀝니다) =====
FONT_HEAD = "맑은 고딕"      # 제목·표 글꼴
FONT_BODY = "함초롬바탕"     # 본문 글꼴
SIZE_TITLE, SIZE_H2, SIZE_H3 = 20, 13, 11.5
SIZE_BODY, SIZE_TABLE, SIZE_NOTE = 11, 10, 9.5
LINE_SPACING = 160           # 본문 줄 간격(%)
MARGIN_SIDE, MARGIN_TOP, MARGIN_BOTTOM = 20, 18, 15   # 용지 여백(mm)

MAIN = (31, 56, 100)         # 주 색상 (남색)
ACCENT = (231, 238, 248)     # 연한 바탕색
STRIPE = (246, 249, 253)     # 표 줄무늬 바탕
GRID = (180, 188, 200)       # 표 안쪽 선 색
TEXT = (38, 38, 38)          # 본문 글자색
NOTE = (110, 110, 110)       # 참고 문구 색
WHITE = (255, 255, 255)


# ---------------------------------------------------------------- 파싱
def parse_blocks(lines):
    """마크다운 줄 목록을 (종류, 내용) 블록 목록으로 변환"""
    blocks, i = [], 0
    while i < len(lines):
        stripped = lines[i].strip()

        if stripped.startswith("|") and i + 1 < len(lines) \
                and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[i + 1]):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.match(r"^[\s:\-]+$", "".join(cells)):
                    rows.append(cells)
                i += 1
            if rows:
                blocks.append(("table", rows))
            continue

        if not stripped or re.match(r"^[-*]{3,}$", stripped):
            pass
        elif stripped.startswith("### "):
            blocks.append(("h3", stripped[4:].strip()))
        elif stripped.startswith("## "):
            blocks.append(("h2", stripped[3:].strip()))
        elif stripped.startswith("# "):
            blocks.append(("h1", stripped[2:].strip()))
        elif stripped.startswith(">"):
            blocks.append(("quote", stripped.lstrip("> ").strip()))
        elif re.match(r"^[-*+]\s+", stripped):
            blocks.append(("bullet", re.sub(r"^[-*+]\s+", "", stripped)))
        elif re.match(r"^\d+[.)]\s+", stripped):
            blocks.append(("number", stripped))
        else:
            blocks.append(("para", stripped))
        i += 1
    return blocks


def clean_inline(text):
    """**굵게**, *기울임*, `코드`, [링크](주소) 표시를 제거해 순수 텍스트로"""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", text)
    return text


# ---------------------------------------------------------------- 서식 도우미
class Styler:
    def __init__(self, hwp):
        self.hwp = hwp

    def rgb(self, c):
        return self.hwp.RGBColor(*c)

    def font(self, size, bold=False, color=TEXT, face=FONT_BODY):
        self.hwp.set_font(Height=size, Bold=bold, FaceName=face,
                          TextColor=self.rgb(color))

    def para(self, align="Justify", left=0, indent=0, before=0, after=0,
             spacing=LINE_SPACING, keep_next=0):
        self.hwp.set_para(AlignType=align, LeftMargin=left, Indentation=indent,
                          PrevSpacing=before, NextSpacing=after,
                          LineSpacing=spacing, KeepWithNext=keep_next)

    def write(self, text):
        self.hwp.insert_text(text)

    def new_para(self):
        self.hwp.BreakPara()

    def cell(self, fill=None, left=None, right=None, top=None, bottom=None):
        """현재 셀의 배경색과 테두리를 지정.
        테두리 값: None(선 없음) 또는 (굵기 문자열, 색) 예: ("0.12mm", GRID)"""
        hwp = self.hwp
        hwp.TableCellBlock()
        pset = hwp.HParameterSet.HCellBorderFill
        hwp.HAction.GetDefault("CellBorderFill", pset.HSet)
        for side, spec in (("Left", left), ("Right", right),
                           ("Top", top), ("Bottom", bottom)):
            if spec is None:
                setattr(pset, "BorderType" + side, hwp.HwpLineType("None"))
            else:
                width, color = spec
                setattr(pset, "BorderType" + side, hwp.HwpLineType("Solid"))
                setattr(pset, "BorderWidth" + side, hwp.HwpLineWidth(width))
                # 한글 API 자체의 오타: 왼쪽만 'BorderCorlorLeft'
                attr = "BorderCorlorLeft" if side == "Left" else "BorderColor" + side
                setattr(pset, attr, self.rgb(color))
        if fill:
            pset.FillAttr.type = hwp.BrushType("NullBrush|WinBrush")
            pset.FillAttr.WinBrushFaceColor = self.rgb(fill)
            pset.FillAttr.WinBrushHatchColor = self.rgb(fill)
            pset.FillAttr.WinBrushFaceStyle = hwp.HatchStyle("None")
            pset.FillAttr.WindowsBrush = 1
        else:
            pset.FillAttr.type = hwp.BrushType("NullBrush")
        hwp.HAction.Execute("CellBorderFill", pset.HSet)
        hwp.Cancel()

    def leave_table(self):
        # 표를 만들면 한글이 표 아래에 빈 문단을 자동으로 만들어 주므로
        # 문서 끝으로만 이동하면 바로 다음 내용을 쓸 수 있음
        self.hwp.Cancel()
        self.hwp.MoveDocEnd()

    def page_setup(self):
        """용지 여백 설정 + 쪽 번호(- 1 -) 넣기"""
        hwp = self.hwp
        pset = hwp.HParameterSet.HSecDef
        hwp.HAction.GetDefault("PageSetup", pset.HSet)
        pd = pset.PageDef
        pd.LeftMargin = hwp.MiliToHwpUnit(MARGIN_SIDE)
        pd.RightMargin = hwp.MiliToHwpUnit(MARGIN_SIDE)
        pd.TopMargin = hwp.MiliToHwpUnit(MARGIN_TOP)
        pd.BottomMargin = hwp.MiliToHwpUnit(MARGIN_BOTTOM)
        pd.HeaderLen = hwp.MiliToHwpUnit(10)
        pd.FooterLen = hwp.MiliToHwpUnit(10)
        pset.HSet.SetItem("ApplyClass", 24)
        pset.HSet.SetItem("ApplyTo", 3)
        hwp.HAction.Execute("PageSetup", pset.HSet)
        try:
            hwp.page_num_pos(position="BottomCenter", side_char=True)
        except Exception:
            pass


# ---------------------------------------------------------------- 블록별 그리기
def draw_title(s, text):
    s.para("Center", before=0, after=4, spacing=100)
    s.hwp.create_table(rows=1, cols=1, treat_as_char=True, header=False)
    s.hwp.set_table_inside_margin(left=4, right=4, top=5, bottom=5)
    s.cell(fill=MAIN)
    s.para("Center", spacing=100)
    # 제목이 한 줄에 들어가도록 글자 크기 자동 조절
    usable_mm = 210 - 2 * MARGIN_SIDE - 12
    em = max(text_width(text) / 2, 1)
    size = max(14, min(SIZE_TITLE, usable_mm / em / 0.3528 * 0.92))
    s.font(round(size, 1), True, WHITE, FONT_HEAD)
    s.write(text)
    s.leave_table()


def draw_h2(s, text):
    m = re.match(r"^(\d+)[.)]?\s*(.*)$", text)
    num, title = (m.group(1), m.group(2)) if m else ("▶", text)
    s.para("Left", before=14, after=6, spacing=100, keep_next=1)
    s.hwp.create_table(rows=1, cols=2, treat_as_char=True, header=False)
    s.hwp.set_table_inside_margin(left=2.5, right=2.5, top=1.6, bottom=1.6)
    # 번호 칸
    s.cell(fill=MAIN)
    s.para("Center", spacing=100)
    s.font(SIZE_H2, True, WHITE, FONT_HEAD)
    s.write(num)
    s.hwp.TableRightCell()
    # 제목 칸
    s.cell(fill=ACCENT, bottom=("0.4mm", MAIN))
    s.para("Left", spacing=100)
    s.font(SIZE_H2, True, MAIN, FONT_HEAD)
    s.write(title)
    s.hwp.set_col_width([1, 13])
    s.leave_table()


def draw_h3(s, text):
    s.para("Left", before=8, after=3, keep_next=1)
    s.font(SIZE_H3, True, MAIN, FONT_HEAD)
    s.write("■ ")
    s.font(SIZE_H3, True, TEXT, FONT_HEAD)
    s.write(text)
    s.new_para()


def draw_bullet(s, text):
    s.para("Justify", left=12, indent=-11, before=1, after=1)
    s.font(SIZE_BODY, False, MAIN, FONT_BODY)
    s.write("○ ")
    s.font(SIZE_BODY, False, TEXT, FONT_BODY)
    s.write(text)
    s.new_para()


def draw_number(s, text):
    m = re.match(r"^(\d+[.)])\s+(.*)$", text)
    mark, body = (m.group(1), m.group(2)) if m else ("", text)
    s.para("Justify", left=16, indent=-15, before=1, after=1)
    s.font(SIZE_BODY, True, MAIN, FONT_BODY)
    s.write(mark + " ")
    s.font(SIZE_BODY, False, TEXT, FONT_BODY)
    s.write(body)
    s.new_para()


def draw_quote(s, text):
    s.para("Left", left=12, indent=-11, before=3, after=3)
    s.font(SIZE_NOTE, False, NOTE, FONT_BODY)
    s.write("※ " + text)
    s.new_para()


def draw_para(s, text):
    s.para("Justify", left=0, indent=0, before=2, after=2)
    s.font(SIZE_BODY, False, TEXT, FONT_BODY)
    s.write(text)
    s.new_para()


def text_width(t):
    """한글은 2칸, 영문·숫자는 1칸으로 대략 계산"""
    return sum(2 if ord(ch) > 127 else 1 for ch in t)


def draw_table(s, rows):
    hwp = s.hwp
    cols = max(len(r) for r in rows)
    rows = [[clean_inline(c) for c in r] + [""] * (cols - len(r)) for r in rows]
    nrows = len(rows)

    # 열 너비: 짧은 열은 줄바꿈 없이 들어갈 만큼 확보하고,
    # 남는 폭을 긴 열들이 내용 길이에 비례해 나눠 가짐
    budget = (210 - 2 * MARGIN_SIDE) / (SIZE_TABLE * 0.3528 / 2) * 0.9  # 표 한 줄에 들어가는 대략적 칸 수
    need = [max(text_width(r[c]) for r in rows) + 4 for c in range(cols)]
    if sum(need) <= budget:
        widths = need
    else:
        # 상한 T를 찾아 각 열 너비 = min(필요 너비, T) 로 배분 (짧은 열 우선 보장)
        lo, hi = 0.0, float(max(need))
        for _ in range(40):
            mid = (lo + hi) / 2
            if sum(min(n, mid) for n in need) > budget:
                hi = mid
            else:
                lo = mid
        widths = [min(n, lo) for n in need]
    # 짧은 내용만 있는 열은 가운데 정렬
    center_col = [max(text_width(r[c]) for r in rows[1:] or rows) <= 12
                  for c in range(cols)]

    s.para("Center", before=4, after=4, spacing=100)
    hwp.create_table(rows=nrows, cols=cols, treat_as_char=True, header=True)
    hwp.set_table_inside_margin(left=2, right=2, top=1.3, bottom=1.3)

    thin = ("0.12mm", GRID)
    thick = ("0.4mm", MAIN)
    for r, row in enumerate(rows):
        is_head = r == 0
        is_total = (r == nrows - 1 and nrows > 2
                    and row[0].replace(" ", "") in ("합계", "계", "총계", "소계"))
        for c in range(cols):
            if is_head:
                fill = MAIN
            elif is_total:
                fill = ACCENT
            elif r % 2 == 0:
                fill = STRIPE
            else:
                fill = None
            s.cell(fill=fill,
                   left=None if c == 0 else thin,
                   right=None if c == cols - 1 else thin,
                   top=thick if is_head else thin,
                   bottom=thick if (is_head or r == nrows - 1) else thin)
            align = "Center" if (is_head or center_col[c]) else "Left"
            s.para(align, spacing=130)
            if is_head:
                s.font(SIZE_TABLE, True, WHITE, FONT_HEAD)
            else:
                s.font(SIZE_TABLE, is_total, MAIN if is_total else TEXT, FONT_HEAD)
            s.write(row[c])
            if not (r == nrows - 1 and c == cols - 1):
                hwp.TableRightCell()

    hwp.set_col_width(widths)
    s.leave_table()


DRAW = {"h1": draw_title, "h2": draw_h2, "h3": draw_h3, "bullet": draw_bullet,
        "number": draw_number, "quote": draw_quote, "para": draw_para}


# ---------------------------------------------------------------- 실행
def build(md_path, hwp_path, show=False, pdf=False):
    from pyhwpx import Hwp

    with open(md_path, "r", encoding="utf-8") as f:
        blocks = parse_blocks(f.read().splitlines())

    if os.path.exists(hwp_path):
        os.remove(hwp_path)

    hwp = Hwp(new=True, visible=show)
    s = Styler(hwp)
    s.page_setup()

    for kind, content in blocks:
        if kind == "table":
            draw_table(s, content)
        else:
            DRAW[kind](s, clean_inline(content))

    hwp.save_as(hwp_path)
    if pdf:
        hwp.save_as(os.path.splitext(hwp_path)[0] + ".pdf", format="PDF")
    if not show:
        hwp.quit()
    return hwp_path


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    show = "--show" in sys.argv
    pdf = "--pdf" in sys.argv

    if not args:
        print("사용법: python md2hwp.py <입력.md> [출력.hwp] [--show] [--pdf]")
        sys.exit(1)

    md_path = os.path.abspath(args[0])
    if not os.path.exists(md_path):
        print("입력 파일을 찾을 수 없습니다:", md_path)
        sys.exit(1)

    hwp_path = os.path.abspath(args[1]) if len(args) > 1 \
        else os.path.splitext(md_path)[0] + ".hwp"

    try:
        build(md_path, hwp_path, show=show, pdf=pdf)
        print("완료:", hwp_path)
        print("크기:", os.path.getsize(hwp_path), "bytes")
    except Exception:
        print("변환 실패")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
