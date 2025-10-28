from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from Database.getConnection import Base
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class Order(Base):
    __tablename__ = "orders"

    id_order = Column(String(50), primary_key=True, index=True)
    # user_client = Column(String(45), ForeignKey("user_client.id_user_client"))
    user_client = Column(String(45))
    combo = Column(String(45), nullable=True)
    payment_method = Column(String(45))
    delivery_mode = Column(String(45))
    price = Column(Float)
    status = Column(String(45))
    coupon = Column(String(45), nullable=True)
    order_notes = Column(String(255), nullable=True)
    local = Column(String(45))

    burgers = relationship("OrderBurger", back_populates="order")
    drinks = relationship("OrderDrinks", back_populates="order")
    fries = relationship("OrderFries", back_populates="order")
    extras = relationship("OrderExtra", back_populates="order")
    sins = relationship("OrderSin", back_populates="order")
    coupons = relationship("OrderCoupons", back_populates="order")
    client = relationship("OrderUserClient", back_populates="order")

class OrderBurger(Base):
    __tablename__ = "order_burger"

    id_order_burger = Column(String(50), primary_key=True, index=True)
    id_order = Column(String(50), ForeignKey("orders.id_order"))
    # id_burger = Column(String(50), ForeignKey("burger.id_burger"))
    id_burger = Column(String(50))

    order = relationship("Order", back_populates="burgers")

class OrderDrinks(Base):
    __tablename__ = "order_drinks"

    id_order_drinks = Column(String(50), primary_key=True, index=True)
    id_order = Column(String(50), ForeignKey("orders.id_order"))
    # id_drinks = Column(String(50), ForeignKey("drinks.id_drinks"))
    id_drinks = Column(String(50))

    order = relationship("Order", back_populates="drinks")

class OrderFries(Base):
    __tablename__ = "order_fries"

    id_order_fries = Column(String(50), primary_key=True, index=True)
    id_order = Column(String(50), ForeignKey("orders.id_order"))
    # id_fries = Column(String(50), ForeignKey("fries.id_fries"))
    id_fries = Column(String(50))

    order = relationship("Order", back_populates="fries")

class OrderExtra(Base):
    __tablename__ = "order_extra"

    id_order_extra = Column(String(50), primary_key=True, index=True)
    id_order = Column(String(50), ForeignKey("orders.id_order"))
    # id_extra = Column(String(50), ForeignKey("extras.id_extras"))
    id_extra = Column(String(50))

    order = relationship("Order", back_populates="extras")

class OrderSin(Base):
    __tablename__ = "order_sin"

    id_order_sin = Column(String(50), primary_key=True, index=True)
    id_order = Column(String(50), ForeignKey("orders.id_order"))
    # id_sin = Column(String(50), ForeignKey("sin.id_sin"))
    id_sin = Column(String(50))

    order = relationship("Order", back_populates="sins")

class OrderCoupons(Base):
    __tablename__ = "order_coupons"

    id_order_coupons = Column(String(50), primary_key=True, index=True)
    id_order = Column(String(50), ForeignKey("orders.id_order"))
    # id_coupons = Column(String(50), ForeignKey("coupons.id_coupons"))
    id_coupons = Column(String(50))

    order = relationship("Order", back_populates="coupons")

class OrderUserClient(Base):
    __tablename__ = "order_user_client"

    id_order_user_client = Column(String(50), primary_key=True, index=True)
    id_order = Column(String(50), ForeignKey("orders.id_order"))
    # id_user_client = Column(String(50), ForeignKey("user_client.id_user_client"))
    id_user_client = Column(String(50))

    order = relationship("Order", back_populates="client")

class OrderMan(BaseModel):
    id_order: Optional[str] = None
    payment_method: Optional[str] = None
    delivery_mode: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None
    order_notes: Optional[str] = None
    local: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[int] = None
    email: Optional[str] = None
    address: Optional[str] = None
    coupon: Optional[str] = None
    products: Optional[List[str]] = None