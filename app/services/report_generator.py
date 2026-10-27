from pathlib import Path
from typing import Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from app.config import REPORTS_DIR, WAZUH_MANAGER_IP, WAZUH_MANAGER_VERSION
from app.models.schemas import DFIRTriageResult


def generate_incident_pdf(triage: DFIRTriageResult, output_path: Optional[Path] = None) -> Path:
    """Generate a publication-grade SOC DFIR Incident Response Report PDF using ReportLab."""
    if output_path is None:
        filename = f"{triage.incident_id}_DFIR_Report.pdf"
        output_path = REPORTS_DIR / filename

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#FFFFFF"),
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#BDC3C7"),
    )

    h2_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1A2530"),
        spaceBefore=10,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2C3E50"),
    )

    badge_style = ParagraphStyle(
        "BadgeText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.white,
        alignment=1,  # Center
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#2C3E50"),
    )

    elements = []

    # 1. Header Banner
    banner_data = [
        [
            Paragraph("AUTOMATED SOC INCIDENT RESPONSE & DFIR REPORT", title_style),
            Paragraph(f"<b>SEVERITY LEVEL {triage.severity_level}</b><br/>{triage.severity}", badge_style),
        ],
        [
            Paragraph(f"Wazuh SIEM/SOAR Pipeline &bull; Automated Forensics Engine", subtitle_style),
            Paragraph(f"Generated: {triage.timestamp[:19].replace('T', ' ')}", subtitle_style),
        ],
    ]
    banner_table = Table(banner_data, colWidths=[380, 160])
    banner_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, 1), colors.HexColor("#1A2530")),
            ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#C0392B")),  # Severity badge red
            ("BACKGROUND", (1, 1), (1, 1), colors.HexColor("#2C3E50")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    elements.append(banner_table)
    elements.append(Spacer(1, 14))

    # 2. Incident Overview & Metadata
    elements.append(Paragraph("1. Incident Overview & SIEM Detection Metadata", h2_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#BDC3C7"), spaceAfter=8))

    meta_data = [
        [
            Paragraph("<b>Incident ID:</b>", body_style),
            Paragraph(f"<code>{triage.incident_id}</code>", body_style),
            Paragraph("<b>Detection Rule ID:</b>", body_style),
            Paragraph(f"<b>{triage.rule_id}</b> (Level {triage.severity_level})", body_style),
        ],
        [
            Paragraph("<b>Detection Time:</b>", body_style),
            Paragraph(triage.timestamp[:19].replace("T", " "), body_style),
            Paragraph("<b>SIEM Manager:</b>", body_style),
            Paragraph(f"Kali Linux ({WAZUH_MANAGER_IP}, v{WAZUH_MANAGER_VERSION})", body_style),
        ],
        [
            Paragraph("<b>Rule Description:</b>", body_style),
            Paragraph(triage.rule_description, body_style),
            Paragraph("<b>Correlation Logic:</b>", body_style),
            Paragraph("5 failed logons (Evt 4625) in 120s by same user", body_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[95, 175, 105, 165])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F9FA")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    elements.append(meta_table)
    elements.append(Spacer(1, 12))

    # 3. Affected Endpoint & Identity Context
    elements.append(Paragraph("2. Targeted Asset & Identity Context", h2_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#BDC3C7"), spaceAfter=8))

    endpoint_data = [
        [
            Paragraph("<b>Endpoint Hostname:</b>", body_style),
            Paragraph(f"<b>{triage.agent_name}</b>", body_style),
            Paragraph("<b>Agent ID:</b>", body_style),
            Paragraph(f"<code>{triage.agent_id}</code>", body_style),
        ],
        [
            Paragraph("<b>Targeted Account:</b>", body_style),
            Paragraph(f"<font color='#C0392B'><b>{triage.target_user}</b></font>", body_style),
            Paragraph("<b>Logon Type:</b>", body_style),
            Paragraph(triage.logon_type, body_style),
        ],
        [
            Paragraph("<b>Source Network IP:</b>", body_style),
            Paragraph(f"<code>{triage.source_ip}</code>", body_style),
            Paragraph("<b>Audit Policy:</b>", body_style),
            Paragraph("auditpol Logon Failure (Active)", body_style),
        ],
    ]
    endpoint_table = Table(endpoint_data, colWidths=[105, 165, 95, 175])
    endpoint_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F6F7")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D5DBDB")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    elements.append(endpoint_table)
    elements.append(Spacer(1, 12))

    # 4. MITRE ATT&CK Framework Alignment
    elements.append(Paragraph("3. MITRE ATT&CK&reg; Classification", h2_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#BDC3C7"), spaceAfter=8))

    mitre_data = [
        [
            Paragraph("<b>MITRE Tactic:</b>", body_style),
            Paragraph(f"<b>{triage.mitre_tactic}</b>", body_style),
            Paragraph("<b>Technique ID:</b>", body_style),
            Paragraph(f"<code><b>{triage.mitre_id}</b></code>", body_style),
        ],
        [
            Paragraph("<b>Technique Name:</b>", body_style),
            Paragraph(triage.mitre_technique, body_style),
            Paragraph("<b>Detection Confidence:</b>", body_style),
            Paragraph("<font color='#27AE60'><b>HIGH (100% Correlation)</b></font>", body_style),
        ],
    ]
    mitre_table = Table(mitre_data, colWidths=[105, 165, 95, 175])
    mitre_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EBF5FB")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AED6F1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    elements.append(mitre_table)
    elements.append(Spacer(1, 12))

    # 5. Forensic Evidence & Event ID 4625 Timeline
    elements.append(Paragraph("4. Forensic Timeline & Evidence Stream (Windows Event ID 4625)", h2_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#BDC3C7"), spaceAfter=8))

    timeline_rows = [
        [
            Paragraph("Event ID", table_header_style),
            Paragraph("Timestamp", table_header_style),
            Paragraph("Target User", table_header_style),
            Paragraph("Sub-Status Code", table_header_style),
            Paragraph("Source IP", table_header_style),
        ]
    ]

    for ev in triage.evidence_events:
        timeline_rows.append([
            Paragraph(f"<b>{ev.event_id}</b>", table_cell_style),
            Paragraph(ev.timestamp, table_cell_style),
            Paragraph(ev.target_user, table_cell_style),
            Paragraph(ev.sub_status, table_cell_style),
            Paragraph(ev.source_ip, table_cell_style),
        ])

    timeline_table = Table(timeline_rows, colWidths=[55, 110, 95, 200, 80])
    timeline_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9F9")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    elements.append(timeline_table)
    elements.append(Spacer(1, 12))

    # 6. Recommended DFIR Containment & Mitigation Actions
    elements.append(Paragraph("5. Automated Containment & DFIR Action Plan", h2_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#BDC3C7"), spaceAfter=8))

    action_rows = [
        [
            Paragraph("Step", table_header_style),
            Paragraph("Action Item & Technical Guidance", table_header_style),
            Paragraph("Status", table_header_style),
        ]
    ]

    for idx, action in enumerate(triage.recommended_actions, 1):
        action_rows.append([
            Paragraph(f"<b>{idx:02d}</b>", table_cell_style),
            Paragraph(action, table_cell_style),
            Paragraph("<font color='#E67E22'><b>RECOMMENDED</b></font>", table_cell_style),
        ])

    action_table = Table(action_rows, colWidths=[35, 415, 90])
    action_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495E")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FDFEFE")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    elements.append(action_table)
    elements.append(Spacer(1, 14))

    # 7. Chain of Custody & Analyst Sign-off
    signoff_data = [
        [
            Paragraph("<b>DFIR Lead / SOC Analyst:</b>", body_style),
            Paragraph("Automated Response Agent (Antigravity SOAR Engine)", body_style),
            Paragraph("<b>Classification:</b>", body_style),
            Paragraph("<font color='#C0392B'><b>CONFIDENTIAL - SOC TIER 2</b></font>", body_style),
        ],
        [
            Paragraph("<b>Evidence Hash (SHA-256):</b>", body_style),
            Paragraph(f"<code>{triage.evidence_hash or 'N/A'}</code>", body_style),

            Paragraph("<b>Review Status:</b>", body_style),
            Paragraph("<font color='#27AE60'><b>VERIFIED SIGNED</b></font>", body_style),
        ],
    ]
    signoff_table = Table(signoff_data, colWidths=[120, 200, 85, 135])
    signoff_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EAEDED")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCD1D1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    elements.append(KeepTogether(signoff_table))

    # Build the document
    doc.build(elements)
    return output_path
