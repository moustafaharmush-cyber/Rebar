import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
from collections import Counter
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpInteger, PULP_CBC_CMD

# =========================
# Settings
DIAMETERS = [8,10,12,14,16,18,20,22,25,32]
wpm_dict = {
    8:0.395, 10:0.617, 12:0.888, 14:1.21, 16:1.58,
    18:2.0, 20:2.47, 22:2.98, 25:3.85, 32:6.31
}
BAR_LENGTH = 12.0

st.title("Rebar Optimizer Pro")
st.subheader("Created by Civil Engineer Moustafa Harmouch")

price = st.number_input("Price per ton ($)", min_value=0.0, value=1000.0)

# =========================
# Initialize dynamic rows per diameter
if "rows_count" not in st.session_state:
    st.session_state.rows_count = {d:1 for d in DIAMETERS}  # initial row per diameter

# =========================
# Input interface
st.header("Enter bar lengths and quantities for each diameter")

# Temporary container to read inputs at Run
input_data = {}

for d in DIAMETERS:
    with st.expander(f"Diameter {d} mm"):
        rows = st.session_state.rows_count[d]
        input_data[d] = []
        for i in range(rows):
            col1, col2, col3 = st.columns([2,2,1])
            with col1:
                length = st.number_input(f"Length (m) - Diameter {d} - Row {i+1}", min_value=0.1, value=1.0, step=0.1, key=f"len_{d}_{i}")
            with col2:
                quantity = st.number_input(f"Quantity - Diameter {d} - Row {i+1}", min_value=1, value=1, step=1, key=f"qty_{d}_{i}")
            input_data[d].append((length, int(quantity)))

        # الزر خارج الحلقة
        if st.button(f"Add Row - Diameter {d}", key=f"add_{d}"):
            st.session_state.rows_count[d] += 1
            # Streamlit سيعيد تشغيل السكربت تلقائيًا لعرض صف جديد

# =========================
# ILP Function for optimal cutting
def cutting_ilp(length_qty_list):
    lengths = []
    for l,q in length_qty_list:
        lengths.extend([l]*q)
    if not lengths:
        return [], []

    n = len(lengths)
    max_bars = n
    prob = LpProblem("CuttingStock", LpMinimize)
    x = [[LpVariable(f"x_{i}_{j}", cat=LpInteger, lowBound=0, upBound=1) for j in range(max_bars)] for i in range(n)]
    y = [LpVariable(f"y_{j}", cat=LpInteger, lowBound=0, upBound=1) for j in range(max_bars)]

    for i in range(n):
        prob += lpSum([x[i][j] for j in range(max_bars)]) == 1

    for j in range(max_bars):
        prob += lpSum([lengths[i]*x[i][j] for i in range(n)]) <= BAR_LENGTH * y[j]

    prob += lpSum([y[j] for j in range(max_bars)])
    prob.solve(PULP_CBC_CMD(msg=0))

    patterns = []
    waste_list = []
    for j in range(max_bars):
        bar = []
        total_len = 0
        for i in range(n):
            if x[i][j].varValue > 0.5:
                bar.append(lengths[i])
                total_len += lengths[i]
        if bar:
            patterns.append(bar)
            waste_list.append(BAR_LENGTH - total_len)
    return patterns, waste_list

# =========================
# Run Optimization
if st.button("Run Optimization"):
    mainbar_data = []
    waste_data = []
    purchase_data = []
    cutting_data = []

    for d in DIAMETERS:
        length_qty = input_data[d]
        if not length_qty:
            continue

        # MainBar Table
        for l,q in length_qty:
            w = l*q*wpm_dict[d]
            mainbar_data.append([d, l, q, round(w,2)])
        df_main = pd.DataFrame(mainbar_data, columns=["Diameter","Length","Quantity","Weight"])
        df_main.sort_values("Diameter", inplace=True)

        # ILP Optimization per diameter
        patterns, waste_list = cutting_ilp(length_qty)

        # WasteBar Table
        for bar, waste in zip(patterns, waste_list):
            weight_waste = waste*wpm_dict[d]
            waste_data.append([d, round(sum(bar),2), len(bar), round(weight_waste,2)])
        df_waste = pd.DataFrame(waste_data, columns=["Diameter","Bar Length (m)","Quantity","Weight (kg)"])
        df_waste.sort_values("Diameter", inplace=True)

        # PurchaseBar Table (12m bars)
        for bar in patterns:
            total_weight = sum(bar)*wpm_dict[d]
            cost = total_weight/1000*price
            purchase_data.append([d, 1, round(total_weight,2), round(cost,2)])
        df_purchase = pd.DataFrame(purchase_data, columns=["Diameter","Bars","Weight (kg)","Cost"])
        df_purchase.sort_values("Diameter", inplace=True)

        # Cutting Instructions Table
        pattern_counts = Counter(tuple(bar) for bar in patterns)
        for pattern, count in pattern_counts.items():
            pattern_str = " + ".join([f"{l:.2f} m" for l in pattern])
            cutting_data.append([d, pattern_str, count])
        df_cutting = pd.DataFrame(cutting_data, columns=["Diameter","Pattern","Count"])
        df_cutting.sort_values("Diameter", inplace=True)

    # =========================
    # Display tables
    st.success("Optimization Completed Successfully ✅")
    st.markdown("### MainBar Table")
    st.dataframe(df_main)
    st.markdown("### WasteBar Table")
    st.dataframe(df_waste)
    st.markdown("### PurchaseBar Table")
    st.dataframe(df_purchase)
    st.markdown("### Cutting Instructions Table")
    st.dataframe(df_cutting)

    # =========================
    # PDF Generation
    def generate_pdf(df_main, df_waste, df_purchase, df_cutting, price):
        pdf = FPDF(orientation='L')
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font("Arial",'B',16)
        pdf.cell(0,10,"Rebar Optimization Report",ln=True,align="C")
        pdf.ln(5)
        pdf.set_font("Arial",'',10)
        pdf.cell(0,8,"Created by Civil Engineer Moustafa Harmouch",ln=True)
        pdf.cell(0,8,f"Date: {datetime.date.today()}",ln=True)
        pdf.ln(10)

        def add_table(df, title):
            pdf.set_font("Arial",'B',12)
            pdf.cell(0,8,title,ln=True)
            pdf.set_font("Arial",'',10)
            col_widths = [30]*len(df.columns)
            for header,w in zip(df.columns,col_widths):
                pdf.cell(w,8,header,border=1)
            pdf.ln()
            for i in range(len(df)):
                for j,col in enumerate(df.columns):
                    pdf.cell(col_widths[j],8,str(df.iloc[i][col]),border=1)
                pdf.ln()
            pdf.ln(5)

        add_table(df_main,"MainBar Table")
        add_table(df_waste,"WasteBar Table")
        add_table(df_purchase,"PurchaseBar Table")
        add_table(df_cutting,"Cutting Instructions Table")

        file_name = "Rebar_Report.pdf"
        pdf.output(file_name)
        return file_name

    pdf_file = generate_pdf(df_main, df_waste, df_purchase, df_cutting, price)
    with open(pdf_file,"rb") as f:
        st.download_button("Download PDF Report", data=f, file_name=pdf_file, mime="application/pdf")
