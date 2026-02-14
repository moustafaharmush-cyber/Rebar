import streamlit as st
import pandas as pd
from collections import defaultdict, Counter
import random
from fpdf import FPDF
import datetime

# =========================
# Settings
# =========================
BAR_LENGTH = 12.0
ITERATIONS = 3000
DIAMETERS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 32]

def weight_per_meter(diameter):
    return (diameter ** 2) / 162

# =========================
# Streamlit Interface
# =========================
st.set_page_config(layout="wide")
st.title("Rebar Optimizer Pro")
st.subheader("Created by Civil Engineer Moustafa Harmouch")

price = st.number_input("Price per ton ($)", min_value=0.0, value=1000.0)

# Initialize session state for each diameter
for d in DIAMETERS:
    if f"rows_{d}" not in st.session_state:
        st.session_state[f"rows_{d}"] = []

# ---------- MainBar Input ----------
st.markdown("### MainBar - Input Rebars")
mainbar_data = []

for d in DIAMETERS:
    with st.expander(f"Diameter {d} mm"):
        rows = st.session_state[f"rows_{d}"]

        # عرض كل صف موجود
        for i, row in enumerate(rows):
            col1, col2, col3 = st.columns(3)
            row["Length"] = col1.number_input(f"Length (m) [{i+1}]", value=row.get("Length",0.0), min_value=0.0, key=f"len_{d}_{i}")
            row["Quantity"] = col2.number_input(f"Quantity [{i+1}]", value=row.get("Quantity",0), min_value=0, key=f"qty_{d}_{i}")
            row["Weight"] = weight_per_meter(d) * row["Length"] * row["Quantity"]
            col3.write(f"Weight: {row['Weight']:.2f} kg")

        # زر لإضافة صف جديد
        if st.button(f"Add Row Ø{d}"):
            st.session_state[f"rows_{d}"].append({"Length":0.0, "Quantity":0, "Weight":0.0})

        # بعد إدخال كل الصفوف، نجمع بيانات MainBar لعرضها لاحقًا
        for row in rows:
            if row["Length"] > 0 and row["Quantity"] > 0:
                mainbar_data.append([d, row["Length"], row["Quantity"], row["Weight"]])

# تجميع المكررات بنفس القطر والطول
df_mainbar = pd.DataFrame(mainbar_data, columns=["Diameter","Length","Quantity","Weight"])
df_mainbar = df_mainbar.groupby(["Diameter","Length"], as_index=False).agg({"Quantity":"sum","Weight":"sum"})

# حساب الوزن الكلي
total_weight = df_mainbar["Weight"].sum()
st.markdown("### MainBar Summary")
st.dataframe(df_mainbar)
st.markdown(f"**Total Weight: {total_weight:.2f} kg**")
