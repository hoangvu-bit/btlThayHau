from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from RestaurantApp import db, app
from datetime import datetime
import enum

class OrderStatus(enum.Enum):
    OPEN = "Đang mở"
    PAID = "Đã thanh toán"

class KitchenStatus(enum.Enum):
    COOKING = "Đang nấu"
    DONE = "Hoàn tất"

# 1. Nhóm món ăn
class Category(db.Model):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    is_kitchen = Column(Boolean, default=True)
    dishes = relationship('Dish', backref='category', lazy=True)

# 2. Món ăn
class Dish(db.Model):
    __tablename__ = 'dish'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, default=0)
    active = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)

# 3. Bàn ăn
class DiningTable(db.Model):
    __tablename__ = 'dining_table'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(20), nullable=False)
    is_occupied = Column(Boolean, default=False)

# 4. Phiếu gọi món / Hóa đơn
class Order(db.Model):
    __tablename__ = 'order'
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_id = Column(Integer, ForeignKey(DiningTable.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now)
    status = Column(Enum(OrderStatus), default=OrderStatus.OPEN)
    table = relationship('DiningTable', backref='orders')
    details = relationship('OrderDetail', backref='order', lazy=True)

# 5. Chi tiết phiếu gọi món
class OrderDetail(db.Model):
    __tablename__ = 'order_detail'
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey(Order.id), nullable=False)
    dish_id = Column(Integer, ForeignKey(Dish.id), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0)
    note = Column(String(255), default='')
    kitchen_status = Column(Enum(KitchenStatus), default=KitchenStatus.COOKING)

    dish = relationship('Dish')
    __table_args__ = (UniqueConstraint('order_id', 'dish_id', name='uk_order_dish'),)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if Category.query.count() == 0:
            c1 = Category(name="Món chế biến (Lẩu/Nướng)", is_kitchen=True)
            c2 = Category(name="Thức uống đóng chai", is_kitchen=False)
            db.session.add_all([c1, c2])
            db.session.commit()

            d1 = Dish(code="LAU01", name="Lẩu hải sản", price=250000, category_id=c1.id)
            d2 = Dish(code="NUOC01", name="Nước suối", price=10000, category_id=c2.id)
            db.session.add_all([d1, d2])

            for i in range(1, 7):
                db.session.add(DiningTable(id=i, name=f"{i:02d}"))
            db.session.commit()
            print("Đã khởi tạo CSDL và nạp dữ liệu mẫu thành công!")