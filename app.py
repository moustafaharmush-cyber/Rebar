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
def generate_pdf(mainbar_df, waste_df, purchase_df, cutting_instr_df, price):
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Rebar Optimization Report", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Created by Civil Engineer Moustafa Harmouch", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.date.today()}", ln=True)
    pdf.ln(5)

    # ----------------------
    # MainBar Table
    # ----------------------
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "MainBar - Input Bars", ln=True)
    pdf.set_font("Arial", '', 8)

    col_widths_main = [25, 35, 35, 35]
    headers_main = ["Diameter", "Length (m)", "Quantity", "Weight (kg)"]

    for i, header in enumerate(headers_main):
        pdf.cell(col_widths_main[i], 8, header, border=1, align="C")
    pdf.ln()

    total_weight = 0
    for _, row in mainbar_df.iterrows():
        pdf.cell(col_widths_main[0], 8, f"{int(row['Diameter'])} mm", border=1, align="C")
        pdf.cell(col_widths_main[1], 8, f"{row['Length']:.2f}", border=1, align="C")
        pdf.cell(col_widths_main[2], 8, f"{int(row['Quantity'])}", border=1, align="C")
        pdf.cell(col_widths_main[3], 8, f"{row['Weight']:.2f}", border=1, align="C")
        pdf.ln()
        total_weight += row['Weight']

    pdf.set_font("Arial", 'B', 8)
    pdf.cell(col_widths_main[0]+col_widths_main[1]+col_widths_main[2], 8, "TOTAL", border=1, align="C")
    pdf.cell(col_widths_main[3], 8, f"{total_weight:.2f}", border=1, align="C")
    pdf.ln(10)

    # ----------------------
    # Waste Table
    # ----------------------
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Detailed Waste Report", ln=True)
    pdf.set_font("Arial", '', 8)
    col_widths_waste = [25, 35, 25, 35]
    headers_waste = ["Diameter", "Waste Length (m)", "Number of Bars", "Waste Weight (kg)"]
    for i, header in enumerate(headers_waste):
        pdf.cell(col_widths_waste[i], 8, header, border=1, align="C")
    pdf.ln()
    total_waste_weight = 0
    for _, row in waste_df.iterrows():
        pdf.cell(col_widths_waste[0], 8, f"{int(row['Diameter'])} mm", border=1, align="C")
        pdf.cell(col_widths_waste[1], 8, f"{row['Waste Length (m)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_waste[2], 8, f"{int(row['Number of Bars'])}", border=1, align="C")
        pdf.cell(col_widths_waste[3], 8, f"{row['Waste Weight (kg)']:.2f}", border=1, align="C")
        pdf.ln()
        total_waste_weight += row['Waste Weight (kg)']
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(col_widths_waste[0]+col_widths_waste[1]+col_widths_waste[2], 8, "TOTAL", border=1, align="C")
    pdf.cell(col_widths_waste[3], 8, f"{total_waste_weight:.2f}", border=1, align="C")
    pdf.ln(10)

    # ----------------------
    # Purchase Table
    # ----------------------
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Purchase Summary (12m Bars)", ln=True)
    pdf.set_font("Arial", '', 8)
    col_widths_purchase = [25, 25, 35, 35]
    headers_purchase = ["Diameter", "Number of Bars", "Weight (kg)", "Cost ($)"]
    for i, header in enumerate(headers_purchase):
        pdf.cell(col_widths_purchase[i], 8, header, border=1, align="C")
    pdf.ln()
    total_purchase_weight = 0
    total_purchase_cost = 0
    for _, row in purchase_df.iterrows():
        pdf.cell(col_widths_purchase[0], 8, f"{int(row['Diameter'])} mm", border=1, align="C")
        pdf.cell(col_widths_purchase[1], 8, f"{int(row['Bars'])}", border=1, align="C")
        pdf.cell(col_widths_purchase[2], 8, f"{row['Weight (kg)']:.2f}", border=1, align="C")
        pdf.cell(col_widths_purchase[3], 8, f"{row['Cost']:.2f}", border=1, align="C")
        pdf.ln()
        total_purchase_weight += row['Weight (kg)']
        total_purchase_cost += row['Cost']
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(col_widths_purchase[0]+col_widths_purchase[1], 8, "TOTAL", border=1, align="C")
    pdf.cell(col_widths_purchase[2], 8, f"{total_purchase_weight:.2f}", border=1, align="C")
    pdf.cell(col_widths_purchase[3], 8, f"{total_purchase_cost:.2f}", border=1, align="C")
    pdf.ln(10)

    # ----------------------
    # Cutting Instructions
    # ----------------------
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "Cutting Instructions", ln=True)
    pdf.set_font("Arial", '', 8)
    for _, row in cutting_instr_df.iterrows():
        pdf.cell(0, 8, f"Diameter {int(row['Diameter'])} mm: {row['Pattern']} x {row['Count']} bars", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Signature: ____________________", ln=True)

    filename = f"Rebar_Report_{datetime.date.today()}.pdf"
    pdf.output(filename)
    return filename

# =========================
# Streamlit Interface
# =========================
st.set_page_config(layout="wide")
st.title("Rebar Optimizer Pro")
st.subheader("Created by Civil Engineer Moustafa Harmouch")

# --- Price Input ---
price = st.number_input("Price per ton ($)", min_value=0.0, value=1000.0)

# --- Reset Project ---
if st.button("Reset Project"):
    for d in DIAMETERS:
        st.session_state[f"rows_{d}"] = [{"Length":0.0,"Quantity":0}]
    st.experimental_rerun()

# --- Input Bars ---
data = {}
for d in DIAMETERS:
    if f"rows_{d}" not in st.session_state:
        st.session_state[f"rows_{d}"] = [{"Length":0.0,"Quantity":0}]
    with st.expander(f"Diameter {d} mm"):
        rows = st.session_state[f"rows_{d}"]
        for i, r in enumerate(rows):
            col1, col2 = st.columns(2)
            r["Length"] = col1.number_input(f"Length (m) [{i+1}]", value=r["Length"], key=f"len_{d}_{i}")
            r["Quantity"] = col2.number_input(f"Quantity [{i+1}]", value=r["Quantity"], min_value=0, key=f"qty_{d}_{i}")

        if st.button(f"Add Row Ø{d}"):
            st.session_state[f"rows_{d}"].append({"Length":0.0,"Quantity":0})

        # Collect valid lengths
        lengths_list = []
        for r in rows:
            if r["Length"]>0 and r["Quantity"]>0:
                lengths_list.extend([r["Length"]]*r["Quantity"])
        if lengths_list:
            data[d] = lengths_list

# --- Run Optimization ---
if st.button("Run Optimization"):
    results = []
    waste_dict = defaultdict(lambda: {"count":0, "weight":0})
    purchase_list = []
    cutting_instr = []
    mainbar_data = []

    for d, lengths in data.items():
        solution = optimize_cutting(lengths)
        if not solution:
            continue
        total_required = sum(lengths)
        used_bars = len(solution)
        total_bar_length = used_bars * BAR_LENGTH
        wpm = weight_per_meter(d)
        required_weight = total_required * wpm
        used_weight = total_bar_length * wpm
        waste_weight = (total_bar_length - total_required) * wpm
        waste_percent = ((total_bar_length - total_required)/total_bar_length)*100
        cost = (used_weight/1000)*price
        results.append([d, used_bars, required_weight, used_weight, waste_weight, waste_percent, cost])

        # Waste per bar
        for bar in solution:
            bar_total_length = sum(bar)
            bar_waste = BAR_LENGTH - bar_total_length
            if bar_waste>0:
                key = (d, round(bar_waste,6))
                waste_dict[key]["count"] +=1
                waste_dict[key]["weight"] += bar_waste*wpm

        # Purchase summary
        purchase_list.append([d, used_bars, used_weight, cost])

        # Cutting instructions aggregation per diameter
        pattern_counts = Counter(tuple(bar) for bar in solution)
        for pattern, count in pattern_counts.items():
            pattern_str = ' + '.join([f"{l:.2f} m" for l in pattern])
            cutting_instr.append([d, pattern_str, count])

        # --- Prepare MainBar Data ---
        # Combine same diameter & length rows
        row_counter = Counter()
        for r in st.session_state[f"rows_{d}"]:
            if r["Length"]>0 and r["Quantity"]>0:
                key = r["Length"]
                row_counter[key] += r["Quantity"]
        for length, qty in row_counter.items():
            mainbar_data.append({
                "Diameter": d,
                "Length": length,
                "Quantity": qty,
                "Weight": length*qty*wpm
            })

    # --- Convert to DataFrames ---
    mainbar_df = pd.DataFrame(mainbar_data)
    df = pd.DataFrame(results, columns=["Diameter","Bars Used","Required Weight (kg)","Used Weight (kg)","Waste Weight (kg)","Waste %","Cost"])
    waste_data = []
    for (diameter,waste_length), info in waste_dict.items():
        waste_data.append([diameter, waste_length, info["count"], info["weight"]])
    df_waste = pd.DataFrame(waste_data, columns=["Diameter","Waste Length (m)","Number of Bars","Waste Weight (kg)"])
    df_purchase = pd.DataFrame(purchase_list, columns=["Diameter","Bars","Weight (kg)","Cost"])
    df_cutting = pd.DataFrame(cutting_instr, columns=["Diameter","Pattern","Count"])

    # --- Display Results ---
    st.success("Optimization Completed Successfully ✅")
    st.markdown("### MainBar")
    st.dataframe(mainbar_df.style.format({"Length":"{:.2f}","Weight":"{:.2f}"}))
    st.markdown("### Detailed Waste Report")
    st.dataframe(df_waste.style.format({"Waste Length (m)":"{:.2f}","Waste Weight (kg)":"{:.2f}"}))
    st.markdown("### Purchase Summary")
    st.dataframe(df_purchase.style.format({"Weight (kg)":"{:.2f}","Cost":"{:.2f}"}))
    st.markdown("### Cutting Instructions")
    st.dataframe(df_cutting)

    # --- Generate PDF ---
    pdf_file = generate_pdf(mainbar_df, df_waste, df_purchase, df_cutting, price)
    with open(pdf_file,"rb") as f:
        st.download_button("Download PDF Report", data=f, file_name=pdf_file, mime="application/pdf")
