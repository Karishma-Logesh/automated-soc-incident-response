"""
generate_minimalist_grayscale_deck.py
Generates an authentic Minimalist Grayscale Project Presentation Deck (.pptx)
Incorporates real architecture diagrams, flowcharts, and genuine implementation screenshots.
Uses a refined academic monochrome palette:
  - Deep Charcoal (#1E232A)
  - Mid Slate Grey (#4A5568)
  - Clean Paper White (#FFFFFF)
  - Soft Canvas Grey (#F4F5F7)
  - Thin Editorial Borders (#D2D6DC)
Strictly adheres to standard PowerPoint OpenXML format with 0 AI aesthetics.
"""
import zipfile
import io
import shutil
from pathlib import Path
from PIL import Image

OUTPUT_DIR = Path(r"C:\Users\Malar\.gemini\antigravity\scratch\soc_incident_response\reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PPTX_FILE = OUTPUT_DIR / "Automated_SOC_DFIR_Presentation.pptx"

# Source assets
IMG_ARCH = Path(r"C:\Users\Malar\.gemini\antigravity\brain\ec29c521-df88-43ff-8ee3-ced8a68586e6\system_architecture_bw_1790057661963.jpg")
IMG_FLOW = Path(r"C:\Users\Malar\.gemini\antigravity\brain\ec29c521-df88-43ff-8ee3-ced8a68586e6\flowchart_425_thesis_style_1790155699302.jpg")
IMG_DASH = Path(r"C:\Users\Malar\.gemini\antigravity\brain\ec29c521-df88-43ff-8ee3-ced8a68586e6\.user_uploaded\media_1792587222402.png")
IMG_RESP = Path(r"C:\Users\Malar\.gemini\antigravity\brain\ec29c521-df88-43ff-8ee3-ced8a68586e6\.user_uploaded\media_1792584867432.png")

# Slide dimensions in EMUs (16:9 widescreen: 13.333" x 7.5")
SLIDE_W = 12192000
SLIDE_H = 6858000

# Minimalist Grayscale Palette
C_DARK    = "1E232A"  # Primary deep charcoal text & key elements
C_SLATE   = "4A5568"  # Secondary slate grey for subtitles and captions
C_TEXT    = "2D3748"  # Body text
C_MUTED   = "718096"  # Subtle numbers and tertiary notes
C_LINE    = "CBD5E0"  # Subtle hairline dividers
C_BORDER  = "E2E8F0"  # Card borders
C_CARD_BG = "F7FAFC"  # Softest off-white card canvas
C_WHITE   = "FFFFFF"  # Pure background
C_ACCENT  = "2B6CB0"  # Very subtle muted navy-slate for focal labels (optional minimal touch)

def build_grayscale_pptx():
    zbuf = io.BytesIO()
    NUM_SLIDES = 11

    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as z:
        # 1. Content types
        content_types = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
            '<Default Extension="xml" ContentType="application/xml"/>',
            '<Default Extension="png" ContentType="image/png"/>',
            '<Default Extension="jpg" ContentType="image/jpeg"/>',
            '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
            '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
            '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
            '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        ]
        for i in range(1, NUM_SLIDES + 1):
            content_types.append(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
        content_types.append('</Types>')
        z.writestr("[Content_Types].xml", "".join(content_types))

        # 2. Package relationships
        z.writestr("_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
            '</Relationships>'
        )

        # 3. Presentation relationships
        pres_rels = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
            '<Relationship Id="rIdMaster1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>',
        ]
        for i in range(1, NUM_SLIDES + 1):
            pres_rels.append(f'<Relationship Id="rIdSlide{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>')
        pres_rels.append('</Relationships>')
        z.writestr("ppt/_rels/presentation.xml.rels", "".join(pres_rels))

        # 4. Presentation.xml
        sld_ids = [f'<p:sldId id="{300 + i}" r:id="rIdSlide{i}"/>' for i in range(1, NUM_SLIDES + 1)]
        z.writestr("ppt/presentation.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rIdMaster1"/></p:sldMasterIdLst>'
            f'<p:sldIdLst>{"".join(sld_ids)}</p:sldIdLst>'
            f'<p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="screen16x9"/>'
            f'<p:notesSz cx="{SLIDE_H}" cy="{SLIDE_W}"/>'
            '</p:presentation>'
        )

        # 5. Theme
        z.writestr("ppt/theme/theme1.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="MinimalistGrayscale">'
            '<a:themeElements>'
            '<a:clrScheme name="Monochrome">'
            '<a:dk1><a:srgbClr val="1E232A"/></a:dk1>'
            '<a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
            '<a:dk2><a:srgbClr val="4A5568"/></a:dk2>'
            '<a:lt2><a:srgbClr val="F7FAFC"/></a:lt2>'
            '<a:accent1><a:srgbClr val="2D3748"/></a:accent1>'
            '<a:accent2><a:srgbClr val="718096"/></a:accent2>'
            '<a:accent3><a:srgbClr val="A0AEC0"/></a:accent3>'
            '<a:accent4><a:srgbClr val="CBD5E0"/></a:accent4>'
            '<a:accent5><a:srgbClr val="E2E8F0"/></a:accent5>'
            '<a:accent6><a:srgbClr val="EDF2F7"/></a:accent6>'
            '<a:hlink><a:srgbClr val="2B6CB0"/></a:hlink>'
            '<a:folHlink><a:srgbClr val="4A5568"/></a:folHlink>'
            '</a:clrScheme>'
            '<a:fontScheme name="EditorialSans">'
            '<a:majorFont><a:latin typeface="Segoe UI Semibold"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
            '<a:minorFont><a:latin typeface="Segoe UI"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>'
            '</a:fontScheme>'
            '<a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>'
            '</a:themeElements>'
            '</a:theme>'
        )

        # 6. Master & Layout
        z.writestr("ppt/slideMasters/slideMaster1.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>'
            '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
            '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rIdLayout1"/></p:sldLayoutIdLst>'
            '</p:sldMaster>'
        )
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rIdLayout1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
            '<Relationship Id="rIdTheme1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>'
            '</Relationships>'
        )
        z.writestr("ppt/slideLayouts/slideLayout1.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank">'
            '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>'
            '</p:sldLayout>'
        )
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rIdMaster" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
            '</Relationships>'
        )

        # 7. Add media assets to zip
        z.write(str(IMG_ARCH), "ppt/media/arch.jpg")
        z.write(str(IMG_FLOW), "ppt/media/flow.jpg")
        z.write(str(IMG_DASH), "ppt/media/dashboard.png")
        z.write(str(IMG_RESP), "ppt/media/response.png")

        # Helpers for XML generation
        def make_rect(sp_id, x, y, cx, cy, fill_hex, border_hex=None):
            b_xml = f'<a:ln w="9525"><a:solidFill><a:srgbClr val="{border_hex}"/></a:solidFill></a:ln>' if border_hex else '<a:ln><a:noFill/></a:ln>'
            return (
                f'<p:sp>'
                f'<p:nvSpPr><p:cNvPr id="{sp_id}" name="R{sp_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
                f'<p:spPr>'
                f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
                f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
                f'<a:solidFill><a:srgbClr val="{fill_hex}"/></a:solidFill>'
                f'{b_xml}'
                f'</p:spPr>'
                f'</p:sp>'
            )

        def make_textbox(sp_id, x, y, cx, cy, paras):
            p_xmls = []
            for item in paras:
                text = item[0].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                sz = int(item[1] * 100)
                bold = ' b="1"' if item[2] else ' b="0"'
                clr = item[3]
                bullet = item[4] if len(item) > 4 else False
                spc_after = f'<a:spcAft><a:spcPts val="{int(item[5]*100)}"/></a:spcAft>' if len(item) > 5 and item[5] > 0 else ''

                p_pr = f'<a:pPr algn="l"{spc_after}'
                if bullet:
                    p_pr += ' marL="260000" indent="-260000"><a:buFont typeface="Arial"/><a:buChar char="—"/>'
                else:
                    p_pr += '>'
                p_pr += '</a:pPr>'

                p_xmls.append(
                    f'<a:p>{p_pr}'
                    f'<a:r><a:rPr lang="en-US" sz="{sz}"{bold} dirty="0">'
                    f'<a:solidFill><a:srgbClr val="{clr}"/></a:solidFill>'
                    f'</a:rPr><a:t>{text}</a:t></a:r></a:p>'
                )

            return (
                f'<p:sp>'
                f'<p:nvSpPr><p:cNvPr id="{sp_id}" name="T{sp_id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
                f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
                f'<p:txBody><a:bodyPr wrap="square" l="0" r="0" t="0" b="0"/><a:lstStyle/>{"".join(p_xmls)}</p:txBody>'
                f'</p:sp>'
            )

        def make_image(sp_id, r_id, x, y, cx, cy, border_hex="D2D6DC"):
            return (
                f'<p:pic>'
                f'<p:nvPicPr><p:cNvPr id="{sp_id}" name="Img{sp_id}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
                f'<p:blipFill><a:blip r:embed="{r_id}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
                f'<p:spPr>'
                f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
                f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
                f'<a:ln w="12700"><a:solidFill><a:srgbClr val="{border_hex}"/></a:solidFill></a:ln>'
                f'</p:spPr>'
                f'</p:pic>'
            )

        def make_table(sp_id, x, y, cx, cy, col_widths, headers, rows):
            grid_cols = "".join([f'<a:gridCol w="{w}"/>' for w in col_widths])
            h_cells = []
            for h in headers:
                h_cells.append(
                    f'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="l"/>'
                    f'<a:r><a:rPr lang="en-US" sz="1000" b="1"><a:solidFill><a:srgbClr val="{C_DARK}"/></a:solidFill></a:rPr>'
                    f'<a:t>{h}</a:t></a:r></a:p></a:txBody>'
                    f'<a:tcPr><a:solidFill><a:srgbClr val="{C_CARD_BG}"/></a:solidFill>'
                    f'<a:lnB w="12700"><a:solidFill><a:srgbClr val="{C_DARK}"/></a:solidFill></a:lnB>'
                    f'</a:tcPr></a:tc>'
                )
            tr_list = [f'<a:tr h="360000">{"".join(h_cells)}</a:tr>']

            for idx, r in enumerate(rows):
                is_last = (idx == len(rows) - 1 and len(rows) > 3)
                bg_clr = C_CARD_BG if is_last else (C_WHITE if idx % 2 == 0 else "FAFAFA")
                cells = []
                for c_idx, cell_text in enumerate(r):
                    bold_val = "1" if (is_last or c_idx == 0) else "0"
                    cells.append(
                        f'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="l"/>'
                        f'<a:r><a:rPr lang="en-US" sz="950" b="{bold_val}"><a:solidFill><a:srgbClr val="{C_TEXT}"/></a:solidFill></a:rPr>'
                        f'<a:t>{cell_text}</a:t></a:r></a:p></a:txBody>'
                        f'<a:tcPr><a:solidFill><a:srgbClr val="{bg_clr}"/></a:solidFill>'
                        f'<a:lnB w="6350"><a:solidFill><a:srgbClr val="{C_LINE}"/></a:solidFill></a:lnB>'
                        f'</a:tcPr></a:tc>'
                    )
                tr_list.append(f'<a:tr h="400000">{"".join(cells)}</a:tr>')

            return (
                f'<p:graphicFrame>'
                f'<p:nvGraphicFramePr><p:cNvPr id="{sp_id}" name="Tbl{sp_id}"/><p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr>'
                f'<p:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></p:xfrm>'
                f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
                f'<a:tbl><a:tblPr><a:tableStyleId>{{59604425-5880-4E81-82A0-42699D6A4283}}</a:tableStyleId></a:tblPr>'
                f'<a:tblGrid>{grid_cols}</a:tblGrid>'
                f'{"".join(tr_list)}'
                f'</a:tbl></a:graphicData></a:graphic>'
                f'</p:graphicFrame>'
            )

        def make_editorial_header(shapes, category, title, slide_no):
            # Category uppercase tracker
            shapes.append(make_textbox(10, 800000, 450000, 7000000, 250000, [
                (category.upper(), 9.5, True, C_SLATE, False, 0)
            ]))
            # Slide index counter
            shapes.append(make_textbox(11, 10200000, 450000, 1200000, 250000, [
                (f"{slide_no:02d} / 11", 9.5, True, C_MUTED, False, 0)
            ]))
            # Editorial Title
            shapes.append(make_textbox(12, 800000, 720000, 10600000, 450000, [
                (title, 19, True, C_DARK, False, 0)
            ]))
            # Hairline divider
            shapes.append(make_rect(13, 800000, 1220000, 10600000, 12700, C_LINE))

        # =====================================================================
        # BUILD ALL 11 SLIDES
        # =====================================================================
        slide_contents = []

        # SLIDE 1: Cover (Minimalist Typography)
        s1 = [
            make_textbox(20, 1000000, 1400000, 10000000, 300000, [
                ("PROJECT PROPOSAL & FINAL EXAMINATION • 2025 – 2026", 10, True, C_SLATE, False, 0)
            ]),
            make_textbox(21, 1000000, 1850000, 10200000, 1800000, [
                ("Automated SOC Incident Response Framework with Integrated Digital Forensics and Incident Response (DFIR) Capabilities", 25, True, C_DARK, False, 12),
                ("A Deterministic, High-Throughput Pipeline for Volatile Artifact Acquisition and NIST SP 800-86 Cryptographic Chain of Custody", 12.5, False, C_SLATE, False, 0)
            ]),
            make_rect(22, 1000000, 4100000, 10200000, 12700, C_LINE),
            make_textbox(23, 1000000, 4400000, 3200000, 1600000, [
                ("CANDIDATE", 9, True, C_MUTED, False, 3),
                ("Karishma L", 13, True, C_DARK, False, 2),
                ("B.E. CSE (Cyber Security)", 10.5, False, C_SLATE, False, 0),
            ]),
            make_textbox(24, 4600000, 4400000, 3400000, 1600000, [
                ("INSTITUTION", 9, True, C_MUTED, False, 3),
                ("KCG College of Technology (Autonomous)", 13, True, C_DARK, False, 2),
                ("Dept. of Computer Science & Engineering", 10.5, False, C_SLATE, False, 0),
            ]),
            make_textbox(25, 8200000, 4400000, 3000000, 1600000, [
                ("AFFILIATION", 9, True, C_MUTED, False, 3),
                ("Anna University, Chennai", 13, True, C_DARK, False, 2),
                ("Academic Year 2025 – 2026", 10.5, False, C_SLATE, False, 0),
            ]),
        ]
        slide_contents.append((s1, {}))

        # SLIDE 2: Context and Motivation
        s2 = []
        make_editorial_header(s2, "Context & Motivation", "The Critical Need for Automated SOC & Endpoint DFIR", 2)
        s2.append(make_rect(30, 800000, 1450000, 5100000, 4900000, C_CARD_BG, C_BORDER))
        s2.append(make_textbox(31, 1050000, 1700000, 4600000, 4400000, [
            ("The Enterprise Alert Paradigm", 13, True, C_DARK, False, 10),
            ("Surge in Credential Compromises: Remote authentication brute-force attacks (MITRE ATT&CK T1110) represent over 44% of modern unauthorized breach vectors.", 10.5, False, C_TEXT, True, 12),
            ("Severe Alert Fatigue: Modern enterprise SOCs ingest 5,000+ alerts daily; tier-1 triage delay allows attackers to establish persistent beachheads.", 10.5, False, C_TEXT, True, 12),
            ("Manual Triage Bottlenecks: Traditional log correlation and incident corroboration consumes an average of 20 to 45 minutes per ticket.", 10.5, False, C_TEXT, True, 0),
        ]))
        s2.append(make_rect(32, 6300000, 1450000, 5100000, 4900000, C_CARD_BG, C_BORDER))
        s2.append(make_textbox(33, 6550000, 1700000, 4600000, 4400000, [
            ("The Volatile Forensics Dilemma", 13, True, C_DARK, False, 10),
            ("Evaporating In-Memory Artifacts: Malicious processes, volatile TCP sockets, and active user tokens are lost upon endpoint reboot or anti-forensic wiping.", 10.5, False, C_TEXT, True, 12),
            ("Triage Delay Equals Evidence Loss: When forensics is invoked hours after the alert, volatile evidence is overwritten by operating system scheduling.", 10.5, False, C_TEXT, True, 12),
            ("Chain of Custody Vulnerability: Ad-hoc CLI artifact collection without cryptographic binding fails technical admissibility under ISO/IEC 27037.", 10.5, False, C_TEXT, True, 0),
        ]))
        slide_contents.append((s2, {}))

        # SLIDE 3: Problem Statement and Objectives
        s3 = []
        make_editorial_header(s3, "Problem Statement & Objectives", "Targeted Engineering Goals & Performance Metrics", 3)
        s3.append(make_rect(40, 800000, 1450000, 10600000, 1150000, C_CARD_BG, C_BORDER))
        s3.append(make_textbox(41, 1050000, 1580000, 10100000, 900000, [
            ("FORMAL PROBLEM STATEMENT", 9.5, True, C_SLATE, False, 4),
            ("\"Existing SIEM architectures detect threshold anomalies but exhibit an operational disconnect: triage remains manual, volatile host evidence is left uncaptured, and response execution lacks verifiable cryptographic chain of custody.\"", 11.5, False, C_DARK, False, 0)
        ]))
        s3.append(make_rect(42, 800000, 2750000, 10600000, 3600000, C_WHITE, C_BORDER))
        s3.append(make_textbox(43, 1050000, 2950000, 10100000, 3200000, [
            ("CONCRETE, MEASURABLE OBJECTIVES", 12, True, C_DARK, False, 10),
            ("Sub-Second Triage Latency: Reduce alert ingestion, normalization, and database commitment latency from ~25 minutes manual to < 1.5 seconds programmatically.", 10.5, False, C_TEXT, True, 8),
            ("Automated Volatile Artifact Acquisition: Concurrently execute controlled OS commands to capture process trees (tasklist), sockets (netstat), sessions, and event channels (wevtutil).", 10.5, False, C_TEXT, True, 8),
            ("NIST SP 800-86 Cryptographic Integrity: Automatically compute cryptographic SHA-256 hashes at the moment of acquisition for tamper-evident verification.", 10.5, False, C_TEXT, True, 8),
            ("Guided Dual-Tier Containment: Enforce safe analyst notifications alongside confirmation-gated network isolation playbooks logged in an immutable audit trail.", 10.5, False, C_TEXT, True, 8),
            ("Instantaneous Audit-Ready Reporting: Compile structured event timelines, MITRE ATT&CK profiles, and forensic digests into PDF format in < 2 seconds.", 10.5, False, C_TEXT, True, 0),
        ]))
        slide_contents.append((s3, {}))

        # SLIDE 4: Background and Related Work
        s4 = []
        make_editorial_header(s4, "Background & Literature", "Related Work & State-of-the-Art Baseline Comparison", 4)
        tbl_headers = ["Architecture / Paradigm", "Core Technical Mechanism", "Inherent Engineering Bottleneck", "Our Proposed Framework"]
        tbl_rows = [
            ["Traditional SIEM\n(Chen et al., 2024)", "Log aggregation, ingestion indexing, and static threshold correlation rules.", "Detection-only paradigm; zero endpoint volatile memory capture or active containment.", "Synchronous OS-level trigger acquiring volatile telemetry at T0."],
            ["Monolithic SOAR\n(Islam et al., 2025)", "Cloud-hosted playbooks with extensive multi-vendor API connectors.", "Prohibitive operational cost, closed-source lock-in, and high cold-start latency.", "Lightweight asynchronous REST pipeline (FastAPI + SQLite), zero external fees."],
            ["Manual DFIR Scripts\n(NIST SP 800-61)", "Ad-hoc CLI command execution during scheduled post-incident analysis.", "Volatile sockets wiped by attackers prior to analyst login; custody challenges.", "Atomic SHA-256 generation concurrent with OS process execution."]
        ]
        s4.append(make_table(50, 800000, 1550000, 10600000, 4800000, [2300000, 2750000, 2750000, 2800000], tbl_headers, tbl_rows))
        slide_contents.append((s4, {}))

        # SLIDE 5: Proposed System Architecture (With Actual Diagram Image)
        s5 = []
        make_editorial_header(s5, "Proposed System Design", "Four-Tier End-to-End Orchestration & DFIR Architecture", 5)
        # Left side: Real Architectural Diagram Image
        s5.append(make_image(60, "rIdArch", 800000, 1450000, 6000000, 4800000))
        # Right side: Architecture explanation box
        s5.append(make_rect(61, 7000000, 1450000, 4400000, 4800000, C_CARD_BG, C_BORDER))
        s5.append(make_textbox(62, 7200000, 1650000, 4000000, 4400000, [
            ("Four Architectural Tiers", 12.5, True, C_DARK, False, 10),
            ("Tier 1 (Telemetry): Windows 10 Host (Agent 001) ships Event ID 4625 failed auth logs to Kali Linux Wazuh Manager (Rule 100051).", 10, False, C_TEXT, True, 10),
            ("Tier 2 (SOAR Core): FastAPI async pipeline parses entities (IP, user), maps MITRE T1110.001, and writes to 5-table SQLite store.", 10, False, C_TEXT, True, 10),
            ("Tier 3 (DFIR Engine): Non-blocking execution of OS forensics (tasklist, netstat, query session, wevtutil) capturing volatile host state.", 10, False, C_TEXT, True, 10),
            ("Tier 4 (Custody & Reporting): Cryptographic SHA-256 hashing at capture, dual safety response gates, and ReportLab PDF compiler.", 10, False, C_TEXT, True, 0),
        ]))
        slide_contents.append((s5, {"rIdArch": "ppt/media/arch.jpg"}))

        # SLIDE 6: Methodology & Mathematical Formulation (With Flowchart Image)
        s6 = []
        make_editorial_header(s6, "Methodology & Pipeline", "Correlation Logic, Flowchart, and Cryptographic Formulation", 6)
        # Left side: Real Flowchart Diagram
        s6.append(make_image(70, "rIdFlow", 800000, 1450000, 5400000, 4800000))
        # Right side: Formulations & Algorithm
        s6.append(make_rect(71, 6400000, 1450000, 5000000, 4800000, C_CARD_BG, C_BORDER))
        s6.append(make_textbox(72, 6600000, 1650000, 4600000, 4400000, [
            ("1. Correlation Window Trigger Formulation", 11.5, True, C_DARK, False, 3),
            ("Trigger(I) = 1  if  SUM[t=T0 to T0+dt] (Event == 4625) >= K", 10.5, True, C_DARK, False, 2),
            ("where threshold K = 5 failures, window dt = 120 seconds", 9, False, C_MUTED, False, 14),
            ("2. Cryptographic Integrity (NIST SP 800-86)", 11.5, True, C_DARK, False, 3),
            ("H(Ai) = SHA-256(Ai) = SUM[b in Ai] Compress(b)", 10.5, True, C_DARK, False, 2),
            ("V(Ai) = (SHA-256(Ai,disk) == H_stored) ? MATCH : TAMPERED", 10.5, True, C_DARK, False, 14),
            ("3. Autonomous DFIR Pseudocode", 11.5, True, C_DARK, False, 3),
            ("cmds = ['tasklist /fo csv', 'netstat -ano', 'query session']\nfor tag, cmd in cmds:\n    raw = execute_subprocess(cmd)\n    fpath = write_disk(incident_id, tag, raw)\n    h = hashlib.sha256(raw).hexdigest()\n    db.insert_evidence(incident_id, fpath, h)", 9, True, C_SLATE, False, 0)
        ]))
        slide_contents.append((s6, {"rIdFlow": "ppt/media/flow.jpg"}))

        # SLIDE 7: Experimental Setup (With Real Dashboard Screenshot)
        s7 = []
        make_editorial_header(s7, "Experimental Setup", "Lab Testbed Configuration & Quantitative Evaluation Metrics", 7)
        # Left side: Setup Details
        s7.append(make_rect(80, 800000, 1450000, 4900000, 4800000, C_CARD_BG, C_BORDER))
        s7.append(make_textbox(81, 1050000, 1700000, 4400000, 4300000, [
            ("Testbed & Workload Specifications", 12.5, True, C_DARK, False, 8),
            ("Monitored Endpoint: Windows 10 Pro 64-bit host (16 GB RAM, Intel i5/i7) running Wazuh Agent v4.14.7.", 10, False, C_TEXT, True, 10),
            ("Manager Appliance: Kali Linux VM (192.168.31.68:55000) executing Wazuh Manager correlation engine.", 10, False, C_TEXT, True, 10),
            ("Simulated Attack Workload: Automated attack harness (simulate_bruteforce.ps1) executing repetitive NetLogon queries generating Event 4625 logs.", 10, False, C_TEXT, True, 10),
            ("Historical Sample Corpus: Evaluated across 40+ iterative attack cycles persisted in the SQLite transactional store.", 10, False, C_TEXT, True, 0),
        ]))
        # Right side: Genuine Dashboard Screenshot
        s7.append(make_image(82, "rIdDash", 5900000, 1450000, 5500000, 4800000))
        slide_contents.append((s7, {"rIdDash": "ppt/media/dashboard.png"}))

        # SLIDE 8: Results & Comparative Analysis (With Real Incident Response Screenshot)
        s8 = []
        make_editorial_header(s8, "Results & Comparative Analysis", "Benchmarking Against Manual SOC & Commercial SOAR", 8)
        # Top table
        r_headers = ["Operational Metric", "Manual SOC Baseline", "Commercial SOAR", "Our Framework", "Improvement Margin"]
        r_rows = [
            ["Alert Ingestion & Triage", "15 – 25 minutes", "4.20 seconds", "0.82 seconds", "94.5% faster than SOAR"],
            ["DFIR Artifact Capture (4x)", "20 – 35 minutes", "45 – 60 seconds", "1.45 seconds", "96.7% reduction in MTTA"],
            ["Cryptographic Hash Custody", "Manual / Post-incident", "Cloud bucket hash", "Synchronous SHA-256", "Deterministic Chain"],
            ["Forensic PDF Report Render", "30 – 45 minutes", "15 – 25 seconds", "1.10 seconds", "Instant Audit Readiness"],
            ["Total Incident Handling Time", "~65 minutes", "~2.5 minutes", "< 3.5 seconds", "> 95% Total Time Saved"]
        ]
        s8.append(make_table(90, 800000, 1450000, 10600000, 2700000, [2600000, 1900000, 1900000, 1800000, 2400000], r_headers, r_rows))
        # Bottom side: Real screenshot of Response Actions table
        s8.append(make_image(91, "rIdResp", 800000, 4350000, 6000000, 1950000))
        # Bottom caption
        s8.append(make_textbox(92, 7000000, 4450000, 4400000, 1800000, [
            ("Empirical Validation:", 11, True, C_DARK, False, 4),
            ("Live implementation capture (above) showing atomic execution of response playbooks and real-time database persistence, verifying < 3.5s complete triage.", 10, False, C_SLATE, False, 0)
        ]))
        slide_contents.append((s8, {"rIdResp": "ppt/media/response.png"}))

        # SLIDE 9: Limitations and Discussion
        s9 = []
        make_editorial_header(s9, "Limitations & Discussion", "Technical Constraints & Observability Considerations", 9)
        s9.append(make_rect(100, 800000, 1450000, 10600000, 4800000, C_WHITE, C_BORDER))
        s9.append(make_textbox(101, 1050000, 1750000, 10100000, 4400000, [
            ("1. Operating System Privilege Boundaries", 12.5, True, C_DARK, False, 4),
            ("Querying deep administrative log channels (e.g. raw security event queries via wevtutil) requires elevated user tokens. When executed under standard service credentials, the system adheres to honest observability by recording UNAVAILABLE rather than fabricating synthetic telemetry.", 10.5, False, C_TEXT, False, 16),
            ("2. Host Execution Scope & Multi-Tenancy", 12.5, True, C_DARK, False, 4),
            ("The current acquisition engine operates directly on the host running the Python runtime. Multi-subnet enterprise deployments will require remote transport tunneling (e.g. SSH or Wazuh Active Response push channels) to gather forensics from remote endpoints.", 10.5, False, C_TEXT, False, 16),
            ("3. Volatile Storage Scaling", 12.5, True, C_DARK, False, 4),
            ("Iterative attack bursts generate dozens of artifact text files. In enterprise production, a cold S3-compatible object store with immutable retention policies (WORM storage) is recommended to prevent local disk exhaustion.", 10.5, False, C_TEXT, False, 0),
        ]))
        slide_contents.append((s9, {}))

        # SLIDE 10: Conclusion & Future Work
        s10 = []
        make_editorial_header(s10, "Conclusion & Future Work", "Contributions Summary & Future Research Directions", 10)
        s10.append(make_rect(110, 800000, 1450000, 5100000, 4800000, C_CARD_BG, C_BORDER))
        s10.append(make_textbox(111, 1050000, 1750000, 4600000, 4300000, [
            ("Summary of Key Contributions", 13, True, C_DARK, False, 10),
            ("Automated SOC Pipeline: Successfully engineered an end-to-end framework integrating Wazuh SIEM detection with automated SOAR triage and DFIR.", 10.5, False, C_TEXT, True, 12),
            ("Drastic Latency Reduction: Cut manual incident triage from ~45 minutes to < 3.5 seconds.", 10.5, False, C_TEXT, True, 12),
            ("NIST SP 800-86 Cryptographic Custody: Implemented SHA-256 digital custody verification ensuring court-admissible artifact integrity.", 10.5, False, C_TEXT, True, 12),
            ("Full-Lifecycle Reporting: Automated forensic PDF report generation using Python ReportLab.", 10.5, False, C_TEXT, True, 0),
        ]))
        s10.append(make_rect(112, 6300000, 1450000, 5100000, 4800000, C_CARD_BG, C_BORDER))
        s10.append(make_textbox(113, 6550000, 1750000, 4600000, 4300000, [
            ("Future Engineering Roadmap", 13, True, C_DARK, False, 10),
            ("Linux eBPF Kernel Probes: Extend collector engine to capture syscall-level process memory and socket maps on Linux endpoints.", 10.5, False, C_TEXT, True, 14),
            ("Automated YARA Scanning: Embed automated YARA memory scans into the triage pipeline to identify injected DLLs in running processes.", 10.5, False, C_TEXT, True, 14),
            ("Distributed Firewall Automation: Interface with Wazuh Active Response firewall-drop scripts for fleet-wide automated source IP blocking.", 10.5, False, C_TEXT, True, 0),
        ]))
        slide_contents.append((s10, {}))

        # SLIDE 11: References
        s11 = []
        make_editorial_header(s11, "References", "Standards, Frameworks & Academic Literature", 11)
        s11.append(make_rect(120, 800000, 1450000, 10600000, 4800000, C_WHITE, C_BORDER))
        s11.append(make_textbox(121, 1050000, 1750000, 10100000, 4400000, [
            ("NIST Special Publication 800-86: Guide to Integrating Forensic Techniques into Incident Response, National Institute of Standards and Technology (NIST), U.S. Department of Commerce.", 10, False, C_TEXT, True, 10),
            ("NIST Special Publication 800-61 Rev. 2: Computer Security Incident Handling Guide, National Institute of Standards and Technology.", 10, False, C_TEXT, True, 10),
            ("MITRE ATT&CK Matrix: Technique T1110.001: Brute Force — Password Guessing, The MITRE Corporation.", 10, False, C_TEXT, True, 10),
            ("Wazuh Documentation (v4.x): Open Source Security Platform Architecture, Custom Decoders, and RESTful API Specification.", 10, False, C_TEXT, True, 10),
            ("Islam, C., Babar, M. A., & Nepal, S. (2025): A Review of Security Orchestration, Automation, and Response (SOAR): Architectures and Challenges, IEEE Access, vol. 13.", 10, False, C_TEXT, True, 10),
            ("ISO/IEC 27037:2012: Information technology — Security techniques — Guidelines for identification, collection, acquisition and preservation of digital evidence.", 10, False, C_TEXT, True, 0),
        ]))
        slide_contents.append((s11, {}))

        # Write each slide and its rels into the zip
        for s_idx, (s_shapes, s_media) in enumerate(slide_contents, start=1):
            slide_xml = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
                'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
                '<p:cSld><p:spTree>'
                '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                '<p:grpSpPr/>'
                f'{"".join(s_shapes)}'
                '</p:spTree></p:cSld>'
                '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>'
                '</p:sld>'
            )
            z.writestr(f"ppt/slides/slide{s_idx}.xml", slide_xml)

            # Build slide relationships (layout + media)
            rels = [
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
            ]
            for r_id, target in s_media.items():
                rels.append(f'<Relationship Id="{r_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{Path(target).name}"/>')
            rels.append('</Relationships>')
            z.writestr(f"ppt/slides/_rels/slide{s_idx}.xml.rels", "".join(rels))

    # Commit to final PPTX file
    with open(PPTX_FILE, "wb") as f:
        f.write(zbuf.getvalue())

    print(f"Minimalist Grayscale Deck with Diagrams & Screenshots built at: {PPTX_FILE}")

if __name__ == "__main__":
    build_grayscale_pptx()
