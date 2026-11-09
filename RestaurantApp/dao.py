from RestaurantApp.models import Category, Dish, DiningTable, Order, OrderDetail, OrderStatus, KitchenStatus
from RestaurantApp import db
from sqlalchemy import func, extract

# --- HÀM ĐỌC DỮ LIỆU ---
def load_categories():
    return Category.query.all()

def load_dishes(cate_id=None, kw=None):
    query = Dish.query.filter(Dish.active.__eq__(True))
    if cate_id:
        query = query.filter(Dish.category_id.__eq__(int(cate_id)))
    if kw:
        query = query.filter(Dish.name.contains(kw))
    return query.all()

def get_dish_by_id(dish_id):
    return Dish.query.get(dish_id)

def load_tables():
    return DiningTable.query.order_by(DiningTable.id).all()

def get_open_order_by_table(table_id):
    """Quy định Yêu cầu 1: Mỗi bàn chỉ có 1 phiếu mở cùng lúc"""
    return Order.query.filter(
        Order.table_id.__eq__(table_id),
        Order.status.__eq__(OrderStatus.OPEN)
    ).first()

# --- YÊU CẦU 1: NHẬN ĐƠN TẠI BÀN (CỘNG DỒN SỐ LƯỢNG) ---
def add_dish_to_table(table_id, dish_id, quantity, note=""):
    try:
        qty = int(quantity)
    except (ValueError, TypeError):
        raise ValueError("Số lượng món ăn phải là số nguyên!")

    if qty <= 0:
        raise ValueError("Số lượng món ăn phải lớn hơn 0!")

    dish = Dish.query.get(dish_id)
    if not dish or not dish.active:
        raise ValueError("Món ăn không tồn tại hoặc đã ngừng kinh doanh!")

    order = get_open_order_by_table(table_id)
    if not order:
        order = Order(table_id=table_id, status=OrderStatus.OPEN)
        db.session.add(order)
        table = DiningTable.query.get(table_id)
        if table:
            table.is_occupied = True
        db.session.flush()

    detail = OrderDetail.query.filter_by(order_id=order.id, dish_id=dish.id).first()
    initial_status = KitchenStatus.COOKING if dish.category.is_kitchen else KitchenStatus.DONE

    if detail:
        # Nếu đã có trong phiếu: Tự động cộng dồn số lượng
        detail.quantity += qty
        if note:
            detail.note = note
        # Nếu là món bếp thì chuyển trạng thái về Đang nấu để bếp chế biến tiếp
        if dish.category.is_kitchen:
            detail.kitchen_status = KitchenStatus.COOKING
    else:
        detail = OrderDetail(
            order_id=order.id,
            dish_id=dish.id,
            quantity=qty,
            unit_price=dish.price,
            note=note,
            kitchen_status=initial_status
        )
        db.session.add(detail)

    db.session.commit()
    return order

# --- YÊU CẦU 2: BẾP NHẬN DANH SÁCH CHẾ BIẾN ---
def load_kitchen_pending_items():
    """Quy định: Bếp chỉ thấy đơn chưa hoàn tất (COOKING) và thuộc nhóm cần nấu"""
    return OrderDetail.query.join(Order).join(Dish).join(Category).filter(
        Order.status.__eq__(OrderStatus.OPEN),
        Category.is_kitchen.__eq__(True),
        OrderDetail.kitchen_status.__eq__(KitchenStatus.COOKING)
    ).order_by(Order.created_date.asc()).all()

def complete_kitchen_item(detail_id):
    detail = OrderDetail.query.get(detail_id)
    if detail:
        detail.kitchen_status = KitchenStatus.DONE
        db.session.commit()
    return detail

# --- YÊU CẦU 3: TÍNH TIỀN & THANH TOÁN HÓA ĐƠN ---
def calculate_bill(order_id):
    order = Order.query.get(order_id)
    if not order:
        return None

    sub_total = sum(d.quantity * d.unit_price for d in order.details)
    discount = sub_total * 0.05 if sub_total > 500000 else 0
    after_discount = sub_total - discount
    vat = after_discount * 0.10
    final_total = after_discount + vat

    return {
        "sub_total": sub_total,
        "discount": discount,
        "vat": vat,
        "final_total": final_total
    }

def pay_order(table_id):
    order = get_open_order_by_table(table_id)
    if not order:
        raise ValueError("Bàn này hiện không có hóa đơn nào cần thanh toán!")
    order.status = OrderStatus.PAID
    table = DiningTable.query.get(table_id)
    if table:
        table.is_occupied = False
    db.session.commit()
    return True

# --- YÊU CẦU 4: QUẢN LÝ THỰC ĐƠN (THÊM / SỬA / XÓA) ---
def create_or_update_dish(code, name, price, category_id, dish_id=None):
    if not code or not str(code).strip():
        raise ValueError("Quy định: Mã món ăn không được để trống!")

    if not name or not str(name).strip():
        raise ValueError("Quy định: Tên món ăn không được để trống!")

    try:
        price_val = float(price)
    except (ValueError, TypeError):
        raise ValueError("Quy định: Đơn giá món ăn phải là chữ số hợp lệ!")

    if price_val <= 0:
        raise ValueError("Quy định: Đơn giá món ăn phải lớn hơn 0 (> 0)!")

    cate = Category.query.get(category_id)
    if not cate:
        raise ValueError("Quy định: Nhóm món (Category) không hợp lệ!")

    clean_code = str(code).strip()
    clean_name = str(name).strip()

    # Ràng buộc: Mã món ăn phải duy nhất
    existing = Dish.query.filter_by(code=clean_code).first()
    if existing and (not dish_id or existing.id != int(dish_id)):
        raise ValueError(f"Quy định: Mã món '{clean_code}' đã tồn tại! Vui lòng chọn mã khác.")

    if dish_id:
        dish = Dish.query.get(dish_id)
        if not dish:
            raise ValueError("Món ăn cần cập nhật không tồn tại!")
        dish.code = clean_code
        dish.name = clean_name
        dish.price = price_val
        dish.category_id = int(category_id)
        dish.active = True
    else:
        dish = Dish(code=clean_code, name=clean_name, price=price_val, category_id=int(category_id))
        db.session.add(dish)

    db.session.commit()
    return dish

def delete_dish(dish_id):
    dish = Dish.query.get(dish_id)
    if not dish:
        raise ValueError("Món ăn không tồn tại!")

    # Nếu món ăn đã từng nằm trong hóa đơn gọi món, soft-delete để bảo toàn lịch sử hóa đơn
    has_orders = OrderDetail.query.filter_by(dish_id=dish.id).first()
    if has_orders:
        dish.active = False
    else:
        db.session.delete(dish)

    db.session.commit()
    return True

# --- YÊU CẦU 5: BÁO CÁO DOANH THU & THỐNG KÊ ---
def get_revenue_stats(date_str=None, month=None, year=None):
    """
    Truy vấn tổng doanh thu từ các hóa đơn đã thanh toán (OrderStatus.PAID)
    Hỗ trợ lọc theo:
    - Ngày cụ thể: date_str (YYYY-MM-DD)
    - Tháng và Năm: month (1-12), year (YYYY)
    - Chỉ Năm: year (YYYY)
    """
    query = Order.query.filter(Order.status == OrderStatus.PAID)

    if date_str:
        query = query.filter(func.date(Order.created_date) == date_str)
    elif month and year:
        query = query.filter(
            extract('month', Order.created_date) == int(month),
            extract('year', Order.created_date) == int(year)
        )
    elif year:
        query = query.filter(extract('year', Order.created_date) == int(year))

    paid_orders = query.all()
    total_orders = len(paid_orders)
    total_revenue = 0
    total_sub_total = 0
    total_discount = 0
    total_vat = 0
    total_items = 0

    for order in paid_orders:
        bill = calculate_bill(order.id)
        if bill:
            total_sub_total += bill['sub_total']
            total_discount += bill['discount']
            total_vat += bill['vat']
            total_revenue += bill['final_total']
        for d in order.details:
            total_items += d.quantity

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_items": total_items,
        "total_sub_total": total_sub_total,
        "total_discount": total_discount,
        "total_vat": total_vat
    }

def get_top_dishes_stats(date_str=None, month=None, year=None, limit=10):
    """
    Truy vấn Top món ăn bán chạy từ các hóa đơn đã thanh toán (PAID)
    Trả về: tên món, tổng số lượng bán, tổng doanh thu, tỷ lệ phần trăm
    """
    # 1. Tính tổng doanh thu toàn bộ món trong kỳ lọc để tính phần trăm
    total_revenue_query = db.session.query(
        func.sum(OrderDetail.quantity * OrderDetail.unit_price)
    ).join(Order, OrderDetail.order_id == Order.id)\
     .filter(Order.status == OrderStatus.PAID)

    if date_str:
        total_revenue_query = total_revenue_query.filter(func.date(Order.created_date) == date_str)
    elif month and year:
        total_revenue_query = total_revenue_query.filter(
            extract('month', Order.created_date) == int(month),
            extract('year', Order.created_date) == int(year)
        )
    elif year:
        total_revenue_query = total_revenue_query.filter(extract('year', Order.created_date) == int(year))

    total_period_revenue = total_revenue_query.scalar() or 0

    # 2. Truy vấn chi tiết theo từng món ăn
    query = db.session.query(
        Dish.id.label('dish_id'),
        Dish.code.label('dish_code'),
        Dish.name.label('dish_name'),
        Category.name.label('category_name'),
        func.sum(OrderDetail.quantity).label('total_quantity'),
        func.sum(OrderDetail.quantity * OrderDetail.unit_price).label('total_revenue')
    ).join(Order, OrderDetail.order_id == Order.id)\
     .join(Dish, OrderDetail.dish_id == Dish.id)\
     .join(Category, Dish.category_id == Category.id)\
     .filter(Order.status == OrderStatus.PAID)

    if date_str:
        query = query.filter(func.date(Order.created_date) == date_str)
    elif month and year:
        query = query.filter(
            extract('month', Order.created_date) == int(month),
            extract('year', Order.created_date) == int(year)
        )
    elif year:
        query = query.filter(extract('year', Order.created_date) == int(year))

    query = query.group_by(Dish.id, Dish.code, Dish.name, Category.name)\
                 .order_by(func.sum(OrderDetail.quantity * OrderDetail.unit_price).desc())

    if limit:
        rows = query.limit(limit).all()
    else:
        rows = query.all()

    top_dishes = []
    for r in rows:
        rev = float(r.total_revenue or 0)
        qty = int(r.total_quantity or 0)
        pct = round((rev / total_period_revenue * 100), 1) if total_period_revenue > 0 else 0
        top_dishes.append({
            "dish_id": r.dish_id,
            "dish_code": r.dish_code,
            "name": r.dish_name,
            "category_name": r.category_name,
            "quantity": qty,
            "revenue": rev,
            "percentage": pct
        })

    return top_dishes
