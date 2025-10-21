from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND
from sqlalchemy.orm import Session
from models import Base, User, Seans, Plan
from database import engine, SessionLocal
from schemas import UserCreate, SeansBase, SeansOut, PlanBase
from auth import get_db, hash_password, verify_password
import uuid
import calendar
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from fastapi import Query
from datetime import date
from sqlalchemy.orm import joinedload
from fastapi_utils.tasks import repeat_every

app = FastAPI()
Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

sessions = {}

def get_user_from_session(request: Request, db: Session):  # POPRAWKA: dodano db
    token = request.cookies.get("session_token")
    if token and token in sessions:
        user = sessions[token]
        return db.query(User).filter(User.id == user.id).first()
    return None

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):  # POPRAWKA: dodano db
    user = get_user_from_session(request, db)              # POPRAWKA: przekazanie db
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "msg": ""})

@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "msg": "Nieprawidłowe dane"})
    token = str(uuid.uuid4())
    sessions[token] = user
    response = RedirectResponse("/", status_code=HTTP_302_FOUND)
    response.set_cookie("session_token", token)
    return response

@app.get("/logout")
def logout(request: Request):
    token = request.cookies.get("session_token")
    if token in sessions:
        del sessions[token]
    response = RedirectResponse("/", status_code=HTTP_302_FOUND)
    response.delete_cookie("session_token")
    return response

@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "msg": ""})

@app.post("/register", response_class=HTMLResponse)
def register_post(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("register.html", {"request": request, "msg": "Użytkownik już istnieje"})
    hashed = hash_password(password)
    db_user = User(username=username, hashed_password=hashed, role="widz")
    db.add(db_user)
    db.commit()
    return templates.TemplateResponse("login.html", {"request": request, "msg": "Zarejestrowano, zaloguj się"})

@app.get("/add_seans", response_class=HTMLResponse)
def add_seans_form(request: Request, db: Session = Depends(get_db)):  # POPRAWKA: dodano db
    user = get_user_from_session(request, db)                       # POPRAWKA: przekazanie db
    if not user or user.role != "operator":
        return RedirectResponse("/login", status_code=302)
    seanse = db.query(Seans).filter(Seans.operator_id == user.id).all()
    return templates.TemplateResponse("add_seans.html", {"request": request, "user": user, "seanse": seanse})

@app.post("/add_seans", response_class=HTMLResponse)
def add_seans_post(request: Request, tytul: str = Form(...), link: str = Form(...), pokoj: str = Form(...), data: str = Form(...), db: Session = Depends(get_db)):  # POPRAWKA: dodano db
    user = get_user_from_session(request, db)  # POPRAWKA: przekazanie db
    if not user or user.role != "operator":
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)
    try:
        data_dt = datetime.fromisoformat(data)
    except ValueError:
        return templates.TemplateResponse("add_seans.html", {"request": request, "user": user, "msg": "Niepoprawny format daty"})
    new_seans = Seans(tytul=tytul, link=link, pokoj=pokoj, data=data_dt, operator_id=user.id)
    db.add(new_seans)
    db.commit()
    return RedirectResponse("/calendar", status_code=HTTP_302_FOUND)

@app.get("/calendar", response_class=HTMLResponse)
def show_calendar(request: Request, db: Session = Depends(get_db)):
    user = get_user_from_session(request, db)
    if not user:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)
    # Filtrujemy tylko aktualne, niearchiwalne
    seanse = db.query(Seans).options(joinedload(Seans.attendees))\
        .filter(Seans.archiwalny == False).all()
    return templates.TemplateResponse("calendar.html", {"request": request, "user": user, "seanse": seanse})

@app.get("/plan", response_class=HTMLResponse)
def plan_form(request: Request, db: Session = Depends(get_db)):
    user = get_user_from_session(request, db)
    if not user:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    today = datetime.today()
    year = request.query_params.get("year")
    month = request.query_params.get("month")
    year = int(year) if year else today.year
    month = int(month) if month else today.month

    cal = calendar.Calendar(firstweekday=0)
    month_days = list(cal.itermonthdates(year, month))

    # Wszystkie plany w danym miesiącu z JOIN do użytkownika
    month_start = datetime(year, month, 1)
    month_end = datetime(year + (month == 12), month % 12 + 1, 1)
    all_plans = db.query(Plan).filter(Plan.data >= month_start, Plan.data < month_end).all()

    # mapowanie dat na plany (lista planów dla każdej daty)
    plans_per_day = {}
    for plan in all_plans:
        dt = plan.data.date()
        plans_per_day.setdefault(dt, []).append(plan)

    calendar_days = []
    for day in month_days:
        # sprawdzamy, czy bieżący user jest wśród osób, które planują ten dzień
        user_plan = next((p for p in plans_per_day.get(day, []) if p.user_id == user.id), None)
        calendar_days.append({
            "day": day.day,
            "date": day,
            "is_planned": bool(user_plan),
            "user_plan": user_plan,  # obiekt planu bieżącego usera lub None
            "plans": plans_per_day.get(day, [])  # lista wszystkich planów tego dnia
        })

    return templates.TemplateResponse(
        "plan_grid.html",
        {
            "request": request,
            "user": user,
            "calendar_days": calendar_days,
            "year": year,
            "month": month,
            "prev_year": year if month > 1 else year - 1,
            "prev_month": month - 1 if month > 1 else 12,
            "next_year": year if month < 12 else year + 1,
            "next_month": month + 1 if month < 12 else 1,
        }
    )


@app.post("/plan", response_class=HTMLResponse)
def plan_post(
    request: Request,
    add_plan: str = Form(None),
    delete_plan: str = Form(None),
    plan_date: str = Form(None),
    plan_time: str = Form(None),
    plan_id: int = Form(None),
    db: Session = Depends(get_db)
):
    user = get_user_from_session(request, db)
    if not user:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    if add_plan and plan_date and plan_time:
        try:
            data_dt = datetime.strptime(plan_date + " " + plan_time, "%Y-%m-%d %H:%M")
        except Exception:
            return RedirectResponse("/plan", status_code=HTTP_302_FOUND)
        new_plan = Plan(user_id=user.id, data=data_dt)
        db.add(new_plan)
        db.commit()
    elif delete_plan and plan_id:
        plan = db.query(Plan).filter(Plan.id == plan_id, Plan.user_id == user.id).first()
        if plan:
            db.delete(plan)
            db.commit()

    # po operacji wraca na wybraną stronę (możesz dodać parametr `next`)
    return RedirectResponse("/plan", status_code=HTTP_302_FOUND)


@app.get("/users", response_class=HTMLResponse)
def show_users(request: Request, data: date = Query(None), db: Session = Depends(get_db)):  # POPRAWKA: dodano db
    user = get_user_from_session(request, db)                  # POPRAWKA: przekazanie db
    if not user or user.role not in ("operator", "widz", "admin"):
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    if user.role == "admin":
        users = db.query(User).all()
    else:
        if data:
            start_dt = datetime.combine(data, datetime.min.time())
            end_dt = datetime.combine(data, datetime.max.time())
            users = (
                db.query(User)
                .join(Plan)
                .filter(Plan.data >= start_dt, Plan.data <= end_dt)
                .distinct()
                .all()
            )
        else:
            users = (
                db.query(User)
                .join(Plan)
                .distinct()
                .all()
            )
    return templates.TemplateResponse("users.html", {"request": request, "user": user, "users": users, "selected_date": data})

@app.get("/combined", response_class=HTMLResponse)
def show_combined(
    request: Request,
    year: int = None,
    month: int = None,
    db: Session = Depends(get_db)  # POPRAWKA: dodano db
):
    user = get_user_from_session(request, db)                 # POPRAWKA: przekazanie db
    if not user:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    today = datetime.today()
    year = year or today.year
    month = month or today.month

    start_dt = datetime(year, month, 1)
    if month == 12:
        end_dt = datetime(year + 1, 1, 1)
    else:
        end_dt = datetime(year, month + 1, 1)

    seanse = (
        db.query(Seans)
        .options(joinedload(Seans.attendees))
        .filter(Seans.data >= start_dt, Seans.data < end_dt, Seans.archiwalny == False)
        .order_by(Seans.data)
        .all()
    )

    cal = calendar.Calendar(firstweekday=0)
    month_days = list(cal.itermonthdates(year, month))
    seanse_per_day = {}
    for s in seanse:
        seans_day = s.data.date()
        seanse_per_day.setdefault(seans_day, []).append(s)

    calendar_days = []
    for day in month_days:
        calendar_days.append({
            "day": day.day,
            "date": day,
            "seanse": seanse_per_day.get(day, [])
        })

    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    if user.role == "admin":
        users = db.query(User).all()
    else:
        users = (
            db.query(User)
            .join(Plan)
            .filter(Plan.data >= start_dt, Plan.data < end_dt)
            .distinct()
            .all()
        )

    return templates.TemplateResponse(
        "combined.html",
        {
            "request": request,
            "user": user,
            "calendar_days": calendar_days,
            "year": year,
            "month": month,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "users": users,
            "selected_date": None
        }
    )

@app.post("/plan/delete", response_class=HTMLResponse)
def delete_plan(request: Request, plan_id: int = Form(...), db: Session = Depends(get_db)):  # POPRAWKA: dodano db
    user = get_user_from_session(request, db)                                                   # POPRAWKA: przekazanie db
    if not user:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.user_id == user.id).first()
    if not plan:
        return templates.TemplateResponse("plan.html", {"request": request, "user": user, "plans": user.plans, "msg": "Nie znaleziono dnia do usunięcia"})
    db.delete(plan)
    db.commit()
    return RedirectResponse("/plan", status_code=HTTP_302_FOUND)

@app.post("/seans/delete", response_class=HTMLResponse)
def delete_seans(request: Request, seans_id: int = Form(...), db: Session = Depends(get_db)):  # POPRAWKA: dodano db
    user = get_user_from_session(request, db)                                                 # POPRAWKA: przekazanie db
    if not user or user.role != "operator":
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)
    seans = db.query(Seans).filter(Seans.id == seans_id, Seans.operator_id == user.id).first()
    if not seans:
        seanse = db.query(Seans).filter(Seans.operator_id == user.id).all()
        return templates.TemplateResponse("add_seans.html", {"request": request, "user": user, "msg": "Nie znaleziono seansu do usunięcia", "seanse": seanse})
    db.delete(seans)
    db.commit()
    return RedirectResponse("/calendar", status_code=HTTP_302_FOUND)

@app.post("/seans/attendance", response_class=HTMLResponse)
def toggle_attendance(request: Request, seans_id: int = Form(...), next: str = Form(None), db: Session = Depends(get_db)):  # POPRAWKA: dodano db
    user = get_user_from_session(request, db)                                                    # POPRAWKA: przekazanie db
    if not user:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)
    seans = db.query(Seans).filter(Seans.id == seans_id).first()
    if not seans:
        redirect_url = next if next else "/calendar"
        return RedirectResponse(redirect_url, status_code=HTTP_302_FOUND)

    if user in seans.attendees:
        seans.attendees.remove(user)
    else:
        seans.attendees.append(user)

    db.commit()

    redirect_url = next if next else "/calendar"
    return RedirectResponse(redirect_url, status_code=HTTP_302_FOUND)

@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request, db: Session = Depends(get_db)):
    user = get_user_from_session(request, db)
    if not user or user.username != "admin":
        return RedirectResponse("/", status_code=HTTP_302_FOUND)
    users = db.query(User).filter(User.username != "admin").all()
    return templates.TemplateResponse("admin.html", {"request": request, "user": user, "users": users})

@app.post("/admin/change_role")
def change_user_role(
    request: Request,
    user_id: int = Form(...),
    new_role: str = Form(...),
    db: Session = Depends(get_db)
):
    # Pobierz aktualnego użytkownika sesji
    current_user = get_user_from_session(request, db)
    # Sprawdzenie czy jest adminem
    if not current_user or current_user.username != "admin":
        return RedirectResponse("/", status_code=HTTP_302_FOUND)
    # Pobierz użytkownika do zmiany
    target_user = db.query(User).filter(User.id == user_id).first()
    if target_user and new_role in ("operator", "widz"):
        target_user.role = new_role
        db.commit()
    # Przekieruj z powrotem do panelu admina
    return RedirectResponse("/admin", status_code=HTTP_302_FOUND)

@app.on_event("startup")
@repeat_every(seconds=3600)  # co godzinę
def move_old_seans_to_archive():
    db = SessionLocal()
    try:
        now = datetime.now()
        old_seanse = db.query(Seans).filter(Seans.data < now, Seans.archiwalny == False).all()
        for seans in old_seanse:
            seans.archiwalny = True
        db.commit()

        # Usuwanie starych planów użytkowników (przeszłe dni)
        old_plans = db.query(Plan).filter(Plan.data < now).all()
        for plan in old_plans:
            db.delete(plan)
        db.commit()
    finally:
        db.close()

@app.get("/archiwum", response_class=HTMLResponse)
def show_archive(request: Request, db: Session = Depends(get_db)):
    user = get_user_from_session(request, db)
    if not user:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)
    seanse = db.query(Seans).options(joinedload(Seans.attendees))\
        .filter(Seans.archiwalny == True)\
        .order_by(Seans.data.desc()).all()
    return templates.TemplateResponse("archive.html", {"request": request, "user": user, "seanse": seanse})

@app.post("/admin/delete_user")
def delete_user(user_id: int = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return RedirectResponse("/admin", status_code=303)

@app.on_event("startup")
def create_admin():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        hashed = hash_password("kinobabilon")
        admin = User(username="admin", hashed_password=hashed, role="admin")
        db.add(admin)
        db.commit()
    db.close()
