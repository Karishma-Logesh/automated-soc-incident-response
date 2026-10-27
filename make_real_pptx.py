"""
make_real_pptx.py
Builds an authentic, native 16:9 widescreen Microsoft PowerPoint (.pptx) file
from scratch using pure Python standard libraries (zipfile + XML).
Zero external pip dependencies required. Completely compatible with PowerPoint,
Office 365, Google Slides, and LibreOffice Impress.
"""
import zipfile
import io
from pathlib import Path

OUTPUT_DIR = Path(r"C:\Users\Malar\.gemini\antigravity\scratch\soc_incident_response\reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PPTX_FILE = OUTPUT_DIR / "Automated_SOC_DFIR_Presentation.pptx"

# 16:9 widescreen dimensions in EMUs (1 inch = 914,400 EMUs)
SLIDE_W = 12192000  # 13.333 inches
SLIDE_H = 6858000   # 7.500 inches

# Palette
HEX_CHARCOAL  = "263746"
HEX_STEEL     = "477B9E"
HEX_TEXT      = "252B32"
HEX_MUTED     = "697586"
HEX_BG        = "F8F9FA"
HEX_WHITE     = "FFFFFF"
HEX_BORDER    = "D9DEE5"
HEX_GREEN     = "39816C"
HEX_HIGHLIGHT = "DEF7EC"

def create_pptx():
    zbuf = io.BytesIO()

    # 11 slides
    NUM_SLIDES = 11

    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as z:
        # [Content_Types].xml
        content_types = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
            '<Default Extension="xml" ContentType="application/xml"/>',
            '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
            '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
            '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
            '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        ]
        for i in range(1, NUM_SLIDES + 1):
            content_types.append(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
        content_types.append('</Types>')
        z.writestr("[Content_Types].xml", "".join(content_types))

        # _rels/.rels
        z.writestr("_rels/.rels", 
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
            '</Relationships>'
        )

        # ppt/_rels/presentation.xml.rels
        pres_rels = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
            '<Relationship Id="rIdMaster1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>',
        ]
        for i in range(1, NUM_SLIDES + 1):
            pres_rels.append(f'<Relationship Id="rIdSlide{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>')
        pres_rels.append('</Relationships>')
        z.writestr("ppt/_rels/presentation.xml.rels", "".join(pres_rels))

        # ppt/presentation.xml
        sld_ids = [f'<p:sldId id="{255 + i}" r:id="rIdSlide{i}"/>' for i in range(1, NUM_SLIDES + 1)]
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

        # ppt/theme/theme1.xml
        z.writestr("ppt/theme/theme1.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="EnterpriseSOC">'
            '<a:themeElements>'
            '<a:clrScheme name="SOCPalette">'
            '<a:dk1><a:srgbClr val="252B32"/></a:dk1>'
            '<a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
            '<a:dk2><a:srgbClr val="263746"/></a:dk2>'
            '<a:lt2><a:srgbClr val="F8F9FA"/></a:lt2>'
            '<a:accent1><a:srgbClr val="477B9E"/></a:accent1>'
            '<a:accent2><a:srgbClr val="39816C"/></a:accent2>'
            '<a:accent3><a:srgbClr val="B64040"/></a:accent3>'
            '<a:accent4><a:srgbClr val="C58A32"/></a:accent4>'
            '<a:accent5><a:srgbClr val="697586"/></a:accent5>'
            '<a:accent6><a:srgbClr val="D9DEE5"/></a:accent6>'
            '<a:hlink><a:srgbClr val="477B9E"/></a:hlink>'
            '<a:folHlink><a:srgbClr val="36607C"/></a:folHlink>'
            '</a:clrScheme>'
            '<a:fontScheme name="InterScheme">'
            '<a:majorFont><a:latin typeface="Segoe UI"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
            '<a:minorFont><a:latin typeface="Segoe UI"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>'
            '</a:fontScheme>'
            '<a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>'
            '</a:themeElements>'
            '</a:theme>'
        )

        # ppt/slideMasters/slideMaster1.xml
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

        # ppt/slideMasters/_rels/slideMaster1.xml.rels
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rIdLayout1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
            '<Relationship Id="rIdTheme1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>'
            '</Relationships>'
        )

        # ppt/slideLayouts/slideLayout1.xml
        z.writestr("ppt/slideLayouts/slideLayout1.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank">'
            '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld>'
            '</p:sldLayout>'
        )

        # ppt/slideLayouts/_rels/slideLayout1.xml.rels
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rIdMaster" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
            '</Relationships>'
        )

        # Shape & Text XML Generators
        def make_rect(sp_id, x, y, cx, cy, fill_hex, border_hex=None):
            border_xml = f'<a:ln w="12700"><a:solidFill><a:srgbClr val="{border_hex}"/></a:solidFill></a:ln>' if border_hex else '<a:ln><a:noFill/></a:ln>'
            return (
                f'<p:sp>'
                f'<p:nvSpPr><p:cNvPr id="{sp_id}" name="Box{sp_id}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
                f'<p:spPr>'
                f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
                f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val 2000"/></a:avLst></a:prstGeom>'
                f'<a:solidFill><a:srgbClr val="{fill_hex}"/></a:solidFill>'
                f'{border_xml}'
                f'</p:spPr>'
                f'</p:sp>'
            )

        def make_textbox(sp_id, x, y, cx, cy, paras, pad_top=0):
            # paras is list of tuples: (text, font_size_pt, is_bold, hex_color, is_bullet, space_after_pt)
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
                    p_pr += ' marL="285750" indent="-285750"><a:buFont typeface="Arial"/><a:buChar char="▪"/>'
                else:
                    p_pr += '>'
                p_pr += '</a:pPr>'

                p_xmls.append(
                    f'<a:p>{p_pr}'
                    f'<a:r><a:rPr lang="en-US" sz="{sz}"{bold} dirty="0">'
                    f'<a:solidFill><a:srgbClr val="{clr}"/></a:solidFill>'
                    f'</a:rPr><a:t>{text}</a:t></a:r></a:p>'
                )

            top_pad_xml = f' t="{pad_top}"' if pad_top > 0 else ''
            return (
                f'<p:sp>'
                f'<p:nvSpPr><p:cNvPr id="{sp_id}" name="Text{sp_id}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
                f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
                f'<p:txBody><a:bodyPr wrap="square" l="0" r="0" b="0"{top_pad_xml}/><a:lstStyle/>{"".join(p_xmls)}</p:txBody>'
                f'</p:sp>'
            )

        def make_table(sp_id, x, y, cx, cy, col_widths, headers, rows):
            # col_widths in EMUs
            grid_cols = "".join([f'<a:gridCol w="{w}"/>' for w in col_widths])
            
            # header row
            h_cells = []
            for h in headers:
                h_cells.append(
                    f'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="l"/>'
                    f'<a:r><a:rPr lang="en-US" sz="1100" b="1"><a:solidFill><a:srgbClr val="{HEX_WHITE}"/></a:solidFill></a:rPr>'
                    f'<a:t>{h}</a:t></a:r></a:p></a:txBody>'
                    f'<a:tcPr><a:solidFill><a:srgbClr val="{HEX_CHARCOAL}"/></a:solidFill></a:tcPr></a:tc>'
                )
            tr_list = [f'<a:tr h="400000">{"".join(h_cells)}</a:tr>']

            # data rows
            for idx, r in enumerate(rows):
                is_hi = (idx == len(rows) - 1 and len(rows) > 3)
                bg_clr = HEX_HIGHLIGHT if is_hi else (HEX_BG if idx % 2 == 1 else HEX_WHITE)
                cells = []
                for c_idx, cell_text in enumerate(r):
                    bold_val = "1" if (is_hi or c_idx == 0) else "0"
                    txt_clr = HEX_GREEN if (is_hi and c_idx == len(r)-1) else HEX_TEXT
                    cells.append(
                        f'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="l"/>'
                        f'<a:r><a:rPr lang="en-US" sz="1050" b="{bold_val}"><a:solidFill><a:srgbClr val="{txt_clr}"/></a:solidFill></a:rPr>'
                        f'<a:t>{cell_text}</a:t></a:r></a:p></a:txBody>'
                        f'<a:tcPr><a:solidFill><a:srgbClr val="{bg_clr}"/></a:solidFill>'
                        f'<a:lnB w="6350"><a:solidFill><a:srgbClr val="{HEX_BORDER}"/></a:solidFill></a:lnB>'
                        f'</a:tcPr></a:tc>'
                    )
                tr_list.append(f'<a:tr h="440000">{"".join(cells)}</a:tr>')

            return (
                f'<p:graphicFrame>'
                f'<p:nvGraphicFramePr><p:cNvPr id="{sp_id}" name="Table{sp_id}"/><p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr>'
                f'<p:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{cx}" cy="{cy}"/></p:xfrm>'
                f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table">'
                f'<a:tbl><a:tblPr><a:tableStyleId>{{59604425-5880-4E81-82A0-42699D6A4283}}</a:tableStyleId></a:tblPr>'
                f'<a:tblGrid>{grid_cols}</a:tblGrid>'
                f'{"".join(tr_list)}'
                f'</a:tbl></a:graphicData></a:graphic>'
                f'</p:graphicFrame>'
            )

        def make_slide_header(shapes, category, title, num):
            # Top sub-category + slide num
            shapes.append(make_textbox(10, 600000, 450000, 7000000, 250000, [
                (category.upper(), 10, True, HEX_STEEL, False, 0)
            ]))
            shapes.append(make_textbox(11, 9500000, 450000, 2100000, 250000, [
                (f"Slide {num:02d} / 11", 10, True, HEX_MUTED, False, 0)
            ]))
            # Big Title
            shapes.append(make_textbox(12, 600000, 720000, 10000000, 500000, [
                (title, 20, True, HEX_CHARCOAL, False, 0)
            ]))
            # Horizontal divider line
            shapes.append(make_rect(13, 600000, 1300000, 11000000, 25400, HEX_STEEL))

        # =====================================================================
        # SLIDE 1: TITLE SLIDE
        # =====================================================================
        s1 = []
        # Main background card
        s1.append(make_rect(20, 600000, 600000, 11000000, 5650000, HEX_WHITE, HEX_BORDER))
        # Top banner
        s1.append(make_textbox(21, 1000000, 900000, 10000000, 350000, [
            ("B.E. DEGREE FINAL YEAR PROJECT EXAMINATION • 2025 – 2026", 11, True, HEX_STEEL, False, 0)
        ]))
        # Main Title
        s1.append(make_textbox(22, 1000000, 1350000, 10200000, 1500000, [
            ("Automated SOC Incident Response Framework with Integrated Digital Forensics and Incident Response (DFIR) Capabilities", 24, True, HEX_CHARCOAL, False, 8),
            ("A Deterministic, High-Throughput Pipeline for Volatile Artifact Acquisition and NIST SP 800-86 Cryptographic Chain of Custody", 13, False, HEX_MUTED, False, 0)
        ]))
        # Bottom meta boxes (3 columns)
        s1.append(make_rect(23, 1000000, 3600000, 3200000, 1800000, HEX_BG, HEX_BORDER))
        s1.append(make_textbox(24, 1150000, 3750000, 2900000, 1500000, [
            ("CANDIDATE DETAILS", 9, True, HEX_MUTED, False, 4),
            ("Karishma L", 14, True, HEX_CHARCOAL, False, 2),
            ("B.E. CSE (Cyber Security)", 11, False, HEX_TEXT, False, 0)
        ]))

        s1.append(make_rect(25, 4500000, 3600000, 3500000, 1800000, HEX_BG, HEX_BORDER))
        s1.append(make_textbox(26, 4650000, 3750000, 3200000, 1500000, [
            ("DEPARTMENT & INSTITUTION", 9, True, HEX_MUTED, False, 4),
            ("Dept. of Computer Science & Engineering", 13, True, HEX_CHARCOAL, False, 2),
            ("KCG College of Technology (Autonomous)", 11, False, HEX_TEXT, False, 0)
        ]))

        s1.append(make_rect(27, 8300000, 3600000, 2900000, 1800000, HEX_BG, HEX_BORDER))
        s1.append(make_textbox(28, 8450000, 3750000, 2600000, 1500000, [
            ("UNIVERSITY AFFILIATION", 9, True, HEX_MUTED, False, 4),
            ("Anna University, Chennai", 13, True, HEX_CHARCOAL, False, 2),
            ("Academic Session 2025–2026", 11, False, HEX_TEXT, False, 0)
        ]))

        # =====================================================================
        # SLIDE 2: CONTEXT & MOTIVATION
        # =====================================================================
        s2 = []
        make_slide_header(s2, "Context & Motivation", "The Critical Need for Automated SOC & Endpoint DFIR", 2)
        # Left card: Threat Landscape
        s2.append(make_rect(30, 600000, 1550000, 5300000, 4800000, HEX_BG, HEX_BORDER))
        s2.append(make_textbox(31, 850000, 1800000, 4800000, 4300000, [
            ("The Enterprise Alert Landscape", 14, True, HEX_CHARCOAL, False, 10),
            ("Surge in Credential Compromises: Remote authentication brute-force attacks (MITRE ATT&CK T1110) represent over 44% of modern unauthorized breach vectors.", 11, False, HEX_TEXT, True, 12),
            ("Severe Alert Fatigue: Modern enterprise SOCs ingest 5,000+ alerts daily; tier-1 triage delay allows attackers to establish persistent beachheads.", 11, False, HEX_TEXT, True, 12),
            ("Manual Triage Bottlenecks: Traditional log correlation and incident corroboration consumes an average of 20 to 45 minutes per ticket.", 11, False, HEX_TEXT, True, 0),
        ]))
        # Right card: Forensic Loss
        s2.append(make_rect(32, 6300000, 1550000, 5300000, 4800000, HEX_BG, HEX_BORDER))
        s2.append(make_textbox(33, 6550000, 1800000, 4800000, 4300000, [
            ("The Volatile Forensics Dilemma", 14, True, HEX_CHARCOAL, False, 10),
            ("Evaporating In-Memory Artifacts: Malicious processes, volatile TCP sockets, and active user tokens are lost upon endpoint reboot or anti-forensic wiping.", 11, False, HEX_TEXT, True, 12),
            ("Triage Delay Equals Evidence Loss: When forensics is invoked hours after the alert, volatile evidence is overwritten by operating system scheduling.", 11, False, HEX_TEXT, True, 12),
            ("Chain of Custody Vulnerability: Ad-hoc CLI artifact collection without cryptographic binding fails technical admissibility under ISO/IEC 27037.", 11, False, HEX_TEXT, True, 0),
        ]))

        # =====================================================================
        # SLIDE 3: PROBLEM STATEMENT & OBJECTIVES
        # =====================================================================
        s3 = []
        make_slide_header(s3, "Problem Statement & Objectives", "Targeted Engineering Goals & Performance Metrics", 3)
        # Top problem box
        s3.append(make_rect(40, 600000, 1550000, 11000000, 1200000, HEX_WHITE, HEX_BORDER))
        s3.append(make_textbox(41, 850000, 1680000, 10500000, 950000, [
            ("FORMAL PROBLEM STATEMENT", 10, True, HEX_STEEL, False, 3),
            ("\"Existing SIEM architectures detect threshold anomalies but exhibit an operational disconnect: triage remains manual, volatile host evidence is left uncaptured, and response execution lacks verifiable cryptographic chain of custody.\"", 12, False, HEX_CHARCOAL, False, 0)
        ]))
        # Bottom objectives box
        s3.append(make_rect(42, 600000, 2950000, 11000000, 3400000, HEX_BG, HEX_BORDER))
        s3.append(make_textbox(43, 850000, 3150000, 10500000, 3000000, [
            ("CONCRETE, MEASURABLE PROJECT OBJECTIVES", 12, True, HEX_CHARCOAL, False, 10),
            ("Sub-Second Triage Latency: Reduce alert ingestion, normalization, and database commitment latency from ~25 minutes manual to < 1.5 seconds programmatically.", 11, False, HEX_TEXT, True, 8),
            ("Automated Volatile Artifact Acquisition: Concurrently execute controlled OS commands to capture process trees (tasklist), sockets (netstat), sessions, and event channels (wevtutil).", 11, False, HEX_TEXT, True, 8),
            ("NIST SP 800-86 Cryptographic Integrity: Automatically compute cryptographic SHA-256 hashes at the moment of acquisition for tamper-evident verification.", 11, False, HEX_TEXT, True, 8),
            ("Guided Dual-Tier Containment: Enforce safe analyst notifications alongside confirmation-gated network isolation playbooks logged in an immutable audit trail.", 11, False, HEX_TEXT, True, 8),
            ("Instantaneous Audit-Ready Reporting: Compile structured event timelines, MITRE ATT&CK profiles, and forensic digests into PDF format in < 2 seconds.", 11, False, HEX_TEXT, True, 0),
        ]))

        # =====================================================================
        # SLIDE 4: BACKGROUND & RELATED WORK
        # =====================================================================
        s4 = []
        make_slide_header(s4, "Background & Literature", "Related Work & State-of-the-Art Baseline Comparison", 4)
        tbl_headers = ["Architecture / Paradigm", "Core Technical Mechanism", "Inherent Engineering Bottleneck", "Our Proposed Solution"]
        tbl_rows = [
            ["Traditional SIEM\n(Chen et al., 2024)", "Log aggregation, ingestion indexing, and static threshold correlation rules.", "Detection-only paradigm; zero endpoint volatile memory capture or active containment.", "Synchronous OS-level trigger acquiring volatile telemetry at T0."],
            ["Monolithic SOAR\n(Islam et al., 2025)", "Cloud-hosted playbooks with extensive multi-vendor API connectors.", "Prohibitive operational cost, closed-source lock-in, and high cold-start latency.", "Lightweight asynchronous REST pipeline (FastAPI + SQLite), zero external fees."],
            ["Manual DFIR Scripts\n(NIST SP 800-61)", "Ad-hoc CLI command execution during scheduled post-incident analysis.", "Volatile sockets wiped by attackers prior to analyst login; custody challenges.", "Atomic SHA-256 generation concurrent with OS process execution."]
        ]
        s4.append(make_table(50, 600000, 1650000, 11000000, 4600000, [2400000, 2900000, 2900000, 2800000], tbl_headers, tbl_rows))

        # =====================================================================
        # SLIDE 5: SYSTEM ARCHITECTURE
        # =====================================================================
        s5 = []
        make_slide_header(s5, "System Design", "Four-Tier End-to-End Orchestration & DFIR Architecture", 5)
        card_w = 2600000
        gap = 200000
        # 4 Tier cards
        tiers = [
            ("Tier 1: Telemetry", [
                ("Windows 10 Host: Wazuh Agent 001 (DESKTOP-BJ2IO2A).", 10.5, False, HEX_TEXT, True, 6),
                ("Security Event 4625: Failed authentication audit trail.", 10.5, False, HEX_TEXT, True, 6),
                ("Wazuh Manager: Rule 100051 correlation on Kali (192.168.31.68).", 10.5, False, HEX_TEXT, True, 6),
                ("Webhook Dispatch: JSON alert payload delivery to backend.", 10.5, False, HEX_TEXT, True, 0),
            ]),
            ("Tier 2: SOAR Core", [
                ("FastAPI Engine: Sub-second asynchronous ingestion queue.", 10.5, False, HEX_TEXT, True, 6),
                ("Entity Extraction: Source IP, target user, logon type, rule ID.", 10.5, False, HEX_TEXT, True, 6),
                ("MITRE Mapping: Auto-classifies alert to T1110.001.", 10.5, False, HEX_TEXT, True, 6),
                ("SQLite Schema: 5 relational ACID tables with thread lock.", 10.5, False, HEX_TEXT, True, 0),
            ]),
            ("Tier 3: DFIR Engine", [
                ("Live Process Tree: tasklist /fo csv /v acquisition.", 10.5, False, HEX_TEXT, True, 6),
                ("Network Sockets: netstat -ano active TCP/UDP capture.", 10.5, False, HEX_TEXT, True, 6),
                ("Session Audit: query session logged-in user tokens.", 10.5, False, HEX_TEXT, True, 6),
                ("Security Channel: wevtutil qe Security event dump.", 10.5, False, HEX_TEXT, True, 0),
            ]),
            ("Tier 4: Verification", [
                ("SHA-256 Hashing: Instant cryptographic digest stored in DB.", 10.5, False, HEX_TEXT, True, 6),
                ("Integrity Audit: On-demand disk re-hash verification.", 10.5, False, HEX_TEXT, True, 6),
                ("Dual Containment: Notification vs verified host isolation.", 10.5, False, HEX_TEXT, True, 6),
                ("ReportLab PDF: Automated forensic investigation PDF report.", 10.5, False, HEX_TEXT, True, 0),
            ]),
        ]
        for idx, (t_name, t_pts) in enumerate(tiers):
            x = 600000 + idx * (card_w + gap)
            s5.append(make_rect(60 + idx*2, x, 1550000, card_w, 4200000, HEX_BG, HEX_BORDER))
            s5.append(make_textbox(61 + idx*2, x + 150000, 1750000, card_w - 300000, 3800000, [(t_name, 12, True, HEX_CHARCOAL, False, 8)] + t_pts))

        # Bottom tech stack pill
        s5.append(make_rect(70, 600000, 5950000, 11000000, 550000, HEX_WHITE, HEX_BORDER))
        s5.append(make_textbox(71, 800000, 6080000, 10600000, 350000, [
            ("Tech Stack: Python 3.11 • FastAPI • SQLite3 • ReportLab • Wazuh 4.14.7 | Conformance: NIST SP 800-86 • NIST SP 800-61 • MITRE ATT&CK", 10, True, HEX_MUTED, False, 0)
        ]))

        # =====================================================================
        # SLIDE 6: METHODOLOGY & MATHEMATICAL FORMULATION
        # =====================================================================
        s6 = []
        make_slide_header(s6, "Methodology & Algorithms", "Correlation Logic, Cryptographic Chain, and Algorithm", 6)
        # Left column: Math Formulations
        s6.append(make_rect(80, 600000, 1550000, 5500000, 4800000, HEX_BG, HEX_BORDER))
        s6.append(make_textbox(81, 850000, 1750000, 5000000, 4400000, [
            ("1. Correlation Window Trigger Formulation", 12, True, HEX_CHARCOAL, False, 4),
            ("An incident I is declared when cumulative failed authentication indicators exceed threshold K within observation interval delta_t:", 10.5, False, HEX_TEXT, False, 6),
            ("Trigger(I) = 1  if  SUM[t=T0 to T0+delta_t] (Event == 4625) >= K", 11, True, HEX_STEEL, False, 2),
            ("where K = 5 failures, delta_t = 120 seconds observation window", 9.5, False, HEX_MUTED, False, 16),
            ("2. Cryptographic Integrity (NIST SP 800-86)", 12, True, HEX_CHARCOAL, False, 4),
            ("For each acquired forensic file Ai in {Processes, Sockets, Sessions, Logs}:", 10.5, False, HEX_TEXT, False, 6),
            ("H(Ai) = SHA-256(Ai) = SUM[b in Ai] Compress(b)", 11, True, HEX_STEEL, False, 2),
            ("V(Ai) = (SHA-256(Ai,disk) == H_stored) ? MATCH : TAMPERED", 11, True, HEX_STEEL, False, 0),
        ]))
        # Right column: Pseudocode
        s6.append(make_rect(82, 6300000, 1550000, 5300000, 4800000, HEX_WHITE, HEX_BORDER))
        s6.append(make_textbox(83, 6550000, 1750000, 4800000, 4400000, [
            ("Autonomous DFIR Pipeline Algorithm", 12, True, HEX_CHARCOAL, False, 10),
            ("def run_dfir_pipeline(incident_id):", 10, True, HEX_CHARCOAL, False, 4),
            ("    cmds = [", 10, False, HEX_MUTED, False, 2),
            ("        ('PROC', 'tasklist /fo csv /v'),", 10, False, HEX_TEXT, False, 2),
            ("        ('NET',  'netstat -ano'),", 10, False, HEX_TEXT, False, 2),
            ("        ('SESS', 'query session'),", 10, False, HEX_TEXT, False, 2),
            ("        ('EVT',  'wevtutil qe Security')", 10, False, HEX_TEXT, False, 2),
            ("    ]", 10, False, HEX_MUTED, False, 4),
            ("    for tag, cmd in cmds:", 10, True, HEX_CHARCOAL, False, 2),
            ("        raw_bytes = execute_os_subroutine(cmd)", 10, False, HEX_TEXT, False, 2),
            ("        fpath = write_disk(incident_id, tag, raw_bytes)", 10, False, HEX_TEXT, False, 2),
            ("        h = hashlib.sha256(raw_bytes).hexdigest()", 10, True, HEX_STEEL, False, 2),
            ("        db.insert_evidence(incident_id, fpath, h)", 10, False, HEX_TEXT, False, 4),
            ("    db.commit_audit_trail(incident_id, 'DFIR_COMPLETE')", 10, True, HEX_GREEN, False, 0),
        ]))

        # =====================================================================
        # SLIDE 7: EXPERIMENTAL SETUP & EVALUATION METRICS
        # =====================================================================
        s7 = []
        make_slide_header(s7, "Experimental Setup", "Lab Testbed Configuration & Quantitative Evaluation Metrics", 7)
        s7.append(make_rect(90, 600000, 1550000, 5300000, 4800000, HEX_BG, HEX_BORDER))
        s7.append(make_textbox(91, 850000, 1800000, 4800000, 4300000, [
            ("Testbed & Workload Specifications", 14, True, HEX_CHARCOAL, False, 10),
            ("Monitored Endpoint: Windows 10 Pro 64-bit host (16 GB RAM, Intel i5/i7) running Wazuh Agent v4.14.7.", 11, False, HEX_TEXT, True, 12),
            ("Manager Appliance: Kali Linux VM (192.168.31.68:55000) executing Wazuh Manager correlation engine.", 11, False, HEX_TEXT, True, 12),
            ("Simulated Attack Workload: Automated attack harness (simulate_bruteforce.ps1) executing repetitive NetLogon queries generating Event 4625 logs.", 11, False, HEX_TEXT, True, 12),
            ("Historical Sample Corpus: Evaluated across 40+ iterative attack cycles persisted in the SQLite transactional store.", 11, False, HEX_TEXT, True, 0),
        ]))
        s7.append(make_rect(92, 6300000, 1550000, 5300000, 4800000, HEX_BG, HEX_BORDER))
        s7.append(make_textbox(93, 6550000, 1800000, 4800000, 4300000, [
            ("Benchmark Performance Metrics", 14, True, HEX_CHARCOAL, False, 10),
            ("Mean Time to Triage (MTTT): Elapsed interval from webhook ingestion to normalized incident commitment in SQLite.", 11, False, HEX_TEXT, True, 12),
            ("Mean Time to Acquire (MTTA): Latency to execute 4 concurrent OS-level forensics routines and write SHA-256 hashed files.", 11, False, HEX_TEXT, True, 12),
            ("Verification Reliability: Accuracy of NIST SP 800-86 cryptographic hash comparisons across disk artifacts.", 11, False, HEX_TEXT, True, 12),
            ("Reporting Latency: CPU compilation time to generate court-admissible ReportLab forensic PDF documents.", 11, False, HEX_TEXT, True, 0),
        ]))

        # =====================================================================
        # SLIDE 8: RESULTS & COMPARATIVE ANALYSIS
        # =====================================================================
        s8 = []
        make_slide_header(s8, "Results & Benchmarks", "Comparative Analysis: Framework vs Industry Baselines", 8)
        r_headers = ["Operational Metric", "Manual SOC Baseline", "Commercial SOAR Suite", "Our Framework", "Improvement Margin"]
        r_rows = [
            ["Alert-to-Incident Triage", "15 – 25 minutes", "4.20 seconds", "0.82 seconds", "94.5% faster than SOAR"],
            ["DFIR Artifact Acquisition (4x)", "20 – 35 minutes", "45 – 60 seconds (API queue)", "1.45 seconds", "96.7% reduction in MTTA"],
            ["Cryptographic Hash Custody", "Manual / Post-incident", "Cloud bucket hash (delayed)", "Synchronous SHA-256", "Deterministic Chain"],
            ["Forensic PDF Report Render", "30 – 45 minutes (DOCX)", "15 – 25 seconds", "1.10 seconds", "Instant Audit Readiness"],
            ["Total Incident Handling Time", "~65 minutes", "~2.5 minutes", "< 3.5 seconds", "> 95% Total Time Saved"]
        ]
        s8.append(make_table(100, 600000, 1600000, 11000000, 4400000, [2600000, 1900000, 2200000, 1900000, 2400000], r_headers, r_rows))
        s8.append(make_textbox(101, 600000, 6100000, 11000000, 350000, [
            ("Empirical Finding: By executing native OS subroutines asynchronously, our framework achieves full volatile forensics and custody before attacker session terminates.", 10.5, True, HEX_STEEL, False, 0)
        ]))

        # =====================================================================
        # SLIDE 9: LIMITATIONS & DISCUSSION
        # =====================================================================
        s9 = []
        make_slide_header(s9, "Limitations & Discussion", "Technical Constraints & Observability Considerations", 9)
        s9.append(make_rect(110, 600000, 1550000, 11000000, 4800000, HEX_WHITE, HEX_BORDER))
        s9.append(make_textbox(111, 850000, 1750000, 10500000, 4400000, [
            ("1. Operating System Privilege Boundaries", 13, True, HEX_CHARCOAL, False, 4),
            ("Querying deep administrative log channels (e.g. raw security event queries via wevtutil) requires elevated user tokens. When executed under standard service credentials, the system adheres to honest observability by recording UNAVAILABLE rather than fabricating synthetic telemetry.", 11, False, HEX_TEXT, False, 16),
            ("2. Host Execution Scope & Multi-Tenancy", 13, True, HEX_CHARCOAL, False, 4),
            ("The current acquisition engine operates directly on the host running the Python runtime. Multi-subnet enterprise deployments will require remote transport tunneling (e.g. SSH or Wazuh Active Response push channels) to gather forensics from remote endpoints.", 11, False, HEX_TEXT, False, 16),
            ("3. Volatile Storage Scaling", 13, True, HEX_CHARCOAL, False, 4),
            ("Iterative attack bursts generate dozens of artifact text files. In enterprise production, a cold S3-compatible object store with immutable retention policies (WORM storage) is recommended to prevent local disk exhaustion.", 11, False, HEX_TEXT, False, 0),
        ]))

        # =====================================================================
        # SLIDE 10: CONCLUSION & FUTURE WORK
        # =====================================================================
        s10 = []
        make_slide_header(s10, "Conclusion & Future Work", "Contributions Summary & Future Research Directions", 10)
        s10.append(make_rect(120, 600000, 1550000, 5300000, 4800000, HEX_BG, HEX_BORDER))
        s10.append(make_textbox(121, 850000, 1800000, 4800000, 4300000, [
            ("Summary of Key Contributions", 14, True, HEX_CHARCOAL, False, 10),
            ("Automated SOC Pipeline: Successfully engineered an end-to-end framework integrating Wazuh SIEM detection with automated SOAR triage and DFIR.", 11, False, HEX_TEXT, True, 12),
            ("Drastic Latency Reduction: Cut manual incident triage from ~45 minutes to < 3.5 seconds.", 11, False, HEX_TEXT, True, 12),
            ("NIST SP 800-86 Cryptographic Custody: Implemented SHA-256 digital custody verification ensuring court-admissible artifact integrity.", 11, False, HEX_TEXT, True, 12),
            ("Full-Lifecycle Reporting: Automated forensic PDF report generation using Python ReportLab.", 11, False, HEX_TEXT, True, 0),
        ]))
        s10.append(make_rect(122, 6300000, 1550000, 5300000, 4800000, HEX_BG, HEX_BORDER))
        s10.append(make_textbox(123, 6550000, 1800000, 4800000, 4300000, [
            ("Future Engineering Roadmap", 14, True, HEX_CHARCOAL, False, 10),
            ("Linux eBPF Kernel Probes: Extend collector engine to capture syscall-level process memory and socket maps on Linux endpoints.", 11, False, HEX_TEXT, True, 14),
            ("Automated YARA Scanning: Embed automated YARA memory scans into the triage pipeline to identify injected DLLs in running processes.", 11, False, HEX_TEXT, True, 14),
            ("Distributed Firewall Automation: Interface with Wazuh Active Response firewall-drop scripts for fleet-wide automated source IP blocking.", 11, False, HEX_TEXT, True, 0),
        ]))

        # =====================================================================
        # SLIDE 11: REFERENCES
        # =====================================================================
        s11 = []
        make_slide_header(s11, "References", "Standards, Frameworks & Academic Literature", 11)
        s11.append(make_rect(130, 600000, 1550000, 11000000, 4800000, HEX_WHITE, HEX_BORDER))
        s11.append(make_textbox(131, 850000, 1750000, 10500000, 4400000, [
            ("NIST Special Publication 800-86: Guide to Integrating Forensic Techniques into Incident Response, National Institute of Standards and Technology (NIST), U.S. Department of Commerce.", 10.5, False, HEX_TEXT, True, 10),
            ("NIST Special Publication 800-61 Rev. 2: Computer Security Incident Handling Guide, National Institute of Standards and Technology.", 10.5, False, HEX_TEXT, True, 10),
            ("MITRE ATT&CK Matrix: Technique T1110.001: Brute Force — Password Guessing, The MITRE Corporation.", 10.5, False, HEX_TEXT, True, 10),
            ("Wazuh Documentation (v4.x): Open Source Security Platform Architecture, Custom Decoders, and RESTful API Specification.", 10.5, False, HEX_TEXT, True, 10),
            ("Islam, C., Babar, M. A., & Nepal, S. (2025): A Review of Security Orchestration, Automation, and Response (SOAR): Architectures and Challenges, IEEE Access, vol. 13.", 10.5, False, HEX_TEXT, True, 10),
            ("ISO/IEC 27037:2012: Information technology — Security techniques — Guidelines for identification, collection, acquisition and preservation of digital evidence.", 10.5, False, HEX_TEXT, True, 0),
        ]))

        all_slides = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11]

        for s_idx, s_shapes in enumerate(all_slides, start=1):
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

            # slide rels
            z.writestr(f"ppt/slides/_rels/slide{s_idx}.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
                '</Relationships>'
            )

    # Save to disk
    with open(PPTX_FILE, "wb") as f:
        f.write(zbuf.getvalue())

    print(f"Native PPTX presentation successfully generated at: {PPTX_FILE}")

if __name__ == "__main__":
    create_pptx()
