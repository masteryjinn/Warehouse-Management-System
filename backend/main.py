from fastapi import FastAPI
from routes.password import password_router  # Імпортуємо маршрути з файлу password.py
from routes.products import products_router  # Імпортуємо маршрути з файлу products.py
from routes.user_info import user_router  # Імпортуємо маршрути з файлу user_info.py
from routes.authorization import authorization_router  # Імпортуємо маршрути з файлу authorization.py
from routes.employees import employees_router  # Імпортуємо маршрути з файлу employees.py
from routes.customers import customers_router  # Імпортуємо маршрути з файлу customers.py
from routes.suppliers import suppliers_router  # Імпортуємо маршрути з файлу suppliers.py
from routes.warehouse import warehouse_router
from routes.orders import orders_router
from routes.stock_movements import stock_movements_router
from routes.reports import report_router
from routes.import_data import import_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # або вкажи конкретні домени, наприклад: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Реєструємо маршрути
app.include_router(password_router)
app.include_router(products_router) 
app.include_router(user_router)
app.include_router(authorization_router)
app.include_router(employees_router)
app.include_router(customers_router)
app.include_router(suppliers_router)
app.include_router(warehouse_router)
app.include_router(orders_router)
app.include_router(stock_movements_router)
app.include_router(report_router)
app.include_router(import_router)