from flask import render_template, request, redirect, url_for, flash, jsonify
from RestaurantApp import app, dao
from RestaurantApp.models import KitchenStatus
from datetime import datetime

# ==============================================================================
# MÀN HÌNH 1: NHẬN ĐƠN TẠI BÀN (YÊU CẦU 1)
# ==============================================================================
@app.route("/", methods=["GET", "POST"])
def index():
    err_msg = None
    selected_table_id = request.args.get("table_id", 1, type=int)

    if request.method == "POST":
        try:
            selected_table_id = int(request.form.get("table_id"))
            dish_id = int(request.form.get("dish_id"))
            quantity = int(request.form.get("quantity", 1))
            note = request.form.get("note", "")
            dao.add_dish_to_table(selected_table_id, dish_id, quantity, note)
            return redirect(url_for("index", table_id=selected_table_id))
        except Exception as ex:
            err_msg = str(ex)

    tables = dao.load_tables()
    # Nếu bàn được chọn không nằm trong danh sách, lấy bàn đầu tiên
    if tables and not any(t.id == selected_table_id for t in tables):
        selected_table_id = tables[0].id

    dishes = dao.load_dishes()
    current_order = dao.get_open_order_by_table(selected_table_id)
    return render_template("index.html", tables=tables, dishes=dishes,
                           selected_table_id=selected_table_id,
                           current_order=current_order, err_msg=err_msg)

# API Polling đồng bộ trạng thái món với Bếp theo thời gian thực
@app.route("/api/table/<int:table_id>/status")
def api_table_status(table_id):
    order = dao.get_open_order_by_table(table_id)
    if not order:
        return jsonify({"has_order": False, "done_items_count": 0, "done_items": []})

    done_items = []
    for d in order.details:
        if d.kitchen_status == KitchenStatus.DONE and d.dish.category.is_kitchen:
            done_items.append({
                "id": d.id,
                "dish_name": d.dish.name,
                "quantity": d.quantity
            })

    return jsonify({
        "has_order": True,
        "order_id": order.id,
        "done_items_count": len(done_items),
        "done_items": done_items
    })


# ==============================================================================
# MÀN HÌNH 2: BẾP NHẬN DANH SÁCH CHẾ BIẾN (YÊU CẦU 2)
# ==============================================================================
@app.route("/kitchen", methods=["GET", "POST"])
def kitchen():
    if request.method == "POST":
        detail_id = request.form.get("detail_id")
        dao.complete_kitchen_item(detail_id)
        return redirect(url_for("kitchen"))

    pending_items = dao.load_kitchen_pending_items()
    return render_template("kitchen.html", pending_items=pending_items)


# ==============================================================================
# MÀN HÌNH 3: THANH TOÁN HÓA ĐƠN (YÊU CẦU 3)
# ==============================================================================
@app.route("/cashier", methods=["GET", "POST"])
def cashier():
    selected_table_id = request.args.get("table_id", 1, type=int)
    msg = None

    if request.method == "POST":
        try:
            dao.pay_order(selected_table_id)
            msg = f"Đã thanh toán thành công cho Bàn {selected_table_id:02d}!"
        except Exception as ex:
            msg = str(ex)

    tables = dao.load_tables()
    if tables and not any(t.id == selected_table_id for t in tables):
        selected_table_id = tables[0].id

    current_order = dao.get_open_order_by_table(selected_table_id)
    bill = dao.calculate_bill(current_order.id) if current_order else None
    return render_template("cashier.html", tables=tables, selected_table_id=selected_table_id,
                           current_order=current_order, bill=bill, msg=msg)


# ==============================================================================
# MÀN HÌNH 4: QUẢN LÝ THỰC ĐƠN (YÊU CẦU 4)
# ==============================================================================
@app.route("/admin-menu", methods=["GET", "POST"])
@app.route("/admin/menu", methods=["GET", "POST"])
def admin_menu():
    err_msg = None
    success_msg = None
    edit_id = request.args.get("edit_id", type=int)
    edit_dish = dao.get_dish_by_id(edit_id) if edit_id else None

    if request.method == "POST":
        try:
            dish_id = request.form.get("dish_id")
            code = request.form.get("code")
            name = request.form.get("name")
            price = request.form.get("price")
            category_id = request.form.get("category_id")

            dao.create_or_update_dish(code, name, price, category_id, dish_id)
            if dish_id:
                flash(f"Đã cập nhật món ăn '{name}' thành công!", "success")
            else:
                flash(f"Đã thêm món ăn mới '{name}' thành công!", "success")
            return redirect(url_for("admin_menu"))
        except Exception as ex:
            err_msg = str(ex)

    categories = dao.load_categories()
    dishes = dao.load_dishes()
    return render_template("admin_menu.html", categories=categories, dishes=dishes,
                           edit_dish=edit_dish, err_msg=err_msg, success_msg=success_msg)

@app.route("/admin-menu/delete/<int:dish_id>", methods=["POST"])
@app.route("/admin/menu/delete/<int:dish_id>", methods=["POST"])
def delete_dish(dish_id):
    try:
        dao.delete_dish(dish_id)
        flash("Đã xóa món ăn khỏi thực đơn thành công!", "success")
    except Exception as ex:
        flash(f"Lỗi khi xóa món: {str(ex)}", "danger")
    return redirect(url_for("admin_menu"))


# ==============================================================================
# MÀN HÌNH 5: BÁO CÁO DOANH THU & THỐNG KÊ (YÊU CẦU 5)
# ==============================================================================
@app.route("/stats")
def stats():
    filter_type = request.args.get("filter_type", "all")
    date_param = request.args.get("date", "").strip()
    month_param = request.args.get("month", type=int)
    year_param = request.args.get("year", type=int)

    # Xử lý tham số lọc
    date_val = None
    month_val = None
    year_val = None

    if filter_type == "date" and date_param:
        date_val = date_param
    elif filter_type == "month":
        month_val = month_param
        year_val = year_param if year_param else datetime.now().year
    elif filter_type == "year" and year_param:
        year_val = year_param
    elif date_param:
        filter_type = "date"
        date_val = date_param
    elif month_param and year_param:
        filter_type = "month"
        month_val = month_param
        year_val = year_param

    # Truy vấn dữ liệu thống kê từ dao.py
    revenue_stats = dao.get_revenue_stats(date_str=date_val, month=month_val, year=year_val)
    top_dishes = dao.get_top_dishes_stats(date_str=date_val, month=month_val, year=year_val)

    return render_template("stats.html",
                           revenue_stats=revenue_stats,
                           top_dishes=top_dishes,
                           filter_type=filter_type,
                           current_date=date_val or "",
                           current_month=month_val or datetime.now().month,
                           current_year=year_val or datetime.now().year)

if __name__ == "__main__":
    app.run(debug=True)
