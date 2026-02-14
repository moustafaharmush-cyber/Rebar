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
def generate_pdf(main_df, waste_df, purchase_df, cutting_df, price):
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
    pdf.cell(0, 8, "MainBar", ln=True)
    pdf.set_font("Arial", '', 8)

    col_widths_main = [25, 35, 25, 35]
    headers_main = ["Diameter", "Length (m)", "Quantity", "Weight (kg)"]

    for i, header in enumerate(headers_main):
        pdf.cell(col_widths_main[i], 8, header, border=1, align="C")
    pdf.ln()

    total_weight = 0
    for _, row in main_df.iterrows():
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
    # Remaining Tables (Waste, Purchase, Cutting)
    # ----------------------
    for title, df_table in zip(
        ["WestBar", "Purchase 12m Bars", "Cutting Instructions"],
        [waste_df, purchase_df, cutting_df]
    ):
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, title, ln=True)
        pdf.set_font("Arial", '', 8)
        pdf.ln(2)
        for col in df_table.columns:
            pdf.cell(40, 8, str(col), border=1, align="C")
        pdf.ln()
        for _, row in df_table.iterrows():
            for col in df_table.columns:
                pdf.cell(40, 8, str(row[col]), border=1, align="C")
            pdf.ln()
        pdf.ln(5)

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

price = st.number_input("Price per ton ($)", min_value=0.0, value=1000.0)

# -------- Reset Project --------
if st.button("Reset Project"):
    for d in DIAMETERS:
        if f"rows_{d}" in st.session_state:
            del st.session_state[f"rows_{d}"]
    st.experimental_rerun()

# -------- Input Section --------
data = {}
for d in DIAMETERS:
    if f"rows_{d}" not in st.session_state:
        st.session_state[f"rows_{d}"] = [{"Length": 0.0, "Quantity": 0}]
    with st.expander(f"Diameter {d} mm"):
        rows = st.session_state[f"rows_{d}"]
        for i in range(len(rows)):
            col1, col2 = st.columns(2)
            rows[i]["Length"] = col1.number_input(f"Length (m) [{i+1}]", value=float(rows[i]["Length"]), key=f"len_{d}_{i}")
            rows[i]["Quantity"] = col2.number_input(f"Quantity [{i+1}]", value=int(rows[i]["Quantity"]), min_value=0, key=f"qty_{d}_{i}")
        if st.button(f"Add Row Ø{d}", key=f"addrow_{d}"):
            st.session_state[f"rows_{d}"].append({"Length": 0.0, "Quantity": 0})

        # جمع البيانات بعد كل expander
        lengths_list = []
        for r in rows:
            if r["Length"] > 0 and r["Quantity"] > 0:
                lengths_list.extend([r["Length"]] * r["Quantity"])
        if lengths_list:
            data[d] = lengths_list

# -------- Run Optimization --------
if st.button("Run Optimization"):
    # --------- MainBar DataFrame ---------
    main_rows = []
    for d, rows in st.session_state.items():
        if d.startswith("rows_"):
            diameter = int(d.split("_")[1])
            for r in rows:
                if r["Length"] > 0 and r["Quantity"] > 0:
                    weight = r["Length"] * r["Quantity"] * weight_per_meter(diameter)
                    main_rows.append({
                        "Diameter": diameter,
                        "Length": r["Length"],
                        "Quantity": r["Quantity"],
                        "Weight": round(weight, 2)
                    })
    main_df = pd.DataFrame(main_rows)
    if not main_df.empty:
        main_df = main_df.groupby(["Diameter","Length"]).agg({"Quantity":"sum","Weight":"sum"}).reset_index()

    # --------- Optimization Calculations ---------
    results = []
    waste_dict = defaultdict(lambda: {"count":0, "weight":0})
    purchase_list = []
    cutting_instr = []

    for d, lengths in data.items():
        solution = optimize_cutting(lengths)
        if not solution:
            continue
        used_bars = len(solution)
        total_bar_length = used_bars * BAR_LENGTH
        wpm = weight_per_meter(d)
        used_weight = total_bar_length * wpm
        cost = (used_weight/1000)*price
        purchase_list.append([d, used_bars, round(used_weight,2), round(cost,2)])

        # Waste per bar
        for bar in solution:
            bar_waste = BAR_LENGTH - sum(bar)
            if bar_waste > 0:
                key = (d, round(bar_waste,2))
                waste_dict[key]["count"] +=1
                waste_dict[key]["weight"] += bar_waste*wpm

        # Cutting instructions
        pattern_counts = Counter(tuple(bar) for bar in solution)
        for pattern, count in pattern_counts.items():
            pattern_str = ' + '.join([f"{l:.2f} m" for l in pattern])
            cutting_instr.append([d, pattern_str, count])

    waste_data = []
    for (diameter,waste_length), info in waste_dict.items():
        waste_data.append([diameter, waste_length, info["count"], round(info["weight"],2)])
    waste_df = pd.DataFrame(waste_data, columns=["Diameter","Waste Length (m)","Number of Bars","Waste Weight (kg)"])
    purchase_df = pd.DataFrame(purchase_list, columns=["Diameter","Bars","Weight (kg)","Cost"])
    cutting_df = pd.DataFrame(cutting_instr, columns=["Diameter","Pattern","Count"])

    # --------- Display Tables ---------
    st.success("Optimization Completed Successfully ✅")
    st.markdown("### MainBar")
    st.dataframe(main_df)
    st.markdown("### WestBar")
    st.dataframe(waste_df)
    st.markdown("### Purchase 12m Bars")
    st.dataframe(purchase_df)
    st.markdown("### Cutting Instructions")
    st.dataframe(cutting_df)

    # --------- Generate PDF ---------
    pdf_file = generate_pdf(main_df, waste_df, purchase_df, cutting_df, price)
    with open(pdf_file,"rb") as f:
        st.download_button("Download PDF Report", data=f, file_name=pdf_file, mime="application/pdf")
