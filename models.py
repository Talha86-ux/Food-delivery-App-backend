from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy_utils import ChoiceType
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    email = Column(String(80), unique=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)
    orders = relationship("Order", back_populates="user")


    def __repr__(self):
        return f"User(id={self.id}, username={self.username}"


class Order(Base):
    ORDER_STATUSES = (
        ('PENDING', 'pending'),
        ('IN_TRANSIT', 'in_transit'),
        ('DELIVERED', 'delivered')
    )

    PIZZA_SIZES = (
        ('SMALL', 'small'),
        ('MEDIUM', 'medium'),
        ('LARGE', 'large'),
        ('EXTRA_LARGE', 'extra_large')
    )
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, nullable=False)
    order_status = Column(ChoiceType(choices=ORDER_STATUSES), nullable=False, default='PENDING')
    pizza_size = Column(ChoiceType(choices=PIZZA_SIZES), nullable=False, default='SMALL')
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship("User", back_populates="orders")


    def __repr__(self):
        return f"Order(id={self.id})"
