from fastapi import FastAPI
from app.routes.products import router as product_router
from app.routes.categories import router as category_router
from app.routes.admin import router as admin_router

from fastapi.staticfiles import StaticFiles
from app.routes.admin_products import router as admin_products_router
from app.routes.pages import router as pages_router
from app.routes.enquiries import router as enquiry_router
from app.routes.auth import router as auth_router


from app.routes.customer_auth import router as customer_auth_router
from app.routes.profile import router as profile_router
from app.routes.orders import router as orders_router
from app.routes.payments import router as payments_router
from app.routes.cms import router as cms_router

app = FastAPI(
    title="Intra Aura API",
    description="Backend API for Intra Aura",
    version="1.0.0"
)




app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

app.include_router(pages_router)

app.include_router(category_router)
app.include_router(product_router)
app.include_router(admin_router)
app.include_router(admin_products_router)
app.include_router(enquiry_router)
app.include_router(auth_router)
# CUSTOMER ACCOUNT
app.include_router(customer_auth_router)
app.include_router(profile_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(cms_router)