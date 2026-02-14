import streamlit as st
import random
import pandas as pd
from fpdf import FPDF
import datetime
from collections import defaultdict, Counter

# =========================
# Settings
# =========================
BAR_LENGTH = 12.0
ITERATIONS = 3000
DIAMETERS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 32]

# =========================
# Weight per meter
# =========================
def weight_per_meter(diameter):
    return (diameter ** 2) / 162

# =========================
# Cutting Optimization
# =========================
def optimize_cutting(lengths):
    best_solution = None
    min_waste = float("inf")
    min_bars = float("inf")

    for _ in range(ITERATIONS):
        shuffled = lengths[:]
        random.shuffle(shuffled)
        shuffled.sort(reverse=True)

        bars = []
        for length in shuffled:
            placed = False
            for bar in bars:
                if sum(bar) + length <= BAR_LENGTH:
                    bar.append(length)
                    placed = True
                    break
            if not placed:
                bars.append([length])

        waste = sum(BAR_LENGTH - sum(bar) for bar in bars)

        if waste < min_waste or (waste == min_waste and len(bars) < min_bars):
            min_waste = waste
            min_bars = len(bars)
            best_solution = bars

    return best_solution

# =========================
# PDF Generator
# =========================
def generate_pdf(main_df, waste_df, purchase_df, cutting_df):

    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Rebar Optimization Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Created by Civil Engineer Moustafa Harmouch", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.date.today()}", ln=True)
    pdf.ln(5)

    # =========================
    # MainBar
    # =========================
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "MainBar", ln=True)
    pdf.set_font("Arial", '', 9)

    col_main = [30, 35, 30, 35]
    headers_main = ["Diameter", "Length (m)", "Quantity", "Weight (kg)"]

    for i, h in enumerate(headers_main):
        pdf.cell(col_main[i], 8, h, 1, 0, "C")
    pdf.ln()

    total_main_weight = 0

    for _, row in main_df.iterrows():
        pdf.cell(col_main[0], 8, f"{int(row['Diameter'])} mm", 1, 0, "C")
        pdf.cell(col_main[1], 8, f"{row['Length']:.2f}", 1, 0, "C")
        pdf.cell(col_main[2], 8, f"{int(row['Quantity'])}", 1, 0, "C")
        pdf.cell(col_main[3], 8, f"{row['Weight']:.2f}", 1, 1, "C")
        total_main_weight += row["Weight"]

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(sum(col_main[:-1]), 8, "TOTAL", 1, 0, "C")
    pdf.cell(col_main[-1], 8, f"{total_main_weight:.2f}", 1, 1, "C")
    pdf.ln(10)

    # =========================
    # Waste Bars
    # =========================
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Waste Bars", ln=True)
    pdf.set_font("Arial", '', 9)

    col_waste = [30, 40, 40, 40]
    headers_waste = ["Diameter", "Waste Length (m)", "Number of Bars", "Waste Weight (kg)"]

    for i, h in enumerate(headers_waste):
        pdf.cell(col_waste[i], 8, h, 1, 0, "C")
    pdf.ln()

    total_waste_weight = waste_df["Waste Weight (kg)"].sum() if not waste_df.empty else 0

    for _, row in waste_df.iterrows():
        pdf.cell(col_waste[0], 8, f"{int(row['Diameter'])} mm", 1, 0, "C")
        pdf.cell(col_waste[1], 8, f"{row['Waste Length (m)']:.2f}", 1, 0, "C")
        pdf.cell(col_waste[2], 8, f"{int(row['Number of Bars'])}", 1, 0, "C")
        pdf.cell(col_waste[3], 8, f"{row['Waste Weight (kg)']:.2f}", 1, 1, "C")

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(sum(col_waste[:-1]), 8, "TOTAL", 1, 0, "C")
    pdf.cell(col_waste[-1], 8, f"{total_waste_weight:.2f}", 1, 1, "C")
    pdf.ln(10)

    # =========================
    # Purchase
    # =========================
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Purchase 12m Bars", ln=True)
    pdf.set_font("Arial", '', 9)

    col_purchase = [30, 35, 40, 40]
    headers_purchase = ["Diameter", "Bars", "Weight (kg)", "Cost"]

    for i, h in enumerate(headers_purchase):
        pdf.cell(col_purchase[i], 8, h, 1, 0, "C")
    pdf.ln()

    total_purchase_weight = purchase_df["Weight (kg)"].sum() if not purchase_df.empty else 0
    total_purchase_cost = purchase_df["Cost"].sum() if not purchase_df.empty else 0

    for _, row in purchase_df.iterrows():
        pdf.cell(col_purchase[0], 8, f"{int(row['Diameter'])} mm", 1, 0, "C")
        pdf.cell(col_purchase[1], 8, f"{int(row['Bars'])}", 1, 0, "C")
        pdf.cell(col_purchase[2], 8, f"{row['Weight (kg)']:.2f}", 1, 0, "C")
        pdf.cell(col_purchase[3], 8, f"{row['Cost']:.2f}", 1, 1, "C")

    pdf.set_font("Arial", 'B', 9)
    pdf.cell(sum(col_purchase[:-2]), 8, "TOTAL", 1, 0, "C")
    pdf.cell(col_purchase[-2], 8, f"{total_purchase_weight:.2f}", 1, 0, "C")
    pdf.cell(col_purchase[-1], 8, f"{total_purchase_cost:.2f}", 1, 1, "C")

    pdf.ln(10)

    # =========================
    # Cutting Instructions
    # =========================
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Cutting Instructions", ln=True)
    pdf.set_font("Arial", '', 8)

    col_cut = [30, 140, 30]
    headers_cut = ["Diameter", "Pattern (12m Bar Distribution)", "Count"]

    for i, h in enumerate(headers_cut):
        pdf.cell(col_cut[i], 8, h, 1, 0, "C")
    pdf.ln()

    for _, row in cutting_df.iterrows():
        pdf.cell(col_cut[0], 8, f"{int(row['Diameter'])} mm", 1, 0, "C")

        x = pdf.get_x()
        y = pdf.get_y()
        pdf.multi_cell(col_cut[1], 8, str(row["Pattern"]), 1)
        pdf.set_xy(x + col_cut[1], y)

        pdf.cell(col_cut[2], 8, f"{int(row['Count'])}", 1, 1, "C")

    pdf.ln(10)
    pdf.cell(0, 8, "Signature: ____________________", ln=True)

    filename = f"Rebar_Report_{datetime.date.today()}.pdf"
    pdf.output(filename)
    return filename
