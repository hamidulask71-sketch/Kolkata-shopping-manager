# shop_manager.py
# Kolkata Local Shop Manager - Simple Inventory & Billing App
# Run with: streamlit run shop_manager.py
# Requirements: pip install streamlit pandas

import streamlit as st
import pandas as pd
from datetime import datetime
import os

# File to save data (CSV for simplicity)
DATA_FILE = "shop_inventory.csv"
SALES_FILE = "sales_log.csv"

# Load or create inventory data
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        required_cols = ['Product', 'Price', 'Stock', 'Last Updated']
        for col in required_cols:
            if col not in df.columns:
                if col == 'Last Updated':
                    df[col] = ""
                else:
                    df[col] = 0.0 if col == 'Price' else 0
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0)
        return df
    else:
        df = pd.DataFrame(columns=['Product', 'Price', 'Stock', 'Last Updated'])
        df.to_csv(DATA_FILE, index=False)
        return df

# Load sales log
def load_sales():
    if os.path.exists(SALES_FILE):
        df = pd.read_csv(SALES_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    else:
        df = pd.DataFrame(columns=['Date', 'Product', 'Quantity', 'Total Price'])
        df.to_csv(SALES_FILE, index=False)
        return df

# Save data
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Save sales
def save_sales(sales_df):
    sales_df.to_csv(SALES_FILE, index=False)

# Main App Config
st.set_page_config(page_title="Kolkata Shop Manager", layout="wide")

st.title("কলকাতা লোকাল শপ ম্যানেজার")
st.markdown("**ছোট দোকানদারদের জন্য সিম্পল ইনভেন্টরি + বিলিং অ্যাপ**")
st.markdown("---")

# Load inventory and sales
inventory = load_data()
sales = load_sales()

# Sidebar menu
page = st.sidebar.selectbox(
    "মেনু",
    ["হোম", "পণ্য যোগ করুন", "ইনভেন্টরি দেখুন", "বিক্রি করুন", "সার্চ"]
)

if page == "হোম":
    st.header("স্বাগতম!")
    st.write("এই অ্যাপ দিয়ে আপনি সহজেই:")
    st.write("- নতুন পণ্য যোগ করতে পারবেন")
    st.write("- স্টক ট্র্যাক করতে পারবেন")
    st.write("- বিক্রির সময় স্টক আপডেট + বিল তৈরি করতে পারবেন")
    st.write(f"বর্তমানে {len(inventory)} টি পণ্য রেজিস্টার করা আছে।")
    
    if not inventory.empty:
        st.subheader("সাম্প্রতিক পণ্য (প্রথম ৫টি)")
        st.dataframe(inventory.head(5))
    else:
        st.info("এখনও কোনো পণ্য যোগ করা হয়নি। 'পণ্য যোগ করুন' মেনুতে যান।")

elif page == "পণ্য যোগ করুন":
    st.header("নতুন পণ্য যোগ করুন")
    
    with st.form(key="add_product_form"):
        product_name = st.text_input("পণ্যের নাম", placeholder="যেমন: রসগোল্লা / চাল / সাবান")
        price = st.number_input("দাম (প্রতি ইউনিট)", min_value=0.0, step=0.01, format="%.2f")
        stock = st.number_input("প্রাথমিক স্টক (পরিমাণ)", min_value=0, step=1)
        
        submit_button = st.form_submit_button("পণ্য যোগ করুন")
        
        if submit_button:
            if not product_name.strip():
                st.error("পণ্যের নাম দিন!")
            else:
                existing = inventory[inventory['Product'].str.lower() == product_name.lower()]
                if not existing.empty:
                    st.warning(f"'{product_name}' নামে ইতিমধ্যে পণ্য আছে। স্টক আপডেট করুন বা নতুন নাম দিন।")
                else:
                    new_row = {
                        'Product': product_name,
                        'Price': price,
                        'Stock': stock,
                        'Last Updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    inventory = pd.concat([inventory, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(inventory)
                    st.success(f"পণ্য '{product_name}' যোগ করা হয়েছে! স্টক: {stock}, দাম: ₹{price:.2f}")
                    st.balloons()
                    inventory = load_data()

elif page == "ইনভেন্টরি দেখুন":
    st.header("ইনভেন্টরি লিস্ট")
    
    if not inventory.empty:
        def highlight_low_stock(row):
            if row['Stock'] < 5:
                return ['background-color: yellow'] * len(row)
            else:
                return [''] * len(row)
        
        styled_df = inventory.style.apply(highlight_low_stock, axis=1)
        
        for idx, row in inventory.iterrows():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{row['Product']}**")
            with col2:
                st.write(f"₹{row['Price']:.2f}")
            with col3:
                st.write(f"{row['Stock']}")
            with col4:
                st.write(row['Last Updated'])
            
            with st.expander(f"এডিট: {row['Product']}"):
                with st.form(key=f"edit_{idx}"):
                    new_price = st.number_input("নতুন দাম", value=float(row['Price']), key=f"price_{idx}", step=0.01, format="%.2f")
                    new_stock = st.number_input("নতুন স্টক", value=int(row['Stock']), key=f"stock_{idx}", step=1)
                    edit_btn = st.form_submit_button("আপডেট")
                    
                    if edit_btn:
                        inventory.loc[idx, 'Price'] = new_price
                        inventory.loc[idx, 'Stock'] = new_stock
                        inventory.loc[idx, 'Last Updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        save_data(inventory)
                        st.success("আপডেট হয়েছে!")
                        st.rerun()
                        
                if st.button(f"মুছে ফেলুন: {row['Product']}", key=f"del_{idx}"):
                    inventory = inventory.drop(idx).reset_index(drop=True)
                    save_data(inventory)
                    st.success("পণ্য মুছে ফেলা হয়েছে!")
                    st.rerun()
        
        st.subheader("পুরো লিস্ট")
        st.dataframe(styled_df)
        
        low_stock = inventory[inventory['Stock'] < 5]
        if not low_stock.empty:
            st.warning(f"লো স্টক অ্যালার্ট: {len(low_stock)} টি পণ্যের স্টক কম।")
            st.dataframe(low_stock[['Product', 'Stock']])
            
    else:
        st.info("কোনো পণ্য নেই। 'পণ্য যোগ করুন' মেনুতে যান।")

elif page == "বিক্রি করুন":
    st.header("বিক্রি করুন")
    
    if not inventory.empty:
        product_options = {row['Product']: idx for idx, row in inventory.iterrows()}
        selected_product = st.selectbox("পণ্য নির্বাচন করুন", list(product_options.keys()))
        
        if selected_product:
            idx = product_options[selected_product]
            selected_row = inventory.loc[idx]
            current_stock = int(selected_row['Stock'])
            price_per_unit = float(selected_row['Price'])
            
            st.write(f"**বর্তমান স্টক:** {current_stock}")
            st.write(f"**প্রতি ইউনিট দাম:** ₹{price_per_unit:.2f}")
            
            with st.form(key="sell_form"):
                quantity = st.number_input("বিক্রির পরিমাণ", min_value=1, max_value=current_stock, step=1)
                customer_name = st.text_input("গ্রাহকের নাম (ঐচ্ছিক)", placeholder="যেমন: রাহুল দা")
                
                sell_button = st.form_submit_button("বিক্রি সম্পন্ন করুন")
                
                if sell_button:
                    if quantity > current_stock:
                        st.error("স্টক অপর্যাপ্ত!")
                    else:
                        total_price = quantity * price_per_unit
                        
                        inventory.loc[idx, 'Stock'] = current_stock - quantity
                        inventory.loc[idx, 'Last Updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        save_data(inventory)
                        
                        new_sale = {
                            'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'Product': selected_product,
                            'Quantity': quantity,
                            'Total Price': total_price
                        }
                        sales = pd.concat([sales, pd.DataFrame([new_sale])], ignore_index=True)
                        save_sales(sales)
                        
                        bill_text = f"""
কলকাতা লোকাল শপ - বিল
===============================
তারিখ: {datetime.now().strftime("%Y-%m-%d %H:%M")}
গ্রাহক: {customer_name or 'নগদ'}
পণ্য: {selected_product}
পরিমাণ: {quantity}
দাম: ₹{total_price:.2f}
===============================
ধন্যবাদ! আবার আসুন।
"""
                        st.success(f"বিক্রি সম্পন্ন! মোট: ₹{total_price:.2f}")
                        st.text_area("বিল (কপি করুন)", bill_text, height=150)
                        
                        st.download_button(
                            label="বিল ডাউনলোড (TXT)",
                            data=bill_text,
                            file_name=f"bill_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                            mime="text/plain"
                        )
                        
                        st.balloons()
                        st.rerun()
    else:
        st.warning("কোনো পণ্য নেই। প্রথমে 'পণ্য যোগ করুন'।")

elif page == "সার্চ":
    st.header("সার্চ এবং রিপোর্ট")
    
    tab1, tab2 = st.tabs(["পণ্য সার্চ", "বিক্রি রিপোর্ট"])
    
    with tab1:
        st.subheader("পণ্য সার্চ")
        
        with st.form(key="search_form"):
            search_query = st.text_input("পণ্যের নাম সার্চ করুন", placeholder="যেমন: রসগোল্লা")
            search_button = st.form_submit_button("সার্চ")
            
            if search_button or search_query:
                if not inventory.empty:
                    filtered = inventory[inventory['Product'].str.contains(search_query, case=False, na=False)]
                    
                    if filtered.empty:
                        st.info("কোনো পণ্য পাওয়া যায়নি।")
                    else:
                        st.success(f"{len(filtered)} টি পণ্য পাওয়া গেছে।")
                        st.dataframe(filtered)
                else:
                    st.warning("কোনো পণ্য নেই।")
    
    with tab2:
        st.subheader("বিক্রি রিপোর্ট")
        
        if not sales.empty:
            total_sales = sales['Total Price'].sum()
            st.metric("মোট বিক্রি", f"₹{total_sales:.2f}")
            
            sales['Date'] = pd.to_datetime(sales['Date'])
            recent_sales = sales[sales['Date'] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
            if not recent_sales.empty:
                daily = recent_sales.groupby(recent_sales['Date'].dt.date)['Total Price'].sum().reset_index()
                st.subheader("সাম্প্রতিক ৭ দিনের বিক্রি")
                st.dataframe(daily)
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("শুরুর তারিখ", value=pd.Timestamp.now() - pd.Timedelta(days=30))
            with col2:
                end_date = st.date_input("শেষ তারিখ", value=pd.Timestamp.now())
            
            filtered_sales = sales[(sales['Date'].dt.date >= start_date) & (sales['Date'].dt.date <= end_date)]
            if not filtered_sales.empty:
                st.subheader("ফিল্টার্ড বিক্রি")
                st.dataframe(filtered_sales)
            else:
                st.info("এই তারিখের মধ্যে কোনো বিক্রি নেই।")
        else:
            st.info("এখনও কোনো বিক্রি রেকর্ড নেই।")
