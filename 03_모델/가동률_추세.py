"""삼성바이오로직스 배치 기준 생산능력·생산실적·가동률 (2015~1H26).

입력: 01_공시_IR/가동률_원문/<접수번호>_prod.html
      (DART 각 보고서의 '원재료 및 생산설비' 또는 '사업의 내용' 원문, 2026-11-08 수집)
출력: 03_모델/가동률_2015_2026.csv (누적 원자료), 03_모델/분기별_가동률_2018_2026.csv (분기 환산)
      04_초안/그림/부록_가동률_추세.png
실행: <matplotlib 있는 python> 03_모델/가동률_추세.py
"""
import re, html, glob, os, csv, sys
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, '01_공시_IR', '가동률_원문')

def tables(path):
    h = open(path, encoding='utf-8').read()
    out = []
    for t in re.findall(r'<table.*?</table>', h, re.S | re.I):
        rows = []
        for tr in re.findall(r'<tr.*?</tr>', t, re.S | re.I):
            rows.append([re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', c))).strip()
                         for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S | re.I)])
        out.append(rows)
    return out

def num(s):
    return float(s.replace(',', '').replace('%', '').split('(')[0])

def period(lbl):
    y = int(re.search(r'(20\d\d)', lbl).group(1))
    if '1분기' in lbl: p = 'Q1'
    elif '반기' in lbl: p = 'H1'
    elif '3분기' in lbl: p = '9M'
    else: p = 'FY'
    return y, p

recs = []   # (rcp, year, period, basis, cap, prod, util_reported, is_current_column)
for f in sorted(glob.glob(os.path.join(RAW, '*_prod.html'))):
    rcp = os.path.basename(f)[:14]
    for t in tables(f):
        flat = [c for r in t for c in r]
        if not any('가동률' in c for c in flat):
            continue
        hdr = t[0]
        if '표준생산능력' in hdr:   # 2016~2017 3분기 보고서: 당기 한 열, 공칭(표준) 기준
            # 당기 기간은 보고서 제목이 아닌 접수일로 판단
            y = int(rcp[:4]); m = int(rcp[4:6])
            yp = {3: (y - 1, 'FY'), 5: (y, 'Q1'), 8: (y, 'H1'), 11: (y, '9M')}[m]
            recs.append((rcp, *yp, '공칭', num(t[1][1]), num(t[1][2]), num(t[1][3]), True))
            continue
        labels = hdr[1:]
        rows = {}
        basis = '실효'
        for r in t[1:]:
            if r and r[0] in ('공칭생산능력대비', '실효생산능력대비'):
                basis = r[0][:2]; r = r[1:]
            if r and r[0] in ('생산능력', '생산실적', '가동률'):
                rows.setdefault(basis, {})[r[0]] = r[1:]
        for b, d in rows.items():
            for k, lbl in enumerate(labels):
                y, p = period(lbl)
                recs.append((rcp, y, p, b, num(d['생산능력'][k]), num(d['생산실적'][k]), num(d['가동률'][k]), k == 0))

# 같은 (연도, 기간, 기준)이 여러 보고서에 나오면 값이 같은지 확인 (재작성 여부)
seen = {}
conflicts = []
for r in recs:
    key = (r[1], r[2], r[3])
    v = (r[4], r[5])
    if key in seen and seen[key][0] != v:
        conflicts.append((key, seen[key], (v, r[0])))
    seen.setdefault(key, (v, r[0]))
print('재작성(값 불일치):', conflicts if conflicts else '없음')

# 당기 열 기준 원자료 (실효 우선, 실효 없으면 공칭)
cur = {}
for r in recs:
    key = (r[1], r[2])
    if r[3] == '실효' or key not in cur:
        if key not in cur or cur[key][3] != '실효' or r[7]:
            cur[key] = r
order = {'Q1': 1, 'H1': 2, '9M': 3, 'FY': 4}
rows = sorted(cur.values(), key=lambda r: (r[1], order[r[2]]))
with open(os.path.join(BASE, '03_모델', '가동률_2015_2026.csv'), 'w', newline='', encoding='utf-8-sig') as fo:
    w = csv.writer(fo); w.writerow(['연도', '기간(누적)', '기준', '생산능력(배치)', '생산실적(배치)', '가동률_공시(%)', '가동률_재계산(%)', '출처_접수번호'])
    for r in rows:
        w.writerow([r[1], r[2], r[3], int(r[4]), int(r[5]), r[6], round(r[5] / r[4] * 100, 1), r[0]])
        assert abs(r[5] / r[4] * 100 - r[6]) < 0.06, r   # 공시 가동률 = 실적/능력 검산

# 분기 환산 (누적 차감), 실효 기준이 있는 2018년부터
q = []
for y in range(2018, 2027):
    cum = {p: cur.get((y, p)) for p in ('Q1', 'H1', '9M', 'FY')}
    prev = (0, 0)
    for qi, p in enumerate(('Q1', 'H1', '9M', 'FY'), 1):
        r = cum[p]
        if r is None or r[3] != '실효':
            break
        c, pr = r[4] - prev[0], r[5] - prev[1]
        q.append((y, qi, int(c), int(pr), round(pr / c * 100, 1)))
        prev = (r[4], r[5])
with open(os.path.join(BASE, '03_모델', '분기별_가동률_2018_2026.csv'), 'w', newline='', encoding='utf-8-sig') as fo:
    w = csv.writer(fo); w.writerow(['연도', '분기', '생산능력(배치)', '생산실적(배치)', '가동률(%)'])
    w.writerows(q)
for r in q: print(*r)

# 5공장을 뺀 1~4공장 가동률 추정 [추정]
# 가정: 1~4공장 생산능력 = 2024년 연간 833배치 ÷ 4 (5공장 가동 전 마지막 완전 연도).
#       5공장 생산능력 = 전사 − 1~4공장. 5공장 배치 가동률은 공시 없음 → 10~40% 범위로 둔다.
C14 = 833 / 4
U5 = (0.10, 0.25, 0.40)
est = []
for y, qi, c, pr, u in q:
    if (y, qi) < (2025, 2):
        continue
    c5 = c - C14
    est.append((y, qi, round(c5, 1), *[round((pr - c5 * u5) / C14 * 100, 1) for u5 in U5]))
def agg(keys):
    sel = [r for r in q if (r[0], r[1]) in keys]
    C = sum(r[2] for r in sel); P = sum(r[3] for r in sel); c5 = C - C14 * len(sel)
    return round(c5 / len(sel), 1), [round((P - c5 * u5) / (C14 * len(sel)) * 100, 1) for u5 in U5]
with open(os.path.join(BASE, '03_모델', '1_4공장_가동률_추정.csv'), 'w', newline='', encoding='utf-8-sig') as fo:
    w = csv.writer(fo); w.writerow(['연도', '분기', '5공장 생산능력 추정(배치)', '1~4공장 가동률 (5공장 10%)', '(5공장 25%)', '(5공장 40%)'])
    w.writerows(est)
    for nm, keys in [('2Q25~4Q25', {(2025, 2), (2025, 3), (2025, 4)}), ('1H26', {(2026, 1), (2026, 2)})]:
        c5, us = agg(keys); w.writerow([nm, '합산', c5, *us]); print('추정', nm, '5공장 능력/분기', c5, '1~4공장 가동률', us)
for nm, keys in [('1Q21~3Q22 (4공장 가동 전, 1~3공장)', {(2021, 1), (2021, 2), (2021, 3), (2021, 4), (2022, 1), (2022, 2), (2022, 3)}),
                 ('4Q24~1Q25 (5공장 가동 전, 1~4공장)', {(2024, 4), (2025, 1)})]:
    sel = [r for r in q if (r[0], r[1]) in keys]
    print('기준', nm, round(sum(r[3] for r in sel) / sum(r[2] for r in sel) * 100, 1))

# 그림: 가동률 정의가 같은 2021년 1분기부터만 그린다 (2021 반기보고서부터 산정 기준 변경)
try:
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm
except ImportError:
    sys.exit('matplotlib 없음: 그림 생략')
fm.fontManager.addfont('/System/Library/Fonts/AppleSDGothicNeo.ttc')
plt.rcParams.update({'font.family': 'Apple SD Gothic Neo', 'axes.unicode_minus': False, 'font.size': 9,
                     'axes.spines.top': False, 'axes.spines.right': False})
B = '#2a78d6'; O = '#eb6834'; GR = '#1baf7a'
qp = [r for r in q if (r[0], r[1]) >= (2021, 1)]
lab = [f"{y % 100}.{qi}Q" for y, qi, *_ in qp]; x = list(range(len(qp)))
fig, (ax, bx) = plt.subplots(2, 1, figsize=(7.2, 4.6), dpi=200, sharex=True, gridspec_kw={'height_ratios': [3, 1.6]})
for a in (ax, bx):
    for l in ('22.4Q', '25.2Q'):
        a.axvline(lab.index(l), color=O, lw=0.8, ls='--', zorder=1)
# 기준 띠: 새 공장 가동 직전 구간(1Q21~3Q22 합산 80.5%, 4Q24~1Q25 합산 82.6%)과 분기 최고치(약 85%)를 묶은 범위
ax.fill_between([-0.4, len(x) - 0.6], 80, 85, color=GR, alpha=0.13, lw=0, zorder=1)
ax.text(-0.3, 85.6, '증설 직전 가동률 80~85%', fontsize=7.5, color='#138a60')
ax.plot(x, [r[4] for r in qp], color=B, marker='o', ms=3, lw=1.5, label='전사 가동률 (공시)', zorder=3)
ex = [lab.index(f"{y % 100}.{qi}Q") for y, qi, *_ in est]
ax.fill_between(ex, [r[5] for r in est], [r[3] for r in est], color=O, alpha=0.18, lw=0, zorder=2)
ax.plot(ex, [r[4] for r in est], color=O, marker='s', ms=3, lw=1.3,
        label='1~4공장 가동률 (추정, 5공장 제외)\n음영: 5공장 가동률 가정 10%(위)~40%(아래)', zorder=3)
ax.set_ylim(55, 95); ax.set_ylabel('가동률 (%)')
for name, l in [('4공장', '22.4Q'), ('5공장', '25.2Q')]:
    ax.text(lab.index(l) + 0.2, 92.5, f'{name} 가동', color=O, fontsize=7.5, va='bottom')
ax.grid(axis='y', color='#e1e0d9', lw=0.6); ax.set_axisbelow(True)
ax.legend(frameon=True, facecolor='white', edgecolor='none', framealpha=1, fontsize=7.5, loc='lower left')
bx.bar(x, [r[2] for r in qp], color='#d3e2f5', width=0.75, label='생산능력', zorder=2)
bx.bar(x, [r[3] for r in qp], color='#7fa9e0', width=0.45, label='생산실적', zorder=3)
bx.set_ylabel('배치 / 분기'); bx.legend(frameon=False, fontsize=7.5, loc='upper left', ncol=2)
bx.grid(axis='y', color='#e1e0d9', lw=0.6); bx.set_axisbelow(True)
bx.set_xticks(x[::2]); bx.set_xticklabels(lab[::2], fontsize=7.5)
fig.tight_layout(); fig.savefig(os.path.join(BASE, '04_초안', '그림', '부록_가동률_추세.png')); plt.close(fig)
print('그림 저장')
