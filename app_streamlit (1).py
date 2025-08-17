
# app_streamlit.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

st.set_page_config(page_title="SutraPOS – Maheshwari Edition", layout="wide")

INV_PATH = Path(__file__).parent / "inventory.csv"
TX_PATH = Path(__file__).parent / "transactions.csv"

# ---------- Load Data ----------
def load_inventory():
    if INV_PATH.exists():
        return pd.read_csv(INV_PATH)
    return pd.DataFrame(columns=["SKU","Title","Fabric","ZariType","Motif","BorderStyle","Color","Occasion","MRP","GST_Slab","Qty","Artisan","Story","ImagePath"])

def load_transactions():
    if TX_PATH.exists():
        return pd.read_csv(TX_PATH)
    return pd.DataFrame(columns=["InvoiceID","DateTime","CustomerName","CustomerPhone","ItemsJSON","Subtotal","Tax","Total","PaymentMode"])

inventory = load_inventory()
transactions = load_transactions()

# ---------- Helpers ----------
def save_inventory(df):
    df.to_csv(INV_PATH, index=False)

def save_transactions(df):
    df.to_csv(TX_PATH, index=False)

def generate_invoice_pdf(invoice_id, date_time, customer_name, customer_phone, items, subtotal, tax, total, payment):
    file_path = Path.cwd() / f"{invoice_id}.pdf"
    c = canvas.Canvas(str(file_path), pagesize=A4)
    w, h = A4
    y = h - 2*cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, y, "SutraPOS – Maheshwari Edition")
    y -= 0.8*cm
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, f"Invoice: {invoice_id}   Date: {date_time}")
    y -= 0.4*cm
    c.drawString(2*cm, y, f"Customer: {customer_name or '-'}   Phone: {customer_phone or '-'}")
    y -= 0.8*cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, "Items")
    y -= 0.4*cm
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y, "SKU")
    c.drawString(7*cm, y, "Title")
    c.drawRightString(16*cm, y, "MRP")
    c.drawRightString(18*cm, y, "Qty")
    c.drawRightString(20*cm, y, "Line Total")
    y -= 0.3*cm
    c.line(2*cm, y, 19.5*cm, y)
    y -= 0.4*cm
    for it in items:
        c.drawString(2*cm, y, it["SKU"][:14])
        c.drawString(7*cm, y, it["Title"][:28])
        c.drawRightString(16*cm, y, f"₹{it['MRP']:.0f}")
        c.drawRightString(18*cm, y, f"{it['Qty']}")
        c.drawRightString(20*cm, y, f"₹{it['MRP']*it['Qty']:.0f}")
        y -= 0.35*cm
    y -= 0.3*cm
    c.line(2*cm, y, 19.5*cm, y)
    y -= 0.6*cm
    c.drawRightString(16*cm, y, "Subtotal:")
    c.drawRightString(20*cm, y, f"₹{subtotal:.2f}")
    y -= 0.5*cm
    c.drawRightString(16*cm, y, "GST:")
    c.drawRightString(20*cm, y, f"₹{tax:.2f}")
    y -= 0.5*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(16*cm, y, "Total:")
    c.drawRightString(20*cm, y, f"₹{total:.2f}")
    y -= 1.0*cm
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, y, f"Payment: {payment}")
    y -= 0.5*cm
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(2*cm, y, "Thank you for celebrating Indian handloom!")
    c.showPage()
    c.save()
    return file_path

# ---------- UI ----------
st.title("🧵 SutraPOS – Maheshwari Edition")
st.caption("Bill. Recommend. Celebrate the weave. (Maheshwari handloom POS demo)")

tab_catalog, tab_pos, tab_inventory, tab_ai, tab_reports = st.tabs(
    ["Catalog", "POS Billing", "Inventory", "AI Assistant", "Reports"]
)

with tab_catalog:
    st.subheader("Catalog")
    if inventory.empty:
        st.info("No inventory found. Add items in the Inventory tab.")
    else:
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            f_occ = st.selectbox("Occasion", ["All"] + sorted(inventory["Occasion"].dropna().unique().tolist()))
        with col2:
            f_color = st.selectbox("Color", ["All"] + sorted(inventory["Color"].dropna().unique().tolist()))
        with col3:
            f_fabric = st.selectbox("Fabric", ["All"] + sorted(inventory["Fabric"].dropna().unique().tolist()))
        with col4:
            price_max = st.number_input("Max Price (₹)", min_value=0, value=int(inventory["MRP"].max()) if not inventory.empty else 0, step=500)

        df = inventory.copy()
        if f_occ != "All":
            df = df[df["Occasion"]==f_occ]
        if f_color != "All":
            df = df[df["Color"]==f_color]
        if f_fabric != "All":
            df = df[df["Fabric"]==f_fabric]
        df = df[df["MRP"]<=price_max]

        # Cards
        for _, row in df.iterrows():
            with st.container(border=True):
                cols = st.columns([1,2])
                with cols[0]:
                    if Path(row["ImagePath"]).exists():
                        st.image(str(Path(__file__).parent / row["ImagePath"]), use_container_width=True)
                with cols[1]:
                    st.markdown(f"#### {row['Title']}  \n**₹{int(row['MRP'])}** | {row['Fabric']} | {row['Motif']} | {row['Color']}")
                    st.caption(f"Zari: {row['ZariType']} | Border: {row['BorderStyle']} | Occasion: {row['Occasion']}")
                    with st.expander("Story / Details"):
                        st.write(row["Story"])
                        st.write(f"Artisan: {row['Artisan']}")
                    if st.button(f"Add to POS cart – {row['SKU']}", key=f"add_{row['SKU']}"):
                        if "session_cart" not in st.session_state:
                            st.session_state.session_cart = []
                        st.session_state.session_cart.append({"SKU":row["SKU"],"Title":row["Title"],"Qty":1,"MRP":float(row["MRP"]), "GST": float(row["GST_Slab"])})
                        st.success("Added to POS cart. Navigate to POS Billing tab.")

with tab_pos:
    st.subheader("POS Billing")
    if "session_cart" not in st.session_state:
        st.session_state.session_cart = []

    # Add manual item
    with st.expander("Add items manually"):
        skus = inventory["SKU"].tolist()
        if skus:
            sku_select = st.selectbox("Select SKU", skus)
            qty = st.number_input("Qty", min_value=1, value=1, step=1)
            if st.button("Add to cart"):
                row = inventory[inventory["SKU"] == sku_select].iloc[0].to_dict()
                st.session_state.session_cart.append({"SKU": sku_select, "Title": row["Title"], "Qty": qty, "MRP": float(row["MRP"]), "GST": float(row["GST_Slab"])})
                st.success(f"Added {qty} x {row['Title']}")
        else:
            st.info("No inventory yet. Add items in Inventory tab.")

    st.write("### Cart")
    if st.session_state.session_cart:
        st.table(pd.DataFrame(st.session_state.session_cart))
        subtotal = sum(i["MRP"]*i["Qty"] for i in st.session_state.session_cart)
        tax = sum(i["MRP"]*i["Qty"]*i["GST"]/100 for i in st.session_state.session_cart)
        total = subtotal + tax
        colA, colB, colC = st.columns(3)
        colA.metric("Subtotal (₹)", round(subtotal,2))
        colB.metric("Tax (₹)", round(tax,2))
        colC.metric("Total (₹)", round(total,2))

        col1, col2 = st.columns(2)
        with col1:
            cust_name = st.text_input("Customer Name")
            cust_phone = st.text_input("Customer Phone")
        with col2:
            payment = st.selectbox("Payment Mode", ["UPI","Cash","Card"])

        if st.button("Generate Invoice"):
            invoice_id = f"INV{datetime.now().strftime('%Y%m%d%H%M%S')}"
            new_tx = {
                "InvoiceID": invoice_id,
                "DateTime": datetime.now().isoformat(timespec='seconds'),
                "CustomerName": cust_name,
                "CustomerPhone": cust_phone,
                "ItemsJSON": json.dumps(st.session_state.session_cart),
                "Subtotal": round(subtotal,2),
                "Tax": round(tax,2),
                "Total": round(total,2),
                "PaymentMode": payment
            }
            global transactions, inventory
            transactions = pd.concat([transactions, pd.DataFrame([new_tx])], ignore_index=True)
            save_transactions(transactions)

            # reduce inventory
            for item in st.session_state.session_cart:
                idx = inventory[inventory["SKU"]==item["SKU"]].index
                if len(idx):
                    inventory.loc[idx, "Qty"] = (inventory.loc[idx, "Qty"] - item["Qty"]).clip(lower=0)
            save_inventory(inventory)

            pdf_path = generate_invoice_pdf(invoice_id, new_tx["DateTime"], cust_name, cust_phone, st.session_state.session_cart, subtotal, tax, total, payment)
            st.success(f"Invoice {invoice_id} generated.")
            st.download_button("Download Invoice PDF", data=open(pdf_path, "rb"), file_name=f"{invoice_id}.pdf")
            st.session_state.session_cart = []
    else:
        st.info("Cart empty. Add items from Catalog or Inventory.")

with tab_inventory:
    st.subheader("Inventory")
    st.dataframe(inventory, use_container_width=True)
    with st.expander("Add New Item"):
        cols = st.columns(5)
        SKU = cols[0].text_input("SKU")
        Title = cols[1].text_input("Title")
        Fabric = cols[2].selectbox("Fabric", ["Silk-Cotton","Pure Silk","Cotton"])
        Zari = cols[3].selectbox("Zari Type", ["Zari","Resham","None"])
        Motif = cols[4].selectbox("Motif", ["Buti","Paisley","Floral","Geometric"])
        cols2 = st.columns(5)
        Border = cols2[0].selectbox("Border Style", ["Classic","Contrast","Temple","Kadiyal"])
        Color = cols2[1].text_input("Color")
        Occasion = cols2[2].selectbox("Occasion", ["Wedding","Festive","Daily Wear"])
        MRP = cols2[3].number_input("MRP (₹)", min_value=0.0, step=100.0)
        GST = cols2[4].number_input("GST (%)", min_value=0.0, max_value=28.0, step=0.5, value=5.0)
        cols3 = st.columns(3)
        Qty = cols3[0].number_input("Qty", min_value=0, step=1, value=1)
        Artisan = cols3[1].text_input("Artisan/Cluster")
        Story = cols3[2].text_input("Short Story")
        if st.button("Save Item"):
            new_row = {"SKU":SKU,"Title":Title,"Fabric":Fabric,"ZariType":Zari,"Motif":Motif,"BorderStyle":Border,"Color":Color,"Occasion":Occasion,
                       "MRP":MRP,"GST_Slab":GST,"Qty":Qty,"Artisan":Artisan,"Story":Story,"ImagePath":""}
            inventory = pd.concat([inventory, pd.DataFrame([new_row])], ignore_index=True)
            save_inventory(inventory)
            st.success("Item added.")

with tab_ai:
    st.subheader("AI Assistant (Rule-based Demo)")
    st.write("Ask me in plain English or Hindi. Example: 'wedding saree under 8000 in red' / 'shaadi ke liye laal saree 8000 ke neeche'")
    q = st.text_input("Your question")
    if st.button("Get Suggestion"):
        df = inventory.copy()
        ql = q.lower()
        price_cap = None
        # Extract a number as possible price cap
        for token in ql.replace('₹',' ').split():
            if token.replace(',','').isdigit():
                price_cap = float(token.replace(',',''))
                break
        if "wedding" in ql or "shaadi" in ql:
            df = df[df["Occasion"]=="Wedding"]
        if "festive" in ql or "tyohar" in ql or "festival" in ql:
            df = df[df["Occasion"].isin(["Festive","Wedding"])]
        # Color filter
        for color in df["Color"].dropna().unique().tolist():
            if color and color.lower() in ql:
                df = df[df["Color"].str.lower()==color.lower()]
                break
        if price_cap:
            df = df[df["MRP"]<=price_cap]
        # Sort by price ascending for budget queries
        df = df.sort_values("MRP").head(5)
        if df.empty:
            st.warning("No items match. Try changing color/price/occasion or add more inventory.")
        else:
            st.write("Recommended picks:")
            show = df[["SKU","Title","Fabric","Motif","BorderStyle","Color","Occasion","MRP","Story"]]
            st.table(show)

    with st.expander("Maheshwari Heritage (Quick Story)"):
        st.write("Maheshwari sarees originate from **Maheshwar, Madhya Pradesh**, patronized by **Queen Ahilyabai Holkar** since the 18th century. The hallmark is a **silk-cotton** blend, lightweight drape, **reversible borders**, and elegant **zari work** with geometric and floral motifs.")

with tab_reports:
    st.subheader("Reports")
    if not transactions.empty:
        st.write("Recent Transactions")
        st.dataframe(transactions.tail(10), use_container_width=True)
        total_sales = float(transactions["Total"].sum())
        upi_ratio = (transactions["PaymentMode"]=="UPI").mean() if len(transactions)>0 else 0
        st.metric("Total Sales (₹)", round(total_sales,2))
        st.metric("UPI Share", f"{upi_ratio*100:.0f}%")
        # Top sellers
        # Expand line items
        all_items = []
        for _, row in transactions.iterrows():
            try:
                items = json.loads(row["ItemsJSON"])
                all_items.extend(items)
            except:
                pass
        if all_items:
            items_df = pd.DataFrame(all_items)
            top = items_df.groupby("SKU").agg(Qty=("Qty","sum"), Title=("Title","first")).sort_values("Qty", ascending=False).head(5)
            st.write("Top Selling SKUs")
            st.table(top)
    else:
        st.info("No transactions yet. Generate invoices in POS Billing.")
