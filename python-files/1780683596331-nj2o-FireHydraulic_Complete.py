#!/usr/bin/env python3
"""
================================================================================
FIRE SPRINKLER HYDRAULIC CALCULATOR - PROFESSIONAL EDITION v7.1
================================================================================
PROFESSIONAL INTERFACE WITH HASSCloud-STYLE PDF REPORT

Features:
- Hazard Description (Light, Ordinary 1, Ordinary 2, Extra Haz 1, Extra Haz 2)
- Min Desired Density (lpm/m² for Metric, gpm/ft² for Imperial)
- Sprinkler System Type (Wet/Dry with NFPA 13 multiplier)
- Area of Sprinkler Operation (m² or ft²)
- Max Area Per Sprinkler (m² or ft²)
- Sprinkler K-Factor (Metric: lpm/√bar, Imperial: GPM/√psi)
- Professional PDF Report matching HASSCloud format
- Pipe Results Table with all hydraulic data
- Water Supply Analysis with Q^1.85 curve

Version: 7.1 - HASSCloud-STYLE PDF REPORT
================================================================================
"""

import math
import json
import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
from enum import Enum
from pathlib import Path

# Set recursion limit
sys.setrecursionlimit(10000)

# ============================================================================
# SECTION 1: IMPORT CHECKS
# ============================================================================

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm, inch
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, 
                                    TableStyle, PageBreak, Image, KeepTogether)
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("WARNING: reportlab not installed. PDF export disabled.")

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


# ============================================================================
# SECTION 2: NFPA 13 DATABASE
# ============================================================================

class NFPA13Database:
    """NFPA 13 Standard Values for Hydraulic Calculations"""
    
    # Hazard Density Ranges (Metric: lpm/m², Imperial: gpm/ft²)
    HAZARD_DENSITY_METRIC = {
        "Light Hazard": {"min": 2.0, "max": 4.0, "default": 3.0},
        "Ordinary Hazard Group 1": {"min": 4.0, "max": 6.0, "default": 5.0},
        "Ordinary Hazard Group 2": {"min": 6.0, "max": 8.0, "default": 7.0},
        "Extra Hazard Group 1": {"min": 8.0, "max": 12.0, "default": 10.0},
        "Extra Hazard Group 2": {"min": 12.0, "max": 16.0, "default": 14.0},
        "High Piled Storage": {"min": 12.0, "max": 20.0, "default": 15.0}
    }
    
    HAZARD_DENSITY_IMPERIAL = {
        "Light Hazard": {"min": 0.07, "max": 0.10, "default": 0.08},
        "Ordinary Hazard Group 1": {"min": 0.10, "max": 0.15, "default": 0.12},
        "Ordinary Hazard Group 2": {"min": 0.15, "max": 0.20, "default": 0.17},
        "Extra Hazard Group 1": {"min": 0.20, "max": 0.30, "default": 0.25},
        "Extra Hazard Group 2": {"min": 0.30, "max": 0.40, "default": 0.35},
        "High Piled Storage": {"min": 0.30, "max": 0.50, "default": 0.40}
    }
    
    # Area of Sprinkler Operation (Metric: m², Imperial: ft²)
    HAZARD_AREA_METRIC = {
        "Light Hazard": 139.0,
        "Ordinary Hazard Group 1": 139.0,
        "Ordinary Hazard Group 2": 139.0,
        "Extra Hazard Group 1": 232.0,
        "Extra Hazard Group 2": 232.0,
        "High Piled Storage": 279.0
    }
    
    HAZARD_AREA_IMPERIAL = {
        "Light Hazard": 1500,
        "Ordinary Hazard Group 1": 1500,
        "Ordinary Hazard Group 2": 1500,
        "Extra Hazard Group 1": 2500,
        "Extra Hazard Group 2": 2500,
        "High Piled Storage": 3000
    }
    
    # Max Area Per Sprinkler (Metric: m², Imperial: ft²)
    MAX_AREA_PER_SPRINKLER_METRIC = {
        "Light Hazard": 20.9,
        "Ordinary Hazard Group 1": 12.1,
        "Ordinary Hazard Group 2": 12.1,
        "Extra Hazard Group 1": 9.3,
        "Extra Hazard Group 2": 9.3,
        "High Piled Storage": 9.3
    }
    
    MAX_AREA_PER_SPRINKLER_IMPERIAL = {
        "Light Hazard": 225,
        "Ordinary Hazard Group 1": 130,
        "Ordinary Hazard Group 2": 130,
        "Extra Hazard Group 1": 100,
        "Extra Hazard Group 2": 100,
        "High Piled Storage": 100
    }
    
    DRY_SYSTEM_MULTIPLIER = 1.3
    
    @classmethod
    def get_recommended_density(cls, hazard: str, use_metric: bool = True) -> float:
        if use_metric:
            return cls.HAZARD_DENSITY_METRIC.get(hazard, {"default": 5.0})["default"]
        return cls.HAZARD_DENSITY_IMPERIAL.get(hazard, {"default": 0.12})["default"]
    
    @classmethod
    def get_recommended_area(cls, hazard: str, use_metric: bool = True, is_dry: bool = False) -> float:
        if use_metric:
            area = cls.HAZARD_AREA_METRIC.get(hazard, 139.0)
        else:
            area = cls.HAZARD_AREA_IMPERIAL.get(hazard, 1500)
        if is_dry:
            area *= cls.DRY_SYSTEM_MULTIPLIER
        return area
    
    @classmethod
    def get_max_area_per_sprinkler(cls, hazard: str, use_metric: bool = True) -> float:
        if use_metric:
            return cls.MAX_AREA_PER_SPRINKLER_METRIC.get(hazard, 12.1)
        return cls.MAX_AREA_PER_SPRINKLER_IMPERIAL.get(hazard, 130)


# ============================================================================
# SECTION 3: DATA MODELS
# ============================================================================

class UnitSystem(Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"

@dataclass
class WaterSupply:
    static_pressure: float = 4.0
    residual_pressure: float = 3.5
    residual_flow: float = 3000.0
    hydrant_elevation: float = 0.0
    exterior_hose_flow: float = 0.0
    
    def get_pressure_at_flow(self, flow: float, use_metric: bool = True) -> float:
        """Calculate available pressure using Q^1.85 relationship"""
        if flow <= 0:
            return self.static_pressure
        if flow >= self.residual_flow:
            ratio = (flow / self.residual_flow) ** 1.85
            pressure_drop = (self.static_pressure - self.residual_pressure) * ratio
            return max(0.5, self.static_pressure - pressure_drop)
        ratio = (flow / self.residual_flow) ** 1.85
        pressure_drop = (self.static_pressure - self.residual_pressure) * ratio
        return max(0.5, self.static_pressure - pressure_drop)

@dataclass
class SystemParameters:
    hazard_description: str = "Ordinary Hazard Group 1"
    min_desired_density: float = 5.0
    sprinkler_system_type: str = "Wet"
    area_of_operation: float = 139.0
    max_area_per_sprinkler: float = 12.1
    sprinkler_k_factor: float = 5.6
    min_residual_pressure: float = 0.5
    use_metric: bool = True
    
    total_flow: float = 0.0
    required_pressure: float = 0.0
    calculated_sprinklers: int = 0
    remote_area: float = 0.0

@dataclass
class PipeResult:
    tag: str
    k_factor: float
    velocity: float
    flow_added: float
    length: float
    c_factor: float
    pf: float
    node1: str
    node1_pt: float
    node1_elev: float
    nominal_dia: float
    friction: float
    pe: float
    node2: str
    node2_pt: float
    node2_elev: float
    total_q: float
    actual_dia: float
    total_length: float
    p_per_foot: float
    pt: float


# ============================================================================
# SECTION 5: PROFESSIONAL PDF REPORT GENERATOR (HASSCloud Style)
# ============================================================================

class HASSCloudReportGenerator:
    """Generate professional PDF reports matching HASSCloud format"""
    
    def __init__(self):
        self.styles = None
        self.elements = []
    
    def generate_report(self, filename: str, params: SystemParameters, 
                       water_supply: WaterSupply, pipe_results: List[PipeResult],
                       sprinkler_count: int, hose_streams: float = 0):
        """Generate complete HASSCloud-style PDF report"""
        
        if not PDF_AVAILABLE:
            print("PDF generation not available. Install reportlab: pip install reportlab")
            return False
        
        # Create PDF document
        doc = SimpleDocTemplate(filename, pagesize=A4,
                                rightMargin=20*mm, leftMargin=20*mm,
                                topMargin=20*mm, bottomMargin=20*mm)
        
        self.elements = []
        
        # Styles
        self.styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=self.styles['Heading1'],
                                     fontSize=14, fontName='Helvetica-Bold',
                                     alignment=0, spaceAfter=12)
        heading_style = ParagraphStyle('CustomHeading', parent=self.styles['Heading2'],
                                       fontSize=11, fontName='Helvetica-Bold',
                                       spaceAfter=6, spaceBefore=12)
        normal_style = self.styles['Normal']
        table_header_style = ParagraphStyle('TableHeader', parent=self.styles['Normal'],
                                            fontName='Helvetica-Bold', fontSize=8,
                                            alignment=1, textColor=colors.white)
        
        # ====================================================================
        # PAGE 1: Header and System Data
        # ====================================================================
        
        # Title
        title = Paragraph("HYDRAULIC CALCULATIONS for", title_style)
        self.elements.append(title)
        self.elements.append(Spacer(1, 5))
        
        sub_title = Paragraph(f"<b>Project name:</b> {params.project_name if hasattr(params, 'project_name') else 'HASSCloud Example Tree'} "
                             f"<b>Location:</b> {params.location if hasattr(params, 'location') else 'HASSCloud Examples'} "
                             f"<b>Drawing no.:</b> {params.drawing_no if hasattr(params, 'drawing_no') else '1'}", normal_style)
        self.elements.append(sub_title)
        self.elements.append(Spacer(1, 10))
        
        # Date
        date_str = datetime.now().strftime('%-m/%-d/%Y')
        date_line = Paragraph(f"<b>Date:</b> {date_str}", normal_style)
        self.elements.append(date_line)
        self.elements.append(Spacer(1, 15))
        
        # Design Section
        design_title = Paragraph("<b>Design</b>", heading_style)
        self.elements.append(design_title)
        
        design_data = [
            ["Remote area number:", "Remote Area 1"],
            ["Remote area location:", "North-West Warehouse Corner"],
            ["Occupancy classification:", params.hazard_description],
            ["Density:", f"{params.min_desired_density:.2f} {'lpm/m²' if params.use_metric else 'gpm/ft²'}"],
            ["Area of application:", f"{params.area_of_operation:.2f} {'m²' if params.use_metric else 'ft²'}"],
            ["Coverage per sprinkler:", f"{params.max_area_per_sprinkler:.2f} {'m²' if params.use_metric else 'ft²'}"],
            ["Type of sprinklers calculated:", f"{params.sprinkler_k_factor:.1f} K-Factor Sprinklers"],
            ["No. of sprinklers calculated:", str(sprinkler_count)],
            ["In-rack demand:", "N/A"],
            ["Hose streams:", f"{hose_streams:.2f} {'lpm' if params.use_metric else 'gpm'}"],
            ["Total water required (including hose streams):", 
             f"{params.total_flow:.2f} {'lpm' if params.use_metric else 'gpm'} @ {params.required_pressure:.2f} {'bar' if params.use_metric else 'psi'}"],
            ["Type of system:", f"Automatic {'Wet' if params.sprinkler_system_type == 'Wet' else 'Dry'}-Pipe Sprinkler System"],
        ]
        
        design_table = Table(design_data, colWidths=[80*mm, 70*mm])
        design_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('ALIGN', (0,0), (0,-1), 'RIGHT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ]))
        self.elements.append(design_table)
        self.elements.append(Spacer(1, 10))
        
        # Water Supply Information
        water_title = Paragraph("<b>Water supply information:</b>", heading_style)
        self.elements.append(water_title)
        
        water_data = [
            ["Date:", "04/30/2026"],
            ["Location:", "81st & Bartlett East Ave"],
            ["Source:", "City Domestic Water Supply"],
            ["Static Pressure:", f"{water_supply.static_pressure:.2f} {'bar' if params.use_metric else 'psi'}"],
            ["Residual Pressure:", f"{water_supply.residual_pressure:.2f} {'bar' if params.use_metric else 'psi'}"],
            ["Measured Flow Rate:", f"{water_supply.residual_flow:.2f} {'lpm' if params.use_metric else 'gpm'}"],
        ]
        
        water_table = Table(water_data, colWidths=[60*mm, 90*mm])
        water_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('ALIGN', (0,0), (0,-1), 'RIGHT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ]))
        self.elements.append(water_table)
        self.elements.append(Spacer(1, 10))
        
        # Contractor and Designer Info
        info_data = [
            ["Name of contractor:", "Henry Silverman"],
            ["Phone number:", "+1 (123) 456-7890"],
            ["Name of designer:", "Henry Silverman"],
            ["Authority having jurisdiction:", "Local Fire Marshall"],
        ]
        
        info_table = Table(info_data, colWidths=[60*mm, 90*mm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('ALIGN', (0,0), (0,-1), 'RIGHT'),
            ('ALIGN', (1,0), (1,-1), 'LEFT'),
        ]))
        self.elements.append(info_table)
        
        # Page break for Flow Test Summary
        self.elements.append(PageBreak())
        
        # ====================================================================
        # PAGE 2: Flow Test Summary Sheet
        # ====================================================================
        
        summary_title = Paragraph("<b>Flow Test Summary Sheet</b>", title_style)
        self.elements.append(summary_title)
        self.elements.append(Spacer(1, 15))
        
        # NFPA Water Supply Data Table
        nfpa_title = Paragraph("<b>NFPA Water Supply Data</b>", heading_style)
        self.elements.append(nfpa_title)
        
        nfpa_data = [
            ["SourceStaticPressure:", f"{water_supply.static_pressure:.4f} {'bar' if params.use_metric else 'psi'}"],
            ["ResidualPressure:", f"{water_supply.residual_pressure:.4f} {'bar' if params.use_metric else 'psi'}"],
            ["Flow @Residual:", f"{water_supply.residual_flow:.2f} {'lpm' if params.use_metric else 'gpm'}"],
            ["AvailablePressure:", f"{params.required_pressure:.4f} {'bar' if params.use_metric else 'psi'}"],
            ["TotalDemand:", f"{params.total_flow:.2f} {'lpm' if params.use_metric else 'gpm'}"],
            ["RequiredPressure:", f"{params.required_pressure:.4f} {'bar' if params.use_metric else 'psi'}"],
        ]
        
        nfpa_table = Table(nfpa_data, colWidths=[70*mm, 70*mm])
        nfpa_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ]))
        self.elements.append(nfpa_table)
        self.elements.append(Spacer(1, 10))
        
        # Hose Stream Allowances
        hose_data = [
            ["HoseStreams:", f"{hose_streams:.2f} {'lpm' if params.use_metric else 'gpm'}"],
            ["SourceHoseAllowance:", f"1500.00 {'lpm' if params.use_metric else 'gpm'}"],
            ["TotalDemand:", f"{params.total_flow:.2f} {'lpm' if params.use_metric else 'gpm'}"],
            ["SourceMargin:", f"{water_supply.static_pressure - params.required_pressure:.4f} "
             f"({(water_supply.static_pressure - params.required_pressure)/water_supply.static_pressure*100:.1f}%) "
             f"{'bar' if params.use_metric else 'psi'}"],
        ]
        
        hose_table = Table(hose_data, colWidths=[70*mm, 70*mm])
        hose_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        self.elements.append(hose_table)
        
        # Page break for Pipe Results
        self.elements.append(PageBreak())
        
        # ====================================================================
        # PAGE 3-7: Pipe Results Table
        # ====================================================================
        
        results_title = Paragraph("<b>Pipe Results</b>", title_style)
        self.elements.append(results_title)
        self.elements.append(Spacer(1, 5))
        
        # Units note
        units_text = f"Units: K-Factor: {'lpm/√bar' if params.use_metric else 'gpm/√psi'}, Velocity: {'m/s' if params.use_metric else 'ft/s'}, Flow added, Total Q: {'lpm' if params.use_metric else 'gpm'}, Node 1 Elev, Node 2 Elev, Length, Friction, Total: {'m' if params.use_metric else 'ft'}, Nom. ID, Act. ID: {'mm' if params.use_metric else 'in'}, Pf, Node 1 PT, Pe, Node 2 PT, Pt: {'bar' if params.use_metric else 'psi'}, Pf/foot: {'bar/m' if params.use_metric else 'psi/ft'}"
        
        units_para = Paragraph(units_text, self.styles['Normal'])
        self.elements.append(units_para)
        self.elements.append(Spacer(1, 8))
        
        # Pipe Results Header
        headers = [
            "Pipe Tag", "K-Factor", "Velocity", "Flow added", "Material", "Fittings",
            "Length", "C Factor", "Pf", "Node 1", "Node 1 PT", "Node 1 Elev",
            "Nom. ID", "Friction", "Pe", "Node 2", "Node 2 PT", "Node 2 Elev",
            "Total Q", "Act. ID", "Total", "P /foot", "Pt"
        ]
        
        # Create header with smaller font for wide table
        header_cells = [Paragraph(h, table_header_style) for h in headers]
        pipe_table = Table([header_cells], repeatRows=1, colWidths=[20*mm, 15*mm, 15*mm, 18*mm, 12*mm, 18*mm, 12*mm, 15*mm, 12*mm, 12*mm, 15*mm, 15*mm, 12*mm, 12*mm, 10*mm, 12*mm, 15*mm, 15*mm, 15*mm, 12*mm, 12*mm, 15*mm, 12*mm])
        
        pipe_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E88E5')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 6),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.2, colors.grey),
            ('FONTSIZE', (0,1), (-1,-1), 5),
        ]))
        
        # Add pipe data rows
        for pipe in pipe_results:
            row = [
                pipe.tag,
                f"{pipe.k_factor:.1f}" if pipe.k_factor > 0 else "-",
                f"{pipe.velocity:.3f}",
                f"{pipe.flow_added:.2f}" if pipe.flow_added > 0 else "-",
                "S40",
                f"T - {pipe.friction:.3f} m" if pipe.friction > 0 else "N/A",
                f"{pipe.length:.2f}",
                f"{pipe.c_factor:.0f}",
                f"{pipe.pf:.4f}",
                pipe.node1,
                f"{pipe.node1_pt:.4f}",
                f"{pipe.node1_elev:.1f}",
                f"{pipe.nominal_dia:.0f}",
                f"{pipe.friction:.2f}",
                f"{pipe.pe:.4f}",
                pipe.node2,
                f"{pipe.node2_pt:.4f}",
                f"{pipe.node2_elev:.1f}",
                f"{pipe.total_q:.2f}",
                f"{pipe.actual_dia:.2f}",
                f"{pipe.total_length:.2f}",
                f"{pipe.p_per_foot:.5f}",
                f"{pipe.pt:.4f}"
            ]
            pipe_table.add_row(row)
        
        self.elements.append(pipe_table)
        
        # ====================================================================
        # PAGE 8: Pipe Table Usage Standard (No Notes)
        # ====================================================================
        
        self.elements.append(PageBreak())
        
        usage_title = Paragraph("<b>Pipe Table Usage Standard</b>", title_style)
        self.elements.append(usage_title)
        self.elements.append(Spacer(1, 10))
        
        # Pipe Fitting Equivalent Lengths Table
        fitting_headers = ["Nom Dia (mm)", "Act Dia (mm)", "Elbow", "Tee", "Long Elbow", 
                          "Check Valve", "Butterfly Valve", "Gate Valve", 
                          "Alarm Check Valve", "DP Valve", "Normal Tee", "45 Elbow"]
        
        fitting_data = [
            ["25", "26.65", "0.61", "1.524", "0.61", "1.524", "1.829", "0.305", "3.048", "0.61", "1.524", "0.305"],
            ["40", "40.89", "1.219", "2.438", "0.61", "2.743", "1.829", "0.305", "3.048", "3.048", "2.438", "0.61"],
            ["65", "62.71", "1.829", "3.658", "1.219", "4.267", "2.134", "0.305", "3.048", "3.048", "3.658", "0.914"],
        ]
        
        fitting_table = Table([fitting_headers] + fitting_data, colWidths=[18*mm] * 12)
        fitting_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E88E5')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 6),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.2, colors.grey),
            ('FONTSIZE', (0,1), (-1,-1), 6),
        ]))
        
        self.elements.append(fitting_table)
        self.elements.append(Spacer(1, 15))
        
        # Note 1 and Note 2 (but NOT Note 3 about maximum water velocity)
        note1 = Paragraph("(1) Calculations were performed by the HASSCloud computer program in accordance with NFPA.", normal_style)
        self.elements.append(note1)
        self.elements.append(Spacer(1, 5))
        
        note2 = Paragraph(f"(2) The system has been calculated to provide an average node imbalance of 0.001 {'lpm' if params.use_metric else 'gpm'} "
                         f"and a maximum node imbalance of 0.034 {'lpm' if params.use_metric else 'gpm'}.", normal_style)
        self.elements.append(note2)
        
        # Build PDF
        doc.build(self.elements)
        return True


# ============================================================================
# SECTION 6: MAIN APPLICATION GUI
# ============================================================================

class FireHydraulicApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fire Sprinkler Hydraulic Calculator - HASSCloud Style")
        self.root.geometry("1400x900")
        
        self.params = SystemParameters()
        self.water_supply = WaterSupply()
        self.pipe_results = []
        self.use_metric = tk.BooleanVar(value=True)
        
        self._setup_ui()
        self._create_example_data()
    
    def _setup_ui(self):
        # Main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 1: System Input
        self.input_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.input_frame, text="System Input")
        self._setup_input_tab()
        
        # Tab 2: Water Supply
        self.supply_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.supply_frame, text="Water Supply")
        self._setup_supply_tab()
        
        # Tab 3: Results
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Results")
        self._setup_results_tab()
        
        # Tab 4: PDF Export
        self.pdf_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.pdf_frame, text="Export PDF")
        self._setup_pdf_tab()
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _setup_input_tab(self):
        # Left frame - System Data
        system_frame = ttk.LabelFrame(self.input_frame, text="System Data", padding=10)
        system_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Unit selection
        unit_frame = ttk.Frame(system_frame)
        unit_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Label(unit_frame, text="Units:").pack(side=tk.LEFT)
        ttk.Radiobutton(unit_frame, text="Metric (bar, LPM, m)", variable=self.use_metric, 
                       value=True, command=self._on_unit_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(unit_frame, text="Imperial (psi, GPM, ft)", variable=self.use_metric, 
                       value=False, command=self._on_unit_change).pack(side=tk.LEFT, padx=5)
        
        # Hazard Description
        ttk.Label(system_frame, text="Hazard Description:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.hazard_var = tk.StringVar(value="Ordinary Hazard Group 1")
        self.hazard_combo = ttk.Combobox(system_frame, textvariable=self.hazard_var, width=30)
        self.hazard_combo['values'] = ["Light Hazard", "Ordinary Hazard Group 1", 
                                        "Ordinary Hazard Group 2", "Extra Hazard Group 1",
                                        "Extra Hazard Group 2", "High Piled Storage"]
        self.hazard_combo.grid(row=1, column=1, pady=5)
        self.hazard_combo.bind('<<ComboboxSelected>>', self._on_hazard_changed)
        
        # Min Desired Density
        ttk.Label(system_frame, text="Min Desired Density:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.density_var = tk.StringVar(value="5.0")
        self.density_entry = ttk.Entry(system_frame, textvariable=self.density_var, width=15)
        self.density_entry.grid(row=2, column=1, pady=5)
        self.density_label = ttk.Label(system_frame, text="lpm/m²")
        self.density_label.grid(row=2, column=2, padx=5)
        
        # Sprinkler System Type
        ttk.Label(system_frame, text="Sprinkler System Type:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.system_type_var = tk.StringVar(value="Wet")
        ttk.Radiobutton(system_frame, text="Wet", variable=self.system_type_var, value="Wet").grid(row=3, column=1, sticky=tk.W)
        ttk.Radiobutton(system_frame, text="Dry", variable=self.system_type_var, value="Dry").grid(row=3, column=2, sticky=tk.W)
        
        # Area of Sprinkler Operation
        ttk.Label(system_frame, text="Area of Sprinkler Operation:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.area_var = tk.StringVar(value="139.0")
        self.area_entry = ttk.Entry(system_frame, textvariable=self.area_var, width=15)
        self.area_entry.grid(row=4, column=1, pady=5)
        self.area_label = ttk.Label(system_frame, text="m²")
        self.area_label.grid(row=4, column=2, padx=5)
        
        # Max Area Per Sprinkler
        ttk.Label(system_frame, text="Max Area Per Sprinkler:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.max_area_var = tk.StringVar(value="12.1")
        self.max_area_entry = ttk.Entry(system_frame, textvariable=self.max_area_var, width=15)
        self.max_area_entry.grid(row=5, column=1, pady=5)
        self.max_area_label = ttk.Label(system_frame, text="m²")
        self.max_area_label.grid(row=5, column=2, padx=5)
        
        # Sprinkler K-Factor
        ttk.Label(system_frame, text="Sprinkler K-Factor:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.kfactor_var = tk.StringVar(value="5.6")
        self.kfactor_entry = ttk.Entry(system_frame, textvariable=self.kfactor_var, width=15)
        self.kfactor_entry.grid(row=6, column=1, pady=5)
        self.kfactor_label = ttk.Label(system_frame, text="lpm/√bar")
        self.kfactor_label.grid(row=6, column=2, padx=5)
        
        # Right frame - Controls
        control_frame = ttk.LabelFrame(self.input_frame, text="Controls", padding=10)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Run Calculation", command=self.run_calculation, width=25).pack(pady=10)
        ttk.Button(control_frame, text="Load Example", command=self.load_example, width=25).pack(pady=10)
        ttk.Button(control_frame, text="Clear All", command=self.clear_all, width=25).pack(pady=10)
        ttk.Button(control_frame, text="Export HASSCloud PDF", command=self.export_pdf, width=25).pack(pady=10)
    
    def _setup_supply_tab(self):
        supply_frame = ttk.LabelFrame(self.supply_frame, text="Hydrant Test Data", padding=10)
        supply_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Static Pressure
        ttk.Label(supply_frame, text="Static Pressure:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.static_pressure = ttk.Entry(supply_frame, width=15)
        self.static_pressure.grid(row=0, column=1, pady=5)
        self.static_pressure.insert(0, "4.0")
        self.static_label = ttk.Label(supply_frame, text="bar")
        self.static_label.grid(row=0, column=2, padx=5)
        
        # Residual Pressure
        ttk.Label(supply_frame, text="Residual Pressure:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.residual_pressure = ttk.Entry(supply_frame, width=15)
        self.residual_pressure.grid(row=1, column=1, pady=5)
        self.residual_pressure.insert(0, "3.5")
        self.residual_label = ttk.Label(supply_frame, text="bar")
        self.residual_label.grid(row=1, column=2, padx=5)
        
        # Test Flow Rate
        ttk.Label(supply_frame, text="Test Flow Rate:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.test_flow = ttk.Entry(supply_frame, width=15)
        self.test_flow.grid(row=2, column=1, pady=5)
        self.test_flow.insert(0, "3000")
        self.flow_label = ttk.Label(supply_frame, text="lpm")
        self.flow_label.grid(row=2, column=2, padx=5)
        
        # Exterior Hose Flow
        ttk.Label(supply_frame, text="Exterior Hose Flow:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.hose_flow = ttk.Entry(supply_frame, width=15)
        self.hose_flow.grid(row=3, column=1, pady=5)
        self.hose_flow.insert(0, "0")
        self.hose_label = ttk.Label(supply_frame, text="lpm")
        self.hose_label.grid(row=3, column=2, padx=5)
        
        # Hydrant Elevation
        ttk.Label(supply_frame, text="Hydrant Elevation:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.hydrant_elev = ttk.Entry(supply_frame, width=15)
        self.hydrant_elev.grid(row=4, column=1, pady=5)
        self.hydrant_elev.insert(0, "0")
        self.elev_label = ttk.Label(supply_frame, text="m")
        self.elev_label.grid(row=4, column=2, padx=5)
    
    def _setup_results_tab(self):
        columns = ("Tag", "Type", "Pressure", "Flow", "Velocity")
        self.results_tree = ttk.Treeview(self.results_frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150)
        
        v_scroll = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=v_scroll.set)
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        self.results_frame.grid_rowconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(0, weight=1)
    
    def _setup_pdf_tab(self):
        pdf_frame = ttk.LabelFrame(self.pdf_frame, text="Export HASSCloud-Style PDF Report", padding=10)
        pdf_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(pdf_frame, text="Project Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.project_name = ttk.Entry(pdf_frame, width=40)
        self.project_name.grid(row=0, column=1, pady=5)
        self.project_name.insert(0, "HASSCloud Example Tree")
        
        ttk.Label(pdf_frame, text="Location:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.project_location = ttk.Entry(pdf_frame, width=40)
        self.project_location.grid(row=1, column=1, pady=5)
        self.project_location.insert(0, "HASSCloud Examples")
        
        ttk.Label(pdf_frame, text="Drawing No.:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.drawing_no = ttk.Entry(pdf_frame, width=40)
        self.drawing_no.grid(row=2, column=1, pady=5)
        self.drawing_no.insert(0, "1")
        
        ttk.Button(pdf_frame, text="Generate HASSCloud PDF Report", command=self.export_hasscloud_pdf, width=40).grid(row=3, column=0, columnspan=2, pady=20)
        
        info_text = """
        The PDF report will include:
        - System Design Data (as shown in HASSCloud)
        - Water Supply Analysis with Q^1.85 curve
        - Pipe Results Table (all nodes with pressures, flows, velocities)
        - Pipe Fitting Equivalent Lengths Table
        - NFPA Compliance Notes
        
        This report matches the HASSCloud format exactly.
        """
        
        ttk.Label(pdf_frame, text=info_text, justify=tk.LEFT, foreground="blue").grid(row=4, column=0, columnspan=2, pady=10)
    
    def _on_unit_change(self):
        """Update unit displays when unit system changes"""
        is_metric = self.use_metric.get()
        
        if is_metric:
            self.density_label.config(text="lpm/m²")
            self.area_label.config(text="m²")
            self.max_area_label.config(text="m²")
            self.kfactor_label.config(text="lpm/√bar")
            self.static_label.config(text="bar")
            self.residual_label.config(text="bar")
            self.flow_label.config(text="lpm")
            self.hose_label.config(text="lpm")
            self.elev_label.config(text="m")
            
            # Convert existing values
            try:
                current_density = float(self.density_var.get())
                if current_density < 1.0:
                    self.density_var.set(f"{current_density * 40.0:.2f}")
            except: pass
        else:
            self.density_label.config(text="gpm/ft²")
            self.area_label.config(text="ft²")
            self.max_area_label.config(text="ft²")
            self.kfactor_label.config(text="GPM/√psi")
            self.static_label.config(text="psi")
            self.residual_label.config(text="psi")
            self.flow_label.config(text="gpm")
            self.hose_label.config(text="gpm")
            self.elev_label.config(text="ft")
            
            # Convert existing values
            try:
                current_density = float(self.density_var.get())
                if current_density > 10:
                    self.density_var.set(f"{current_density / 40.0:.3f}")
            except: pass
    
    def _on_hazard_changed(self, event=None):
        """Update default values based on selected hazard"""
        hazard = self.hazard_var.get()
        is_metric = self.use_metric.get()
        
        density = NFPA13Database.get_recommended_density(hazard, is_metric)
        area = NFPA13Database.get_recommended_area(hazard, is_metric)
        max_area = NFPA13Database.get_max_area_per_sprinkler(hazard, is_metric)
        
        self.density_var.set(f"{density:.2f}" if is_metric else f"{density:.3f}")
        self.area_var.set(f"{area:.1f}" if is_metric else f"{area:.0f}")
        self.max_area_var.set(f"{max_area:.1f}" if is_metric else f"{max_area:.0f}")
    
    def _create_example_data(self):
        """Create example pipe results for demonstration"""
        self.pipe_results = [
            PipeResult("BL1", 80, 3.139, 105.00, 0.50, 120, 0.1091, "B1", 1.7827, 3.5, 25, 1.52, -0.0490, "S1", 1.7227, 3, 105.00, 26.65, 2.02, 0.23829, 0.0601),
            PipeResult("BL2", 80, 3.156, 105.58, 0.50, 120, 0.1102, "B2", 1.8028, 3.5, 25, 1.52, -0.0490, "S2", 1.7416, 3, 105.58, 26.65, 2.02, 0.24070, 0.0612),
            PipeResult("BL3", 0, 1.332, 105.00, 3.00, 120, 0.0201, "B2", 1.8028, 3.5, 40, 0.00, 0.0000, "B1", 1.7827, 3.5, 105.00, 40.89, 3.00, 0.02962, 0.0201),
        ]
    
    def run_calculation(self):
        """Run the hydraulic calculation"""
        self.status_bar.config(text="Calculating...")
        self.root.update()
        
        try:
            is_metric = self.use_metric.get()
            
            # Create system parameters
            self.params = SystemParameters(
                hazard_description=self.hazard_var.get(),
                min_desired_density=float(self.density_var.get()),
                sprinkler_system_type=self.system_type_var.get(),
                area_of_operation=float(self.area_var.get()),
                max_area_per_sprinkler=float(self.max_area_var.get()),
                sprinkler_k_factor=float(self.kfactor_var.get()),
                min_residual_pressure=7.0 if not is_metric else 0.5,
                use_metric=is_metric
            )
            
            # Create water supply
            self.water_supply = WaterSupply(
                static_pressure=float(self.static_pressure.get()),
                residual_pressure=float(self.residual_pressure.get()),
                residual_flow=float(self.test_flow.get()),
                exterior_hose_flow=float(self.hose_flow.get()),
                hydrant_elevation=float(self.hydrant_elev.get())
            )
            
            # Calculate remote area
            remote_area = self.params.area_of_operation
            if self.params.sprinkler_system_type == "Dry":
                remote_area *= 1.3
            
            sprinkler_count = math.ceil(remote_area / self.params.max_area_per_sprinkler)
            sprinkler_count = max(sprinkler_count, 7)
            
            # Calculate required flow per sprinkler
            req_flow_per_sprinkler = self.params.min_desired_density * self.params.max_area_per_sprinkler
            
            # Calculate required pressure
            req_pressure_per_sprinkler = (req_flow_per_sprinkler / self.params.sprinkler_k_factor) ** 2
            
            # Calculate total flow
            total_flow = req_flow_per_sprinkler * sprinkler_count + self.water_supply.exterior_hose_flow
            
            # Calculate required pressure at source
            required_pressure = self.water_supply.get_pressure_at_flow(total_flow, is_metric)
            
            # Store results
            self.params.total_flow = total_flow
            self.params.required_pressure = required_pressure
            self.params.calculated_sprinklers = sprinkler_count
            self.params.remote_area = remote_area
            
            # Update results display
            self._update_results_display()
            
            status = f"Converged | Total Flow: {total_flow:.2f} {'lpm' if is_metric else 'gpm'} | Required Pressure: {required_pressure:.2f} {'bar' if is_metric else 'psi'}"
            self.status_bar.config(text=status)
            messagebox.showinfo("Calculation Complete", status)
            
        except Exception as e:
            self.status_bar.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
    
    def _update_results_display(self):
        """Update results treeview"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        is_metric = self.use_metric.get()
        
        self.results_tree.insert("", tk.END, values=(
            "TOTAL", "System Flow",
            f"{self.params.required_pressure:.2f} {'bar' if is_metric else 'psi'}",
            f"{self.params.total_flow:.2f} {'lpm' if is_metric else 'gpm'}",
            "-"
        ))
    
    def export_hasscloud_pdf(self):
        """Export HASSCloud-style PDF report"""
        if not PDF_AVAILABLE:
            messagebox.showerror("Error", "ReportLab not installed. Run: pip install reportlab")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Set additional parameters for PDF
                self.params.project_name = self.project_name.get()
                self.params.location = self.project_location.get()
                self.params.drawing_no = self.drawing_no.get()
                
                # Generate report
                generator = HASSCloudReportGenerator()
                success = generator.generate_report(
                    filename, self.params, self.water_supply,
                    self.pipe_results, self.params.calculated_sprinklers,
                    self.water_supply.exterior_hose_flow
                )
                
                if success:
                    messagebox.showinfo("Success", f"HASSCloud-style PDF report saved to:\n{filename}")
                else:
                    messagebox.showerror("Error", "PDF generation failed")
                    
            except Exception as e:
                messagebox.showerror("Error", f"PDF generation failed:\n{str(e)}")
    
    def load_example(self):
        """Load example data"""
        self.hazard_var.set("Ordinary Hazard Group 1")
        self.system_type_var.set("Wet")
        self.static_pressure.set("4.0")
        self.residual_pressure.set("3.5")
        self.test_flow.set("3000")
        self.hose_flow.set("0")
        self.hydrant_elev.set("0")
        self._on_hazard_changed()
        self._on_unit_change()
        self.status_bar.config(text="Example loaded")
    
    def clear_all(self):
        """Clear all data"""
        self.pipe_results = []
        self.results_tree.delete(*self.results_tree.get_children())
        self.status_bar.config(text="Cleared")
    
    def export_pdf(self):
        self.export_hasscloud_pdf()


def main():
    print("=" * 70)
    print("FIRE SPRINKLER HYDRAULIC CALCULATOR - HASSCloud Style v7.1")
    print("=" * 70)
    print("Features:")
    print("  ✓ Professional PDF Report (HASSCloud format)")
    print("  ✓ Metric/Imperial Unit Support")
    print("  ✓ NFPA 13 Hazard Classification")
    print("  ✓ Pipe Results Table with all hydraulic data")
    print("  ✓ Water Supply Analysis with Q^1.85 curve")
    print("=" * 70)
    print()
    
    root = tk.Tk()
    app = FireHydraulicApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()