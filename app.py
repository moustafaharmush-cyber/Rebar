import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
from collections import Counter
import pulp

# =========================
# دالة ILP لتحسين القص
# =========================
def optimize_cutting_ilp(lengths, stock_length=12.0):
    lengths_count = Counter(lengths)
    unique_lengths = sorted(lengths_count.keys())
    
    patterns = []
    def generate_patterns(current_pattern=[], remaining_lengths=unique_lengths, remaining_stock=stock_length):
        for l in remaining_lengths:
            if lengths_count[l] > current_pattern.count(l) and remaining_stock >= l:
                new_pattern = current_pattern + [l]
                patterns.append(new_pattern)
                generate_patterns(new_pattern, remaining_lengths, remaining_stock - l)
    generate_patterns()
    
    unique_patterns = []
    seen = set()
    for p in patterns:
        t = tuple(sorted(p))
        if t not in seen:
            seen.add(t)
            unique_patterns.append(p)
    
    prob = pulp.LpProblem("Cutting_Stock", pulp.LpMinimize)
    pattern_vars = [pulp.LpVariable(f'Pattern_{i}', lowBound=0, cat='Integer') 
                    for i in range(len(unique_patterns))]
    prob += pulp.lpSum(pattern_vars)
    
    for l in unique_lengths:
        prob += pulp.lpSum(pattern_vars[i]*unique_patterns[i].count(l) for i in range(len(unique_patterns))) >= lengths_count[l]
    
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    solution = []
    for i, var in enumerate(pattern_vars):
        if var.varValue > 0:
            for _ in range(int(var.varValue)):
                solution.append(unique_patterns[i])
    return solution

# =========================
# دالة توليد PDF
# =========================
def generate_pdf(input_df, waste_df, purchase_df, cutting_instr_df, total_input_weight, total_waste_weight, total_purchase_weight, total_purchase_cost):
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ------------------------
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Rebar Optimization Report", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Created by Civil Engineer Moustafa Harmouch", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.date.today()}", ln=True)
    pdf.ln(10)

    # ------------------------
    # MainBar
    input_df = input_df.sort_values(by=["Diameter", "Length (m)"]).reset_index(drop=True)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "MainBar (Input Bars)", ln=True)
    pdf.set_font("Arial", 'B', 9)
    col_widths_main = [35, 35, 35, 40]
    headers_main = ["Diameter (mm)", "Length (m)", "Quantity", "Weight (kg)"]
    for i, header in enumerate(headers_main):
        pdf.cell(col_widths_main[i], 8, header, border=1, align="C")
    pdf.ln()
    pdf.set_font("Arial", '', 9)
    for _, row in input_df.iterrows():
        pdf.cell(col_widths_main[0], 8, f"{int(row['Diameter'])}", border=1, align="C")
        pdf.cell(col_widths_main[1], 8, f"{row['Length (m)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_main[2], 8, f"{int(row['Quantity'])}", border=1, align="C")
        pdf.cell(col_widths_main[3], 8, f"{row['Weight (kg)']:.2f}", border=1, align="C")
        pdf.ln()
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(col_widths_main[0]+col_widths_main[1]+col_widths_main[2], 8, "Total Weight (kg)", border=1, align="C")
    pdf.cell(col_widths_main[3], 8, f"{total_input_weight:.2f}", border=1, align="C")
    pdf.ln(12)

    # ------------------------
    # WasteBar
    waste_df = waste_df.sort_values(by=["Diameter", "Waste Length (m)"]).reset_index(drop=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "WasteBar (Wasted Bars)", ln=True)
    pdf.set_font("Arial", '', 9)
    col_widths_waste = [35, 35, 35, 40]
    headers_waste = ["Diameter (mm)", "Waste Length (m)", "Quantity", "Waste Weight (kg)"]
    for i, header in enumerate(headers_waste):
        pdf.cell(col_widths_waste[i], 8, header, border=1, align="C")
    pdf.ln()
    for _, row in waste_df.iterrows():
        pdf.cell(col_widths_waste[0], 8, f"{int(row['Diameter'])}", border=1, align="C")
        pdf.cell(col_widths_waste[1], 8, f"{row['Waste Length (m)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_waste[2], 8, f"{int(row['Number of Bars'])}", border=1, align="C")
        pdf.cell(col_widths_waste[3], 8, f"{row['Waste Weight (kg)']:.2f}", border=1, align="C")
        pdf.ln()
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(col_widths_waste[0]+col_widths_waste[1]+col_widths_waste[2], 8, "Total Waste Weight (kg)", border=1, align="C")
    pdf.cell(col_widths_waste[3], 8, f"{total_waste_weight:.2f}", border=1, align="C")
    pdf.ln(12)

    # ------------------------
    # PurchaseBar
    purchase_df = purchase_df.sort_values(by=["Diameter"]).reset_index(drop=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "PurchaseBar (12m Bars to Buy)", ln=True)
    pdf.set_font("Arial", '', 9)
    col_widths_purchase = [35, 40, 35, 40]
    headers_purchase = ["Diameter (mm)", "Number of 12m Bars", "Weight (kg)", "Cost ($)"]
    for i, header in enumerate(headers_purchase):
        pdf.cell(col_widths_purchase[i], 8, header, border=1, align="C")
    pdf.ln()
    for _, row in purchase_df.iterrows():
        pdf.cell(col_widths_purchase[0], 8, f"{int(row['Diameter'])}", border=1, align="C")
        pdf.cell(col_widths_purchase[1], 8, f"{int(row['Bars'])}", border=1, align="C")
        pdf.cell(col_widths_purchase[2], 8, f"{row['Weight (kg)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_purchase[3], 8, f"{row['Cost']:.2f}", border=1, align="C")
        pdf.ln()
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(col_widths_purchase[0], 8, "Total", border=1, align="C")
    pdf.cell(col_widths_purchase[1], 8, "", border=1, align="C")
    pdf.cell(col_widths_purchase[2], 8, f"{total_purchase_weight:.2f}", border=1, align="C")
    pdf.cell(col_widths_purchase[3], 8, f"{total_purchase_cost:.2f}", border=1, align="C")
    pdf.ln(12)

    # ------------------------
    # Cutting Instructions
    cutting_instr_df = cutting_instr_df.sort_values(by=["Diameter"]).reset_index(drop=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Cutting Instructions per 12m Bar (ILP Optimized)", ln=True)
    pdf.set_font("Arial", '', 9)
    col_widths_cut = [35, 160, 35]
    headers_cut = ["Diameter (mm)", "Cutting Pattern (m)", "Number of 12m Bars"]
    for i, header in enumerate(headers_cut):
        pdf.cell(col_widths_cut[i], 8, header, border=1, align="C")
    pdf.ln()
    for _, row in cutting_instr_df.iterrows():
        pdf.cell(col_widths_cut[0], 8, f"{int(row['Diameter'])}", border=1, align="C")
        pdf.cell(col_widths_cut[1], 8, f"{row['Pattern']}", border=1, align="C")
        pdf.cell(col_widths_cut[2], 8, f"{int(row['Count'])}", border=1, align="C")
        pdf.ln()

    pdf.ln(10)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Signature: ____________________", ln=True)

    pdf_file = "Rebar_Optimization_Report.pdf"
    pdf.output(pdf_file)
    return pdf_file

# =========================
# Streamlit UI
# =========================
st.title("Rebar Optimizer Pro")
st.subheader("Created by Civil Engineer Moustafa Harmouch")

# أسعار الحديد
price = st.number_input("Price per ton ($)", min_value=0.0, value=1000.0)

# إدخال الأطوال لكل قطر
data_dict = {}
DIAMETERS = [8, 10, 12, 16, 20, 25]  # أمثلة
for d in DIAMETERS:
    lengths_text = st.text_area(f"Enter lengths for {d} mm (comma separated)", key=f"lengths_{d}")
    if lengths_text:
        lengths_list = [float(x.strip()) for x in lengths_text.split(",") if x.strip()]
        if lengths_list:
            data_dict[d] = lengths_list

if st.button("Run Optimization"):
    # تجهيز MainBar
    input_rows = []
    for d, lengths in data_dict.items():
        for l in lengths:
            qty = 1
            weight = l * 0.617 * d*d  # مثال على الوزن بالكيغرام (يمكنك تعديل الصيغة حسب الحديد)
            input_rows.append([d, l, qty, weight])
    input_df = pd.DataFrame(input_rows, columns=["Diameter","Length (m)","Quantity","Weight (kg)"])
    total_input_weight = input_df["Weight (kg)"].sum()

    # تجهيز WasteBar (هدر تقريبياً)
    waste_rows = []
    for d, lengths in data_dict.items():
        for l in lengths:
            waste_rows.append([d, l*0.1, 1, l*0.1*0.617*d*d])  # مثال على الهدر 10% تقريبا
    waste_df = pd.DataFrame(waste_rows, columns=["Diameter","Waste Length (m)","Number of Bars","Waste Weight (kg)"])
    total_waste_weight = waste_df["Waste Weight (kg)"].sum()

    # تجهيز PurchaseBar
    purchase_rows = []
    for d, lengths in data_dict.items():
        total_length = sum(lengths)
        used_weight = total_length * 0.617 * d*d
        bars_needed = int((total_length/12) + 0.999)  # تقريب لأعلى
        cost = used_weight/1000*price
        purchase_rows.append([d, bars_needed, used_weight, cost])
    purchase_df = pd.DataFrame(purchase_rows, columns=["Diameter","Bars","Weight (kg)","Cost"])
    total_purchase_weight = purchase_df["Weight (kg)"].sum()
    total_purchase_cost = purchase_df["Cost"].sum()

    # تجهيز Cutting Instructions
    cutting_rows = []
    for d, lengths in data_dict.items():
        solution = optimize_cutting_ilp(lengths)
        pattern_counts = Counter(tuple(bar) for bar in solution)
        for pattern, count in pattern_counts.items():
            pattern_str = ' + '.join([f"{l:.2f}" for l in pattern])
            cutting_rows.append([d, pattern_str, count])
    cutting_df = pd.DataFrame(cutting_rows, columns=["Diameter","Pattern","Count"])

    # عرض الجداول على Streamlit
    st.markdown("### MainBar (Input Bars)")
    st.dataframe(input_df)
    st.markdown("### WasteBar (Wasted Bars)")
    st.dataframe(waste_df)
    st.markdown("### PurchaseBar (12m Bars)")
    st.dataframe(purchase_df)
    st.markdown("### Cutting Instructions (ILP Optimized)")
    st.dataframe(cutting_df)

    # إنشاء PDF
    pdf_file = generate_pdf(input_df, waste_df, purchase_df, cutting_df, total_input_weight, total_waste_weight, total_purchase_weight, total_purchase_cost)
    with open(pdf_file, "rb") as f:
        st.download_button("Download PDF Report", data=f, file_name=pdf_file, mime="application/pdf")
