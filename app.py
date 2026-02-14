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
# PDF Generator (كما كان)
# =========================
def generate_pdf(mainbar_df, waste_df, purchase_df, cutting_df, price):
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    # ... نفس محتوى PDF السابق بدون تعديل هنا
    # في النهاية:
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

# زر Reset Project لمسح كل البيانات
if st.button("Reset Project"):
    for d in DIAMETERS:
        st.session_state[f"rows_{d}"] = [{"Length": 0.0, "Quantity": 0}]

# =========================
# إدخال البيانات لكل قطر
# =========================
data = {}
for d in DIAMETERS:
    if f"rows_{d}" not in st.session_state:
        st.session_state[f"rows_{d}"] = [{"Length": 0.0, "Quantity": 0}]
    with st.expander(f"Diameter {d} mm"):
        rows = st.session_state[f"rows_{d}"]
        for i, row in enumerate(rows):
            col1, col2 = st.columns(2)
            row["Length"] = col1.number_input(f"Length (m) [{i+1}]", value=float(row["Length"]), key=f"len_{d}_{i}")
            row["Quantity"] = col2.number_input(f"Quantity [{i+1}]", value=int(row["Quantity"]), min_value=0, key=f"qty_{d}_{i}")
        # عند الضغط على Add Row، يضيف صف جديد فقط بدون rerun
        if st.button(f"Add Row Ø{d}"):
            rows.append({"Length": 0.0, "Quantity": 0})

        # إعداد قائمة الأطوال لتسليمها للحساب
        lengths_list = []
        for r in rows:
            if r["Length"] > 0 and r["Quantity"] > 0:  # نتجاهل الصفوف الفارغة
                lengths_list.extend([r["Length"]] * r["Quantity"])
        if lengths_list:
            data[d] = lengths_list

# =========================
# Run Optimization
# =========================
if st.button("Run Optimization"):
    results = []
    waste_dict = defaultdict(lambda: {"count":0, "weight":0})
    purchase_list = []
    cutting_instr = []

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

    df_mainbar = pd.DataFrame(results, columns=["Diameter","Bars Used","Required Weight (kg)","Used Weight (kg)","Waste Weight (kg)","Waste %","Cost"])
    df_waste = pd.DataFrame([[diameter, waste_len, info["count"], info["weight"]] for (diameter,waste_len), info in waste_dict.items()],
                            columns=["Diameter","Waste Length (m)","Number of Bars","Waste Weight (kg)"])
    df_purchase = pd.DataFrame(purchase_list, columns=["Diameter","Bars","Weight (kg)","Cost"])
    df_cutting = pd.DataFrame(cutting_instr, columns=["Diameter","Pattern","Count"])

    st.success("Optimization Completed Successfully ✅")
    st.dataframe(df_mainbar)
    st.dataframe(df_waste)
    st.dataframe(df_purchase)
    st.dataframe(df_cutting)

    pdf_file = generate_pdf(df_mainbar, df_waste, df_purchase, df_cutting, price)
    with open(pdf_file,"rb") as f:
        st.download_button("Download PDF Report", data=f, file_name=pdf_file, mime="application/pdf")
