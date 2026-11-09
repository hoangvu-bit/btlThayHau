# ĐỀ TÀI 10: HỆ THỐNG QUẢN LÝ NHÀ HÀNG GỌI MÓN

* **Học phần:** Công nghệ phần mềm
* **Giảng viên hướng dẫn:** ThS. Dương Hữu Thành
* **Khoa:** Công nghệ Thông tin - Trường Đại học Mở TP.HCM
* **Công nghệ sử dụng:** Python 3.x, Flask, SQLAlchemy, MySQL, Bootstrap 5, Chart.js

---

## 1. Giới thiệu & Các chức năng chính

Hệ thống hỗ trợ quy trình vận hành khép kín cho nhà hàng gọi món từ khâu gọi món tại bàn, điều phối chế biến tại bếp theo thời gian thực, thanh toán hóa đơn đến quản trị thực đơn và báo cáo thống kê doanh thu.

Dự án đáp ứng đầy đủ 5 yêu cầu chuẩn của Đề tài 10:

1. **Yêu cầu 1: Nhận đơn hàng tại bàn (`/`)**
   - Nhân viên phục vụ chọn bàn và ghi nhận món ăn theo yêu cầu của khách.
   - **Quy định:** Mỗi bàn chỉ có duy nhất 1 phiếu mở (`OPEN`) cùng lúc. Khi gọi trùng món trong cùng phiếu, hệ thống **tự động cộng dồn số lượng** thay vì tạo dòng mới.
2. **Yêu cầu 2: Bếp nhận danh sách chế biến (`/kitchen`)**
   - Bếp chỉ hiển thị các món ăn thuộc nhóm cần nấu (`is_kitchen = True`) và chưa hoàn tất (`COOKING`). Thức uống đóng chai được hoàn tất sẵn và không vào danh sách bếp.
   - Khi bếp bấm **"Xác nhận hoàn tất"**, trạng thái món chuyển sang `DONE`. Màn hình phục vụ lập tức hiển thị thông báo nổi bật (banner alert & toast) để nhân viên mang món ra bàn.
   - Tích hợp cơ chế **tự động làm mới (polling real-time mỗi 3-5 giây)** đồng bộ tức thời giữa Bàn và Bếp.
3. **Yêu cầu 3: Thanh toán hóa đơn (`/cashier`)**
   - Thu ngân chọn bàn để xuất hóa đơn thanh toán: hiển thị chi tiết tên món, số lượng, đơn giá, thành tiền.
   - **Chính sách:** Tự động áp dụng giảm giá 5% nếu tổng tiền món > 500.000 VNĐ và cộng thêm thuế VAT 10%.
   - Hỗ trợ nút **"In hóa đơn"** (`window.print()`) chuẩn in hóa đơn nhà hàng (tự động ẩn menu và thanh điều hướng). Sau khi thanh toán, hóa đơn chuyển sang `PAID` và bàn chuyển về trạng thái trống.
4. **Yêu cầu 4: Quản lý thực đơn (`/admin-menu`)**
   - Cho phép Thêm, Sửa (nạp dữ liệu món theo `edit_id`) và Xóa món ăn.
   - Kiểm tra ràng buộc chặt chẽ: Mã món ăn duy nhất, Đơn giá phải lớn hơn 0 (`> 0`), và Nhóm món (Category) hợp lệ.
5. **Yêu cầu 5: Báo cáo doanh thu & Thống kê (`/stats`)**
   - Thống kê doanh thu từ các hóa đơn đã thanh toán (`PAID`).
   - Thẻ tổng quan: Tổng doanh thu (VNĐ), Tổng số hóa đơn, Tổng số lượng món đã bán.
   - Bảng xếp hạng Top món ăn bán chạy nhất (kèm số lượng, doanh thu và tỷ lệ phần trăm đóng góp).
   - Bộ lọc linh hoạt: Tra cứu theo **Ngày cụ thể** hoặc theo **Tháng & Năm**.
   - Tích hợp **Chart.js** vẽ Biểu đồ tròn (Doughnut/Pie Chart) trực quan, có nút chuyển đổi xem theo Doanh thu hoặc Số lượng.

---

## 2. Cấu trúc thư mục dự án

```text
btlThayHau/
├── .env                      # File chứa mật khẩu & cấu hình nhạy cảm (Được ẩn bởi .gitignore)
├── .env.example              # File mẫu cấu hình biến môi trường khi chia sẻ code
├── .gitignore                # Chặn các file bảo mật, .venv, __pycache__ khi đẩy lên GitHub
├── requirements.txt          # Danh sách các thư viện Python cần cài đặt
├── README.md                 # Tài liệu hướng dẫn cài đặt & sử dụng chi tiết
└── RestaurantApp/
    ├── __init__.py           # Khởi tạo Flask App & kết nối CSDL từ config.py
    ├── config.py             # Trung tâm quản lý cấu hình nạp từ .env (dotenv + quote)
    ├── models.py             # Khai báo các Model ORM (Category, Dish, DiningTable, Order, OrderDetail)
    ├── dao.py                # Tầng xử lý nghiệp vụ & truy vấn dữ liệu (Data Access Object)
    ├── index.py              # Controller điều hướng các Route và API Polling
    ├── data/
    │   └── categories.json   # Dữ liệu danh mục tham khảo
    └── templates/
        ├── layout/
        │   ├── base.html     # Khung giao diện dùng chung (Bootstrap 5.3 + Bootstrap Icons)
        │   ├── header.html   # Thanh điều hướng Navbar (Highlight active menu)
        │   └── footer.html   # Chân trang thông tin đồ án
        ├── index.html        # Giao diện YC1: Nhận đơn tại bàn & Toast Bếp nấu xong
        ├── kitchen.html      # Giao diện YC2: Màn hình Bếp chế biến món ăn
        ├── cashier.html      # Giao diện YC3: Màn hình Thu ngân thanh toán & In hóa đơn
        ├── admin_menu.html   # Giao diện YC4: Quản lý thực đơn (Thêm / Sửa / Xóa)
        └── stats.html        # Giao diện YC5: Báo cáo thống kê & Biểu đồ Chart.js
```

---

## 3. Hướng dẫn cài đặt và chạy chương trình

### Bước 1: Mở Terminal tại thư mục dự án
Mở terminal (PowerShell, CMD hoặc Git Bash) tại thư mục gốc `btlThayHau/`:
```bash
cd D:\ALL_Assignment\btlThayHau
```

### Bước 2: Tạo và kích hoạt môi trường ảo (Virtual Environment)
* **Trên Windows (PowerShell / CMD):**
  ```bash
  python -m venv .venv
  .venv\Scripts\activate
  ```
* **Trên macOS / Linux / Git Bash:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### Bước 3: Cài đặt các thư viện cần thiết
Chạy lệnh sau để cài đặt toàn bộ thư viện từ `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Bước 4: Cấu hình thông tin mật khẩu vào file `.env`
Dự án sử dụng cơ chế bảo mật biến môi trường, tuyệt đối **không viết cứng mật khẩu vào mã nguồn**.

1. Sao chép file `.env.example` thành file `.env`:
   * **Trên Windows PowerShell:**
     ```powershell
     Copy-Item .env.example .env
     ```
   * **Trên CMD / Git Bash / Linux:**
     ```bash
     cp .env.example .env
     ```
2. Mở file `.env` vừa tạo và điền mật khẩu MySQL của bạn tại dòng `DB_PASSWORD`:
   ```env
   SECRET_KEY=1234567890!@#$%^&*()
   DB_USER=root
   DB_PASSWORD=mat_khau_mysql_cua_ban
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=restaurantdb
   ```
   > **Lưu ý:** File `.env` chứa mật khẩu cá nhân và đã được đưa vào `.gitignore` để tránh bị lộ khi đẩy code lên GitHub.

### Bước 5: Khởi tạo Cơ sở dữ liệu MySQL
1. Mở MySQL (hoặc MySQL Workbench / XAMPP / phpMyAdmin) và tạo database:
   ```sql
   CREATE DATABASE IF NOT EXISTS restaurantdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. Chạy lệnh sau để tự động tạo cấu trúc các bảng và nạp dữ liệu mẫu ban đầu:
   ```bash
   python -m RestaurantApp.models
   ```
   Khi màn hình hiển thị:
   ```text
   Đã khởi tạo CSDL và nạp dữ liệu mẫu thành công!
   ```
   tức là cơ sở dữ liệu đã sẵn sàng.

### Bước 6: Khởi chạy ứng dụng Web
Chạy lệnh:
```bash
python -m RestaurantApp.index
```
Hoặc:
```bash
python RestaurantApp/index.py
```

Mở trình duyệt web và truy cập địa chỉ:
👉 **`http://127.0.0.1:5000/`**

---

## 4. Danh sách các màn hình và đường dẫn chức năng

| STT | Chức năng | Đường dẫn URL | Mô tả nghiệp vụ |
|:---:|:---|:---|:---|
| 1 | **Nhận đơn tại bàn** | `http://127.0.0.1:5000/` | Nhân viên chọn bàn, gọi món, tự động cộng dồn số lượng. Nhận thông báo toast khi bếp nấu xong. |
| 2 | **Bếp chế biến** | `http://127.0.0.1:5000/kitchen` | Bếp theo dõi món đang nấu, xác nhận hoàn tất món. Tự làm mới real-time mỗi 5s. |
| 3 | **Thanh toán hóa đơn** | `http://127.0.0.1:5000/cashier` | Chi tiết hóa đơn, giảm giá 5% (>500k), thuế VAT 10%, nút In hóa đơn và xác nhận thanh toán. |
| 4 | **Quản lý thực đơn** | `http://127.0.0.1:5000/admin-menu` | Quản lý món ăn: Thêm mới, Sửa giá/tên/mã món, Xóa món (kiểm tra mã duy nhất, giá > 0). |
| 5 | **Báo cáo doanh thu** | `http://127.0.0.1:5000/stats` | Thống kê doanh thu, bảng xếp hạng Top món bán chạy, bộ lọc Ngày/Tháng/Năm, Biểu đồ tròn Chart.js. |

---

## 5. Lưu ý bảo mật khi đẩy lên GitHub
- File `.gitignore` đã được cấu hình sẵn để chặn đẩy file `.env`, thư mục môi trường ảo `.venv/`, và các file bytecode `__pycache__/`.
- Khi người khác clone dự án về, họ chỉ cần làm theo **Bước 4** (sao chép `.env.example` thành `.env` và điền mật khẩu MySQL của máy họ) là có thể chạy ngay lập tức.
