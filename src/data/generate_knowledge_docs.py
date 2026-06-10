"""
SteelMind AI Wizard — Synthetic Knowledge Documents Generator
=============================================================
Generates PDF files with synthetic knowledge base content.

Run:
    python src/data/generate_knowledge_docs.py
"""

import os
from pathlib import Path

try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2 not installed. Please install it: pip install fpdf2")
    exit(1)

# Ensure directory exists
KB_DIR = Path(__file__).parent.parent / "knowledge_base" / "documents"
KB_DIR.mkdir(parents=True, exist_ok=True)


class DocumentGenerator(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Tata Steel - SteelMind AI Wizard Knowledge Base", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")


def create_pdf(filename: str, title: str, sections: dict):
    pdf = DocumentGenerator()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 15, title, 0, 1, "C")
    pdf.ln(10)

    # Content
    for section_title, content in sections.items():
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, section_title, 0, 1, "L")
        pdf.ln(2)

        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, content)
        pdf.ln(5)

    save_path = KB_DIR / filename
    pdf.output(str(save_path))
    print(f"✅ Generated: {save_path}")


def generate_all_documents():
    print("Generating Knowledge Base PDFs...")

    # 1. Blast Furnace Operations Manual
    create_pdf(
        "blast_furnace_manual.pdf",
        "Blast Furnace Operations & Maintenance Manual",
        {
            "1. Introduction": "This manual covers the operations and maintenance of Blast Furnaces BF-001 and BF-002.",
            "2. Normal Operating Parameters": "Temperature: 1150-1300 C. Pressure: 150-200 bar. Airflow must be maintained consistently to ensure proper smelting.",
            "3. Tuyere Maintenance": "Tuyeres are critical for air injection. Inspect tuyeres weekly for wear and tear. If temperature drops below 1100 C, check for tuyere blockage.",
            "4. Cooling System": "The stave cooling system uses water. Check for leaks daily. A leak will cause a sudden pressure drop below 140 bar.",
            "5. Emergency Shutdown": "If temperature exceeds 1550 C or pressure exceeds 250 bar, initiate emergency shutdown procedure immediately to prevent explosion.",
        }
    )

    # 2. Rolling Mill Bearing Replacement SOP
    create_pdf(
        "rolling_mill_bearing_sop.pdf",
        "Rolling Mill Bearing Replacement SOP",
        {
            "Purpose": "Standard Operating Procedure for replacing roller bearings in Rolling Mills (RM-001, RM-002).",
            "Symptoms of Failure": "High vibration (>3.5 mm/s), abnormal noise, and increased motor current (>115A).",
            "Required Tools": "Hydraulic puller, torque wrench, bearing heater, new SKF-22236 bearing.",
            "Procedure": "Step 1: Isolate power and apply LOTO (Lockout/Tagout). Step 2: Remove the coupling and housing cover. Step 3: Use hydraulic puller to remove the old bearing. Step 4: Heat the new bearing to 90 C using the bearing heater. Step 5: Slide the new bearing onto the shaft. Step 6: Apply grease and reassemble the housing. Step 7: Torque housing bolts to 450 Nm.",
        }
    )

    # 3. Hydraulic System Maintenance SOP
    create_pdf(
        "hydraulic_system_sop.pdf",
        "Hydraulic System Maintenance SOP",
        {
            "Overview": "Maintenance guidelines for central hydraulic systems (HS-001).",
            "Routine Checks": "Check oil level daily. Normal pressure is 150-200 bar.",
            "Seal Replacement Procedure": "When pressure drops below 140 bar or oil leakage is observed, seal replacement is required. Step 1: Depressurize the system. Step 2: Disconnect the affected cylinder. Step 3: Remove the gland nut. Step 4: Replace the polyurethane seals (Part# SEAL-HYD-04). Step 5: Reassemble and bleed air from the system.",
            "Oil Change": "Hydraulic oil (ISO VG 46) must be replaced every 4000 operating hours. Take oil samples every 500 hours for contamination analysis.",
        }
    )

    # 4. Electric Arc Furnace Troubleshooting
    create_pdf(
        "eaf_troubleshooting.pdf",
        "Electric Arc Furnace Troubleshooting Guide",
        {
            "Overview": "Troubleshooting guide for EAF-001.",
            "Fault: Electrode Breakage": "Symptom: Sudden loss of arc, current drops to zero. Cause: Scrap cave-in or mechanical stress. Action: Retract electrode arms, remove broken pieces from the melt, install new electrode segment, tighten nipple joint to 2500 Nm.",
            "Fault: Water Cooled Panel Leak": "Symptom: High moisture in off-gas, drop in cooling water return pressure. Cause: Arc deflection or slag erosion. Action: Stop power immediately. Inspect panels visually. Replace leaking panel.",
            "Fault: Hydraulic Roof Lift Failure": "Symptom: Roof fails to lift or swing. Cause: Hydraulic pump failure or solenoid valve stuck. Action: Check pump pressure (>120 bar). Manually override solenoid valve to test.",
        }
    )

    # 5. Spare Parts Catalog
    create_pdf(
        "spare_parts_catalog.pdf",
        "Plant Spare Parts Catalog",
        {
            "Bearings": "SKF-22236 (Roller Bearing, RM) - Location: Warehouse A, Rack 12. \nSKF-6210 (Motor Bearing, CV) - Location: Warehouse A, Rack 5.",
            "Hydraulic Components": "SEAL-HYD-04 (Polyurethane Seal Set) - Location: Warehouse B, Bin 42. \nPUMP-REX-01 (Rexroth Hydraulic Pump) - Location: Warehouse B, Pallet 3.",
            "Sensors": "SENS-TEMP-K (K-type Thermocouple, 0-1600C) - Location: E-Store, Cabinet 2. \nSENS-VIB-01 (Piezoelectric Vibration Sensor) - Location: E-Store, Cabinet 4.",
            "Furnace Components": "TUY-CU-01 (Copper Tuyere for BF) - Location: Warehouse C, Zone 1. \nELEC-GRAPH-600 (Graphite Electrode 600mm) - Location: Outdoor Storage Yard.",
        }
    )

    # 6. Failure Analysis Report
    create_pdf(
        "failure_analysis_report.pdf",
        "Historical Failure Analysis Cases",
        {
            "Case 1: RM-001 Catastrophic Bearing Failure (2025-03-12)": "Observation: Rolling mill seized during operation. Vibration sensors indicated 7.2 mm/s shortly before failure. Root Cause: Lack of lubrication due to blocked grease line. Resolution: Replaced bearing and installed automated grease flow monitors. Recommendation: Inspect grease lines monthly.",
            "Case 2: BF-002 Tuyere Burnout (2024-11-05)": "Observation: Water leak into the furnace causing a steam explosion. Root Cause: Tuyere cooling water flow was restricted due to scale buildup. Resolution: Replaced tuyere and chemically cleaned the cooling circuit. Recommendation: Implement daily cooling water flow checks and annual chemical cleaning.",
            "Case 3: CV-001 Conveyor Belt Tear (2025-01-20)": "Observation: Main feed conveyor belt tore laterally. Root Cause: A sharp piece of scrap metal bypassed the magnetic separator and jammed against the idler. Resolution: Spliced the belt and replaced the magnetic separator with a stronger unit. Recommendation: Regular calibration of the magnetic separator.",
        }
    )

    print("✅ All Knowledge Base PDFs generated successfully.")


if __name__ == "__main__":
    generate_all_documents()
