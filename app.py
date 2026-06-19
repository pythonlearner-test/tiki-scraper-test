import streamlit as st
import requests
import pandas as pd
import io
import time

st.set_page_config(page_title="Tiki Trading Scraper", page_icon="🛒", layout="centered")

st.title("🛒 Công cụ cào dữ liệu Tiki Trading")
st.write("Ứng dụng giúp lấy dữ liệu sản phẩm từ gian hàng Tiki Trading xuất ra file Excel.")

# Giao diện nhập liệu
keyword = st.text_input("Nhập từ khóa sản phẩm muốn tìm:", "Vinamilk")
pages = st.number_input("Số lượng trang muốn cào (Mỗi trang tối đa 40 SP):", min_value=1, max_value=100, value=5)

if st.button("🚀 Bắt đầu cào dữ liệu"):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'X-Source': 'Web',
    }
    
    product_list = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for page in range(1, pages + 1):
        status_text.text(f"Đang lấy dữ liệu trang {page}/{pages}...")
        url = f"https://tiki.vn/api/v2/products?q={keyword}&seller=1&page={page}&limit=40"
        
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                products = res.json().get('data', [])
                if not products:
                    status_text.text("Đã lấy hết sản phẩm có sẵn.")
                    break
                
                for p in products:
                    # 1. Lấy giá bán sau giảm (Giá hiện tại)
                    current_price = p.get('price')
                    
                    # 2. Xử lý lấy Giá niêm yết thông minh (Kiểm tra nhiều trường dự phòng)
                    market_price = p.get('market_price')
                    original_price = p.get('original_price')
                    
                    # Ưu tiên market_price -> original_price -> current_price
                    if market_price and int(market_price) > 0:
                        list_price = market_price
                    elif original_price and int(original_price) > 0:
                        list_price = original_price
                    else:
                        list_price = current_price
                    
                    # 3. Lấy phần trăm giảm giá
                    discount_rate = p.get('discount_rate', 0)
                    discount_str = f"{discount_rate}%" if discount_rate > 0 else "0%"
                    
                    # Bóc tách dữ liệu sạch
                    product_list.append({
                        'Mã sản phẩm': p.get('id'),
                        'Tên sản phẩm': p.get('name'),
                        'Giá niêm yết (VND)': list_price,
                        'Giá sau giảm (VND)': current_price,
                        '% giảm': discount_str,
                        'Link sản phẩm': f"https://tiki.vn/{p.get('url_path')}"
                    })
            else:
                st.error(f"Lỗi kết nối Tiki tại trang {page}")
                break
        except:
            st.error("Có lỗi xảy ra trong quá trình cào.")
            break
            
        progress_bar.progress(page / pages)
        time.sleep(2)
        
    status_text.text("Quá trình cào hoàn tất!")
    
    if product_list:
        df = pd.DataFrame(product_list)
        st.success(f"🎉 Thành công! Tìm thấy tổng cộng {len(df)} sản phẩm.")
        
        # Hiển thị bảng xem trước dữ liệu trực tiếp trên Web
        st.write("### Bản xem trước dữ liệu:")
        st.dataframe(df.head())
        
        # Định dạng xuất file Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        # Nút bấm Tải file Excel
        st.download_button(
            label="📥 TẢI VỀ FILE EXCEL NGAY",
            data=buffer.getvalue(),
            file_name=f"tiki_{keyword}_trading.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Không tìm thấy sản phẩm nào phù hợp.")
