import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
from collections import Counter
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpInteger

# =========================
# Settings
DIAMETERS = [8, 10, 12]
wpm_dict = {8: 0.395, 10: 0.617, 12: 0.888}  # kg/m
BAR_LENGTH = 12.0

# =========================
# Streamlit Interface
st.title("Rebar Optimizer Pro - Accurate ILP")
st.subheader("Created by Civil Engineer Moustafa Harmouch")

price = st.number_input("Price per ton ($)", min_value=0.0, value=1000.0)

# =========================
# إدخال الأطوال وعدد الأسياخ لكل قطر
for d in DIAMETERS:
    if f"rows_{d}" not in st.session_state:
        st.session_state[f"rows_{d}"] = []

st.header("إدخال أطوال الأسياخ لكل قطر")

for d in DIAMETERS:
    st.subheader(f"القطر {d} mm")
    length = st.number_input(f"أدخل طول السيخ (متر) للقطر {d}", min_value=0.1, value=1.0, step=0.1, key=f"length_{d}")
    quantity = st.number_input(f"أدخل عدد الأسياخ لهذا الطول للقطر {d}", min_value=1, value=1, step=1, key=f"qty_{d}")
    
    if st.button(f"Add length for {d}mm"):
        st.session_state[f"rows_{d}"].append((length, quantity))
    
    if st.session_state[f"rows_{d}"]:
        st.write("Current entries:", st.session_state[f"rows_{d}"])

# =========================
# ILP Optimization Function (Cutting Stock Problem)
def optimize_cutting_ilp(length_qty_list):
    """
    length_qty_list: [(length, quantity), ...]
    Returns:
        patterns_per_bar: list of lists, كل قائمة تمثل طول الأسياخ داخل قضيب 12 متر
        waste_per_bar: list of الهدر لكل قضيب
    """
    # توليد قائمة كل الأسياخ مع تكرارها
    lengths = []
    for l, q in length_qty_list:
        lengths.extend([l]*q)
    
    n = len(lengths)
    max_bars = n  # أقصى عدد قضبان (worst case)
    
    prob = LpProblem("CuttingStock", LpMinimize)
    
    # متغيرات: x[i][j] = 1 إذا وضعت طول i في القضيب j
    x = [[LpVariable(f"x_{i}_{j}", cat=LpInteger, lowBound=0, upBound=1) for j in range(max_bars)] for i in range(n)]
    y = [LpVariable(f"y_{j}", cat=LpInteger, lowBound=0, upBound=1) for j in range(max_bars)]
    
    # كل طول يجب أن يوضع مرة واحدة
    for i in range(n):
        prob += lpSum([x[i][j] for j in range(max_bars)]) == 1
    
    # مجموع الأطوال داخل كل قضيب ≤ 12 متر
    for j in range(max_bars):
        prob += lpSum([lengths[i]*x[i][j] for i in range(n)]) <= BAR_LENGTH * y[j]
    
    # الهدف: تقليل عدد القضبان المستخدمة
    prob += lpSum([y[j] for j in range(max_bars)])
    
    prob.solve()
    
    # استخراج النتائج
    patterns = []
    waste_list = []
    for j in range(max_bars):
        bar = []
        total_length = 0
        for i in range(n):
            if x[i][j].varValue > 0.5:
                bar.append(lengths[i])
                total_length += lengths[i]
        if bar:
            patterns.append(bar)
            waste_list.append(BAR_LENGTH - total_length)
    
    return patterns, waste_list

# =========================
# Run Optimization
if st.button("Run Optimization"):

    mainbar_data = []
    waste_data = []
    purchase_data = []
    cutting_data = []

    for d in DIAMETERS:
        length_qty = st.session_state[f"rows_{d}"]
        if not length_qty:
            continue
        
        # MainBar
        for l, q in length_qty:
            w = l * q * wpm_dict[d]
            mainbar_data.append([d, l, q, w])
        df_main = pd.DataFrame(mainbar_data, columns=["Diameter", "Length", "Quantity", "Weight"])
        df_main.sort_values("Diameter", inplace=True)

        # ILP Optimization لكل قطر
        patterns, waste_list = optimize_cutting_ilp(length_qty)
        
        # WasteBar
        for bar, waste in zip(patterns, waste_list):
            weight_waste = waste * wpm_dict[d]
            waste_data.append([d, round(sum(bar),2), len(bar), round(weight_waste,2)])
        
        # PurchaseBar
        for bar in patterns:
            total_weight = sum(bar)*wpm_dict[d]
            cost = total_weight/1000*price
            purchase_data.append([d, 1, total_weight, cost])
        
        # Cutting Instructions
        pattern_counts = Counter(tuple(bar) for bar in patterns)
        for pattern, count in pattern_counts.items():
            pattern_str = " + ".join([f"{l:.2f} m" for l in pattern])
            cutting_data.append([d, pattern_str, count])

    # تحويل إلى DataFrames
    df_waste = pd.DataFrame(waste_data, columns=["Diameter","Waste Length (m)","Quantity","Weight (kg)"])
    df_waste.sort_values("Diameter", inplace=True)
    df_purchase = pd.DataFrame(purchase_data, columns=["Diameter","Bars","Weight (kg)","Cost"])
    df_purchase.sort_values("Diameter", inplace=True)
    df_cutting = pd.DataFrame(cutting_data, columns=["Diameter","Pattern","Count"])
    df_cutting.sort_values("Diameter", inplace=True)

    # عرض النتائج
    st.success("Optimization Completed Successfully ✅")
    st.markdown("### MainBar")
    st.dataframe(df_main)
    st.markdown("### WasteBar")
    st.dataframe(df_waste)
    st.markdown("### PurchaseBar")
    st.dataframe(df_purchase)
    st.markdown("### Cutting Instructions")
    st.dataframe(df_cutting)

    # =========================
    # PDF Generation
    def generate_pdf(df_main, df_waste, df_purchase, df_cutting, price):
        pdf = FPDF(orientation='L')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Rebar Optimization Report", ln=True, align="C")
        pdf.ln(5)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, "Created by Civil Engineer Moustafa Harmouch", ln=True)
        pdf.cell(0, 8, f"Date: {datetime.date.today()}", ln=True)
        pdf.ln(10)

        # يمكن إضافة جميع الجداول هنا كما في الكود السابق
        file_name = "Rebar_Report.pdf"
        pdf.output(file_name)
        return file_name

    pdf_file = generate_pdf(df_main, df_waste, df_purchase, df_cutting, price)
    with open(pdf_file, "rb") as f:
        st.download_button("Download PDF Report", data=f, file_name=pdf_file, mime="application/pdf")
