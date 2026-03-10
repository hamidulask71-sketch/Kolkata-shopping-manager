import streamlit as st
import pandas as pd
import os
from datetime import datetime
import speech_recognition as sr

# ফাইল নাম
DATA_FILE = "shop_inventory.csv"
SALES_FILE = "sales_log.csv"

# ডাটা লোড ফাংশন
@st.cache_data(ttl=30)  # ৩০ সেকেন্ড ক্যাশে রাখবে
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0)
        df['Last Updated'] = pd.to_datetime(df['Last Updated'], errors='coerce')
        return df
    else:
        df = pd.DataFrame(columns=['Product', 'Price', 'Stock', 'Last Updated'])
        df.to_csv(DATA_FILE, index=False)
        return df

@st.cache_data(ttl=30)
def load_sales():
    if os.path.exists(SALES_FILE):
        df = pd.read_csv(SALES_FILE)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Total Price'] = pd.to_numeric(df['Total Price'], errors='coerce').fillna(0)
        return df
    else:
        df = pd.DataFrame(columns=['Date', 'Product', 'Quantity', 'Total Price'])
        df.to_csv(SALES_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def save_sales(df):
    df.to_csv(SALES_FILE, index=False)

# অ্যাপ কনফিগ
st.set_page_config(
    page_title="কলকাতা লোকাল শপ ম্যানেজার",
    page_icon="🛒",
    layout="wide"
)

# বর্তমান সময় + তারিখ (সাইডবারে)
now = datetime.now()
st.sidebar.markdown(f"**তারিখ:** {now.strftime('%Y-%m-%d')}")
st.sidebar.markdown(f"**সময়:** {now.strftime('%H:%M:%S')}")

# লোগো (repo-তে logo.png আপলোড করলে দেখাবে)
st.logo("logo.png", size="medium")

# মূল টাইটেল
st.title("কলকাতা লোকাল শপ ম্যানেজার")
st.markdown("***ছোট দোকানদারদের জন্য সিম্পল ইনভেন্টরি + বিলিং + ভয়েস ইনপুট অ্যাপ***")
st.markdown("---")

# ডাটা লোড
inventory = load_data()
sales = load_sales()

# সাইডবার মেনু
page = st.sidebar.selectbox(
    "পেজ নির্বাচন করুন",
    ["হোম", "নতুন পণ্য যোগ করুন", "বিক্রি করুন", "রিপোর্ট"]
)

# হোম পেজ
if page == "হোম":
    st.header("স্বাগতম!")
    st.write("এই অ্যাপ দিয়ে আপনি করতে পারবেন:")
    st.write("- নতুন পণ্য যোগ করা (কীবোর্ড / মাইক দিয়ে)")
    st.write("- বিক্রি রেকর্ড করা + বিল দেখা")
    st.write("- স্টক দেখা + লো স্টক অ্যালার্ট")
    st.write("- আজকের ও মোট বিক্রির রিপোর্ট")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("মোট পণ্য", len(inventory))
    with col2:
        st.metric("আজকের বিক্রি", len(sales[sales['Date'].dt.date == now.date()]))

    if not inventory.empty:
        st.subheader("সাম্প্রতিক পণ্য (প্রথম ৫টা)")
        st.dataframe(inventory.head(5))
    else:
        st.info("এখনো কোনো পণ্য যোগ করা হয়নি।")

# নতুন পণ্য যোগ করুন
elif page == "নতুন পণ্য যোগ করুন":
    st.header("নতুন পণ্য যোগ করুন")

    # মাইক অপশন
    st.subheader("মাইক দিয়ে পণ্যের নাম বলুন")
    if st.button("🎤 মাইক চালু করুন"):
        with st.spinner("শুনছি..."):
            r = sr.Recognizer()
            try:
                with sr.Microphone() as source:
                    audio = r.listen(source, timeout=5, phrase_time_limit=5)
                text = r.recognize_google(audio, language="bn-IN")
                st.success(f"শোনা গেছে: **{text}**")
                product_name_default = text
            except:
                st.warning("কথা বোঝা যায়নি বা মাইক সমস্যা। নিচে টাইপ করুন।")
                product_name_default = ""
    else:
        product_name_default = ""

    with st.form("add_product_form"):
        product_name = st.text_input("পণ্যের নাম", value=product_name_default, placeholder="যেমন: চাল / সাবান / দুধ")
        price = st.number_input("দাম (₹)", min_value=0.01, step=0.01, format="%.2f")
        stock = st.number_input("প্রাথমিক স্টক", min_value=0, step=1)

        submitted = st.form_submit_button("যোগ করুন")
        if submitted:
            if not product_name.strip():
                st.error("পণ্যের নাম দিন")
            elif product_name.lower() in inventory['Product'].str.lower().values:
                st.error("এই নামের পণ্য আগে থেকে আছে")
            else:
                new_row = {
                    'Product': product_name,
                    'Price': price,
                    'Stock': stock,
                    'Last Updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                inventory = pd.concat([inventory, pd.DataFrame([new_row])], ignore_index=True)
                save_data(inventory)
                st.success(f"{product_name} যোগ হয়েছে ✓")
                st.rerun()

    st.subheader("বর্তমান পণ্য তালিকা")
    st.dataframe(inventory)

# বিক্রি করুন
elif page == "বিক্রি করুন":
    st.header("বিক্রি করুন")

    if inventory.empty:
        st.info("কোনো পণ্য নেই। প্রথমে পণ্য যোগ করুন।")
    else:
        product = st.selectbox("পণ্য নির্বাচন করুন", inventory['Product'])
        current_stock = inventory[inventory['Product'] == product]['Stock'].values[0]
        price = inventory[inventory['Product'] == product]['Price'].values[0]

        quantity = st.number_input("পরিমাণ", min_value=1, max_value=int(current_stock), step=1)

        if st.button("বিক্রি সম্পন্ন করুন"):
            if quantity > current_stock:
                st.error(f"স্টক কম আছে! উপলব্ধ: {current_stock}")
            else:
                total = quantity * price
                sale_row = {
                    'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Product': product,
                    'Quantity': quantity,
                    'Total Price': total
                }
                sales = pd.concat([sales, pd.DataFrame([sale_row])], ignore_index=True)
                save_sales(sales)

                inventory.loc[inventory['Product'] == product, 'Stock'] -= quantity
                inventory.loc[inventory['Product'] == product, 'Last Updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_data(inventory)

                st.success(f"{quantity} টি {product} বিক্রি হয়েছে। মোট: ₹{total:.2f}")
                st.balloons()

                # সিম্পল বিল দেখানো
                st.subheader("বিক্রির বিল")
                st.markdown(f"**তারিখ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                st.markdown(f"**পণ্য:** {product}")
                st.markdown(f"**পরিমাণ:** {quantity}")
                st.markdown(f"**দাম:** ₹{price:.2f}")
                st.markdown("---")
                st.markdown(f"**মোট:** ₹{total:.2f}")
                st.markdown("**ধন্যবাদ! আবার আসবেন।**")

# রিপোর্ট
elif page == "রিপোর্ট":
    st.header("রিপোর্ট")

    col1, col2, col3 = st.columns(3)
    col1.metric("মোট পণ্য", len(inventory))
    col2.metric("মোট বিক্রি রেকর্ড", len(sales))
    col3.metric("আজকের বিক্রি", f"₹{sales[sales['Date'].dt.date == now.date()]['Total Price'].sum():.2f}")

    st.subheader("লো স্টক পণ্য (স্টক < ৫)")
    low_stock = inventory[inventory['Stock'] < 5]
    if low_stock.empty:
        st.success("কোনো পণ্য লো স্টকে নেই ✓")
    else:
        st.dataframe(low_stock)
        st.warning("এই পণ্যগুলোর স্টক দ্রুত বাড়ানো দরকার!")

    st.subheader("সাম্প্রতিক বিক্রি (শেষ ১০টা)")
    if not sales.empty:
        st.dataframe(sales.sort_values('Date', ascending=False).head(10))
    else:
        st.info("এখনো কোনো বিক্রি হয়নি।")
