# ── pdf_generator.py ─────────────────────────────────────────────────────
# Genera el informe PDF a partir de los datos ya extraídos
# ─────────────────────────────────────────────────────────────────────────
import math, io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import Image as RLImage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

NAVY  = colors.HexColor('#1A2744')
NAVY2 = colors.HexColor('#2A3F6F')
BLUE  = colors.HexColor('#2E5FE8')
GOLD  = colors.HexColor('#C8A84B')
GREEN = colors.HexColor('#16A34A')
RED   = colors.HexColor('#DC2626')
LGRAY = colors.HexColor('#F2F4F8')
MGRAY = colors.HexColor('#D1D5E0')
DGRAY = colors.HexColor('#8892A4')
WHITE = colors.white
PALETTE = ['#2E5FE8','#1A2744','#C8A84B','#16A34A','#DC2626',
           '#7C3AED','#0369A1','#0F766E','#C2410C','#4338CA']

def fmt(n, dec=0):
    if n is None: return "-"
    s = f"{abs(n):,.{dec}f}"
    return f"({s})" if n < 0 else s

def fmtpct(n):
    if n is None: return "-"
    return f"+{n*100:.1f}%" if n >= 0 else f"{n*100:.1f}%"

def fmtpct2(n):
    if n is None: return "-"
    return f"+{n:.1f}%" if n >= 0 else f"{n:.1f}%"

def fig_to_rl(fig, w_mm, h_mm):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=160, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    buf.seek(0)
    return RLImage(buf, width=w_mm*mm, height=h_mm*mm)

def S(name, **kw):
    bases = {
        'hdr1': dict(fontName='Helvetica-Bold', fontSize=15, textColor=WHITE,  alignment=TA_LEFT),
        'hdr2': dict(fontName='Helvetica-Bold', fontSize=9,  textColor=WHITE,  alignment=TA_CENTER),
        'hdr3': dict(fontName='Helvetica-Bold', fontSize=8,  textColor=NAVY,   alignment=TA_LEFT, spaceBefore=4, spaceAfter=2),
        'body': dict(fontName='Helvetica',      fontSize=8,  textColor=colors.black, alignment=TA_LEFT, leading=11),
        'small':dict(fontName='Helvetica',      fontSize=7,  textColor=DGRAY,  alignment=TA_LEFT, leading=9),
        'lbl':  dict(fontName='Helvetica',      fontSize=7,  textColor=DGRAY,  alignment=TA_LEFT),
        'th':   dict(fontName='Helvetica-Bold', fontSize=7.5,textColor=WHITE,  alignment=TA_CENTER),
        'td':   dict(fontName='Helvetica',      fontSize=7.5,textColor=colors.black, alignment=TA_RIGHT),
        'td_l': dict(fontName='Helvetica',      fontSize=7.5,textColor=colors.black, alignment=TA_LEFT),
        'td_b': dict(fontName='Helvetica-Bold', fontSize=7.5,textColor=NAVY,   alignment=TA_LEFT),
        'note': dict(fontName='Helvetica-Oblique', fontSize=6.5, textColor=DGRAY, alignment=TA_LEFT, leading=9),
    }
    b = bases[name].copy(); b.update(kw)
    return ParagraphStyle(name + str(hash(str(kw))), **b)

def p(text, sname, **kw):
    return Paragraph(str(text), S(sname, **kw))

def sec_hdr(title, cw):
    t = Table([[p(title, 'hdr2')]], colWidths=[cw])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), NAVY),
        ('TOPPADDING', (0,0),(-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
    ]))
    return t

# ── CHARTS ────────────────────────────────────────────────────────────────
def chart_patrimonio(years_dict, display_keys, w_mm, h_mm):
    vals = [years_dict[y]['vf']/1000 for y in display_keys]
    x = np.arange(len(display_keys))
    fig, ax = plt.subplots(figsize=(w_mm/25.4, h_mm/25.4))
    ax.bar(x, vals, color='#2E5FE8', zorder=3, width=0.55)
    ax.set_xticks(x); ax.set_xticklabels([str(y) for y in display_keys], fontsize=7)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'U$S {v:.0f}k'))
    ax.yaxis.set_tick_params(labelsize=7)
    ax.grid(axis='y', linestyle='--', alpha=0.35, zorder=0)
    ax.set_axisbelow(True); ax.spines[['top','right']].set_visible(False)
    ax.set_title('Valor de la cartera', fontsize=8, fontweight='bold', pad=4)
    fig.tight_layout(pad=0.5)
    return fig_to_rl(fig, w_mm, h_mm)

def chart_flujos(years_dict, display_keys, w_mm, h_mm):
    deps = [years_dict[y]['dep']/1000 for y in display_keys]
    rets = [-years_dict[y]['ret']/1000 for y in display_keys]
    x = np.arange(len(display_keys))
    fig, ax = plt.subplots(figsize=(w_mm/25.4, h_mm/25.4))
    ax.bar(x, deps, color='#2E5FE8', label='Depósitos', zorder=3, width=0.4)
    ax.bar(x, rets, color='#DC2626', label='Retiros',   zorder=3, width=0.4)
    ax.set_xticks(x); ax.set_xticklabels([str(y) for y in display_keys], fontsize=7)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}k'))
    ax.yaxis.set_tick_params(labelsize=7)
    ax.axhline(0, color='#888', linewidth=0.5)
    ax.grid(axis='y', linestyle='--', alpha=0.35, zorder=0)
    ax.set_axisbelow(True); ax.spines[['top','right']].set_visible(False)
    ax.legend(fontsize=7, framealpha=0.7, loc='lower left')
    ax.set_title('Flujos de cartera', fontsize=8, fontweight='bold', pad=4)
    fig.tight_layout(pad=0.5)
    return fig_to_rl(fig, w_mm, h_mm)

def chart_retornos(years_dict, display_keys, w_mm, h_mm):
    rets = [years_dict[y]['r']*100 for y in display_keys]
    cols = ['#16A34A' if r >= 0 else '#DC2626' for r in rets]
    x = np.arange(len(display_keys))
    fig, ax = plt.subplots(figsize=(w_mm/25.4, h_mm/25.4))
    ax.bar(x, rets, color=cols, zorder=3, width=0.55)
    ax.axhline(0, color='#888', linewidth=0.7)
    ax.set_xticks(x); ax.set_xticklabels([str(y) for y in display_keys], fontsize=7)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v,_: f'{v:.0f}%'))
    ax.yaxis.set_tick_params(labelsize=7)
    ax.grid(axis='y', linestyle='--', alpha=0.35, zorder=0)
    ax.set_axisbelow(True); ax.spines[['top','right']].set_visible(False)
    ax.set_title('Rentabilidad', fontsize=8, fontweight='bold', pad=4)
    fig.tight_layout(pad=0.5)
    return fig_to_rl(fig, w_mm, h_mm)

def chart_donut(data_dict, w_mm, h_mm):
    sorted_d = sorted(data_dict.items(), key=lambda x: -x[1])
    labels = [k for k,_ in sorted_d]
    vals   = [v for _,v in sorted_d]
    total  = sum(vals)
    if total == 0: return None
    fig, ax = plt.subplots(figsize=(w_mm/25.4, h_mm/25.4))
    wedges, _ = ax.pie(vals, colors=PALETTE[:len(vals)], startangle=90,
                       wedgeprops={'width':0.52,'linewidth':0.5,'edgecolor':'white'})
    legend_labels = [f'{l}  {v/total*100:.1f}%' for l,v in zip(labels,vals)]
    ax.legend(wedges, legend_labels, loc='center left',
              bbox_to_anchor=(0.88, 0.5), fontsize=6.5,
              framealpha=0, handlelength=1.0, handleheight=0.9)
    fig.tight_layout(pad=0.2)
    return fig_to_rl(fig, w_mm, h_mm)

def consolidate_positions(raw_by_custodian):
    consolidated = {}
    for custodian, positions in raw_by_custodian.items():
        for pos in positions:
            sym = pos['symbol']
            if sym not in consolidated:
                consolidated[sym] = {
                    'desc': pos['description'], 'stype': pos['secType'],
                    'acat': pos.get('assetCategory',''), 'geo': pos.get('geo','Global'),
                    'sector': pos.get('sector',''), 'price_mkt': pos['price'],
                    'qty': 0, 'mv': 0, 'cost': 0, 'custodians': []
                }
            consolidated[sym]['qty']  += pos['quantity']
            consolidated[sym]['mv']   += pos['marketValue']
            consolidated[sym]['cost'] += pos['costBasis']
            if custodian not in consolidated[sym]['custodians']:
                consolidated[sym]['custodians'].append(custodian)

    result = []
    for sym, d in consolidated.items():
        gl = d['mv'] - d['cost']
        glpct = gl / d['cost'] * 100 if d['cost'] else None
        result.append({
            'symbol': sym, 'desc': d['desc'], 'stype': d['stype'],
            'acat': d['acat'], 'geo': d['geo'], 'sector': d['sector'],
            'qty': d['qty'], 'price_mkt': d['price_mkt'],
            'mv': d['mv'], 'cost': d['cost'], 'gl': gl, 'glpct': glpct,
            'custodians': d['custodians']
        })
    return result

def generate_pdf(client_name, report_date, history_all, positions_by_custodian):
    """
    client_name: str
    report_date: str  e.g. "14.05.2026"
    history_all: dict  {year_key: {vi, dep, ret, vf, res, r}}
    positions_by_custodian: dict  {'pershing': [...], 'ibkr': [...], 'stonex': [...]}
    Returns: bytes (PDF content)
    """
    buf = io.BytesIO()
    W, H = landscape(A4)
    ML = 14*mm; MR = 14*mm
    CW = W - ML - MR

    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=ML, rightMargin=MR,
                            topMargin=12*mm, bottomMargin=12*mm)
    story = []

    # ── Compute derived data ──────────────────────────────────────────
    all_keys     = sorted(history_all.keys(), key=str)
    display_keys = all_keys[-5:]  # last 5 periods

    total_dep  = sum(v['dep'] for v in history_all.values())
    total_ret  = sum(v['ret'] for v in history_all.values())
    latest_val = history_all[all_keys[-1]]['vf']
    total_res  = sum(v['res'] for v in history_all.values())

    # Cumulative return: chain last 5 annual returns (exclude YTD from chain if present)
    chain_keys = [k for k in all_keys if 'YTD' not in str(k)]
    cumul_ret  = math.prod([(1 + history_all[y]['r']) for y in chain_keys]) - 1

    positions = consolidate_positions(positions_by_custodian)
    total_mkt  = sum(p['mv']   for p in positions)
    total_gl   = sum(p['gl']   for p in positions)
    total_cost = sum(p['cost'] for p in positions)

    # ── HEADER ───────────────────────────────────────────────────────
    hdr = Table([[
        p(f'<b>{client_name.upper()}</b>', 'hdr1'),
        p(f'Informe al {report_date}, en U$S', 'body',
          textColor=WHITE, alignment=TA_RIGHT, fontSize=8)
    ]], colWidths=[CW*0.6, CW*0.4])
    hdr.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), NAVY),
        ('TOPPADDING',    (0,0),(-1,-1), 9),
        ('BOTTOMPADDING', (0,0),(-1,-1), 9),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('RIGHTPADDING',  (0,0),(-1,-1), 10),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 4*mm))

    # ── RENTABILIDAD SECTION ──────────────────────────────────────────
    story.append(sec_hdr('Rentabilidad', CW))
    story.append(Spacer(1, 3*mm))

    LW  = CW * 0.20
    CHW = (CW - LW) / 3

    img_patr = chart_patrimonio(history_all, display_keys, CHW/mm, 52)
    img_fluj = chart_flujos(history_all,    display_keys, CHW/mm, 52)
    img_rets = chart_retornos(history_all,  display_keys, CHW/mm, 52)

    net_transfers = total_dep - total_ret
    left_rows = [
        [p('Transferencias netas',     'lbl'), p(f'U$S {fmt(net_transfers)}', 'body', alignment=TA_RIGHT)],
        [p('Valor al final del período','lbl'), p(f'U$S {fmt(latest_val)}',   'body', alignment=TA_RIGHT)],
        [p('Resultado',                'lbl'), p(f'U$S {fmt(total_res)}',     'body', alignment=TA_RIGHT,
           textColor=GREEN if total_res>=0 else RED)],
    ]
    left_t = Table(left_rows, colWidths=[LW*0.58, LW*0.42])
    left_t.setStyle(TableStyle([
        ('TOPPADDING',    (0,0),(-1,-1), 2),
        ('BOTTOMPADDING', (0,0),(-1,-1), 2),
        ('LINEBELOW',     (0,-1),(-1,-1), 0.4, MGRAY),
    ]))

    ret_col = '#16A34A' if cumul_ret>=0 else '#DC2626'
    ret_box = Table([[
        p('Retorno acumulado:', 'lbl', fontSize=7),
        p(f'<b><font color="{ret_col}">{fmtpct(cumul_ret)}</font></b>',
          'body', fontSize=8, alignment=TA_RIGHT),
    ]], colWidths=[LW*0.60, LW*0.40])
    ret_box.setStyle(TableStyle([
        ('TOPPADDING',    (0,0),(-1,-1), 2),
        ('BOTTOMPADDING', (0,0),(-1,-1), 2),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
        ('LINEABOVE',     (0,0),(-1,0),  0.4, MGRAY),
    ]))

    left_panel = Table([[left_t],[ret_box]], colWidths=[LW])
    left_panel.setStyle(TableStyle([
        ('TOPPADDING',    (0,0),(-1,-1), 0),
        ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ('LEFTPADDING',   (0,0),(-1,-1), 0),
        ('RIGHTPADDING',  (0,0),(-1,-1), 0),
    ]))

    charts_row = Table([[left_panel, img_patr, img_fluj, img_rets]],
                       colWidths=[LW, CHW, CHW, CHW])
    charts_row.setStyle(TableStyle([
        ('VALIGN',       (0,0),(-1,-1), 'TOP'),
        ('LEFTPADDING',  (0,0),(-1,-1), 2),
        ('RIGHTPADDING', (0,0),(-1,-1), 2),
        ('TOPPADDING',   (0,0),(-1,-1), 0),
        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
    ]))
    story.append(charts_row)
    story.append(Spacer(1, 4*mm))

    # ── HISTÓRICO ────────────────────────────────────────────────────
    story.append(p('Histórico — Últimos 5 períodos', 'hdr3'))
    th = [p('', 'th')] + [p(str(y), 'th') for y in display_keys]
    defs = [
        ('Valor al inicio del período', lambda y: f'U$S {fmt(history_all[y]["vi"])}'),
        ('Depósitos',                   lambda y: f'U$S {fmt(history_all[y]["dep"])}' if history_all[y]["dep"] else '-'),
        ('Retiros',                     lambda y: f'U$S {fmt(history_all[y]["ret"])}' if history_all[y]["ret"] else '-'),
        ('Valor ajustado',              lambda y: f'U$S {fmt(history_all[y]["vi"]+history_all[y]["dep"]*0.5-history_all[y]["ret"]*0.5)}'),
        ('Valor al final del período',  lambda y: f'U$S {fmt(history_all[y]["vf"])}'),
        ('Resultado',                   lambda y: f'U$S {fmt(history_all[y]["res"])}'),
        ('Rentabilidad del período',    lambda y: fmtpct(history_all[y]["r"])),
    ]
    hist_data = [th]
    for label, fn in defs:
        is_ret = 'Rentabilidad' in label
        row = [p(label, 'td_l', fontSize=7.5)]
        for y in display_keys:
            val = fn(y)
            if is_ret:
                r = history_all[y]['r']
                col = '#16A34A' if r >= 0 else '#DC2626'
                row.append(p(f'<b><font color="{col}">{val}</font></b>', 'td', fontSize=8))
            else:
                row.append(p(val, 'td'))
        hist_data.append(row)

    c0w = CW * 0.26
    cyw = (CW - c0w) / len(display_keys)
    hist_t = Table(hist_data, colWidths=[c0w] + [cyw]*len(display_keys))
    hist_t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0),  NAVY),
        ('BACKGROUND',    (0,-1),(-1,-1),LGRAY),
        ('ROWBACKGROUNDS',(0,1),(-1,-2), [WHITE, LGRAY]),
        ('GRID',          (0,0),(-1,-1), 0.3, MGRAY),
        ('TOPPADDING',    (0,0),(-1,-1), 3),
        ('BOTTOMPADDING', (0,0),(-1,-1), 3),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
        ('RIGHTPADDING',  (0,0),(-1,-1), 5),
        ('LINEBELOW',     (0,-2),(-1,-2), 0.8, NAVY),
    ]))
    story.append(hist_t)
    story.append(p('* MWR (Money Weight Return). Flujos ponderados a mitad del período analizado.', 'note'))
    story.append(Spacer(1, 4*mm))

    # ── POSICIONES ───────────────────────────────────────────────────
    story.append(sec_hdr(f'Posiciones de la cartera al {report_date}', CW))
    story.append(Spacer(1, 2*mm))

    pos_th = [p(h, 'th') for h in ['Instrumento','Tipo','Cantidad','Precio Costo',
                                     'Precio Actual','Cost Basis','Valor Mercado',
                                     '% Cartera','G/P No Real.','G/P %']]
    pos_data = [pos_th]

    groups = {}
    for pos in positions:
        groups.setdefault(pos['acat'] or pos['stype'], []).append(pos)

    cat_order = ['Renta Variable','Renta Fija','Alternativo','Fondos','Efectivo']
    ordered   = [c for c in cat_order if c in groups] + [c for c in groups if c not in cat_order]

    cat_idxs = []; sub_idxs = []; ri = 1
    for cat in ordered:
        ct = sum(p['mv']   for p in groups[cat])
        cc = sum(p['cost'] for p in groups[cat])
        cg = sum(p['gl']   for p in groups[cat])
        cgp = cg/cc*100 if cc else None
        pct_cat = ct/total_mkt*100 if total_mkt else 0
        cat_idxs.append(ri)
        pos_data.append([p(f'<b>{cat}</b>', 'td_b')] + [p('','td')]*9)
        ri += 1
        for pos in sorted(groups[cat], key=lambda x: -x['mv']):
            price_cost = pos['cost']/pos['qty'] if pos['qty'] else 0
            pct = pos['mv']/total_mkt*100 if total_mkt else 0
            gc  = '#16A34A' if pos['gl']>=0 else '#DC2626'
            gps = fmtpct2(pos['glpct']) if pos['glpct'] is not None else '-'
            cus_tag = '+'.join(c.upper()[:3] for c in pos.get('custodians',[])) if len(pos.get('custodians',[])) > 1 else ''
            sym_txt = f'<b>{pos["symbol"]}</b>' + (f' <font size="6" color="#C8A84B">{cus_tag}</font>' if cus_tag else '')
            pos_data.append([
                p(f'{sym_txt}<br/><font size="6.5" color="#8892A4">{pos["desc"][:30]}</font>', 'td_l'),
                p(pos['stype'][:12], 'small', alignment=TA_LEFT),
                p(fmt(pos['qty']), 'td'),
                p(fmt(price_cost, 2), 'td'),
                p(fmt(pos['price_mkt'], 2), 'td'),
                p(f'U$S {fmt(pos["cost"])}', 'td'),
                p(f'U$S {fmt(pos["mv"])}', 'td'),
                p(f'{pct:.1f}%', 'td'),
                p(f'<font color="{gc}">U$S {fmt(pos["gl"])}</font>', 'td'),
                p(f'<font color="{gc}">{gps}</font>', 'td'),
            ])
            ri += 1
        gc_c  = '#16A34A' if cg>=0 else '#DC2626'
        gps_c = fmtpct2(cgp) if cgp is not None else '-'
        sub_idxs.append(ri)
        pos_data.append([
            p(f'<b>Subtotal {cat}</b>', 'td_b', fontSize=7),
            p('','td'), p('','td'), p('','td'), p('','td'),
            p(f'<b>U$S {fmt(cc)}</b>', 'td', fontName='Helvetica-Bold', textColor=NAVY),
            p(f'<b>U$S {fmt(ct)}</b>', 'td', fontName='Helvetica-Bold', textColor=NAVY),
            p(f'<b>{pct_cat:.1f}%</b>', 'td', fontName='Helvetica-Bold', textColor=NAVY),
            p(f'<b><font color="{gc_c}">U$S {fmt(cg)}</font></b>', 'td'),
            p(f'<b><font color="{gc_c}">{gps_c}</font></b>', 'td'),
        ])
        ri += 1

    gc_t   = '#16A34A' if total_gl>=0 else '#DC2626'
    tglpct = total_gl/total_cost*100 if total_cost else None
    pos_data.append([
        p('<b>TOTAL</b>', 'td_b'),
        p('','td'), p('','td'), p('','td'), p('','td'),
        p(f'<b>U$S {fmt(total_cost)}</b>', 'td', fontName='Helvetica-Bold', textColor=NAVY),
        p(f'<b>U$S {fmt(total_mkt)}</b>',  'td', fontName='Helvetica-Bold', textColor=NAVY),
        p('<b>100.0%</b>', 'td', fontName='Helvetica-Bold'),
        p(f'<font color="{gc_t}"><b>U$S {fmt(total_gl)}</b></font>', 'td'),
        p(f'<font color="{gc_t}"><b>{fmtpct2(tglpct)}</b></font>', 'td'),
    ])

    cw_pos = [CW*0.17, CW*0.07, CW*0.055, CW*0.065, CW*0.065,
              CW*0.09, CW*0.10, CW*0.065, CW*0.115, CW*0.065]
    pos_t = Table(pos_data, colWidths=cw_pos, repeatRows=1)
    pts = [
        ('BACKGROUND',    (0,0),(-1,0),  NAVY),
        ('BACKGROUND',    (0,-1),(-1,-1),NAVY),
        ('ROWBACKGROUNDS',(0,1),(-1,-2), [WHITE, LGRAY]),
        ('GRID',          (0,0),(-1,-1), 0.3, MGRAY),
        ('TOPPADDING',    (0,0),(-1,-1), 2),
        ('BOTTOMPADDING', (0,0),(-1,-1), 2),
        ('LEFTPADDING',   (0,0),(-1,-1), 4),
        ('RIGHTPADDING',  (0,0),(-1,-1), 4),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]
    for cr in cat_idxs:
        pts += [('BACKGROUND',(0,cr),(-1,cr), colors.HexColor('#EEF2FB')),
                ('LINEABOVE', (0,cr),(-1,cr), 0.8, NAVY2)]
    for sr in sub_idxs:
        pts += [('BACKGROUND',(0,sr),(-1,sr), colors.HexColor('#DDE4F5')),
                ('LINEABOVE', (0,sr),(-1,sr), 0.5, MGRAY),
                ('LINEBELOW', (0,sr),(-1,sr), 0.8, NAVY2)]
    pos_t.setStyle(TableStyle(pts))
    story.append(pos_t)
    story.append(Spacer(1, 4*mm))

    # ── ANÁLISIS ────────────────────────────────────────────────────
    story.append(sec_hdr('Análisis de la Cartera', CW))
    story.append(Spacer(1, 3*mm))

    by_sector = {}; by_geo = {}; by_asset = {}
    for pos in positions:
        mv = pos['mv']
        by_sector[pos['sector'] or 'Otro'] = by_sector.get(pos['sector'] or 'Otro', 0) + mv
        by_geo[pos['geo']    or 'Global']  = by_geo.get(pos['geo'] or 'Global', 0)    + mv
        by_asset[pos['acat'] or 'Otro']    = by_asset.get(pos['acat'] or 'Otro', 0)   + mv

    dw = CW/3 - 4*mm; dh = 60
    img_sec = chart_donut(by_sector, dw/mm, dh)
    img_geo = chart_donut(by_geo,    dw/mm, dh)
    img_ast = chart_donut(by_asset,  dw/mm, dh)

    an_row = Table([[
        Table([[p('Por Sector',         'hdr3')],[img_sec or Spacer(1,dh*mm)]], colWidths=[dw]),
        Table([[p('Por Geografía',      'hdr3')],[img_geo or Spacer(1,dh*mm)]], colWidths=[dw]),
        Table([[p('Por Tipo de Activo', 'hdr3')],[img_ast or Spacer(1,dh*mm)]], colWidths=[dw]),
    ]], colWidths=[CW/3]*3)
    an_row.setStyle(TableStyle([
        ('VALIGN',       (0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',  (0,0),(-1,-1), 2),
        ('RIGHTPADDING', (0,0),(-1,-1), 2),
        ('TOPPADDING',   (0,0),(-1,-1), 0),
        ('BOTTOMPADDING',(0,0),(-1,-1), 0),
    ]))
    story.append(an_row)

    # ── FOOTER ──────────────────────────────────────────────────────
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width=CW, thickness=0.4, color=MGRAY))
    story.append(Spacer(1, 2*mm))
    story.append(p(
        '* Retorno acumulado calculado encadenando retornos anuales MWR. '
        'Retorno anual/YTD según MWR (Money Weight Return), flujos ponderados a mitad del período. '
        'Informe de carácter informativo, no constituye asesoramiento de inversión. — West Side Consultants',
        'note'))

    doc.build(story)
    buf.seek(0)
    return buf.read()
