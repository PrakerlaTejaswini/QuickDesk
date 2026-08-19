from datetime import datetime

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)

from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import (
    Base,
    engine,
    get_db,
)

from .models import (
    User,
    Ticket,
    OverrideAudit,
)

from .schemas import (
    LoginRequest,
    TicketCreate,
    TicketReply,
    TicketOverride,
)

from .auth import (
    verify_password,
    create_access_token,
    get_current_user,
    require_role,
)

from .ai import (
    classify_ticket,
    ALLOWED_CATEGORIES,
    ALLOWED_PRIORITIES,
)

from .rag import rag_engine
from .ws import manager
from .config import settings


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="QuickDesk API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():
    return {
        "status": "ok"
    }


# ============================================================
# LOGIN - FRONTEND JSON LOGIN
# ============================================================

@app.post("/api/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Normal JSON login used by the frontend.

    Example:

    {
        "email": "employee@quickdesk.local",
        "password": "employee123"
    }
    """

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token(user)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
    }


# ============================================================
# OAUTH2 TOKEN - SWAGGER AUTHORIZE
# ============================================================

@app.post("/api/token")
def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    OAuth2 login endpoint used by Swagger Authorize.

    Swagger sends:

    username = employee@quickdesk.local
    password = employee123
    """

    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    if not verify_password(
        form_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# ============================================================
# EMPLOYEE - CREATE TICKET
# ============================================================

@app.post("/api/tickets")
async def create_ticket(
    data: TicketCreate,
    user: User = Depends(
        require_role("employee")
    ),
    db: Session = Depends(get_db),
):
    ai_result = classify_ticket(
        data.title,
        data.description,
    )

    ticket = Ticket(
        employee_id=user.id,
        title=data.title,
        description=data.description,
        attachment_filename=data.attachment_filename,

        category=ai_result["category"],
        priority=ai_result["priority"],

        ai_category=ai_result["category"],
        ai_priority=ai_result["priority"],

        status="Open",
    )

    db.add(ticket)

    db.commit()

    db.refresh(ticket)

    await manager.broadcast({
        "type": "ticket_created",
        "ticket_id": ticket.id,
    })

    return serialize_ticket(ticket)


# ============================================================
# EMPLOYEE - MY TICKETS
# ============================================================

@app.get("/api/my-tickets")
def my_tickets(
    user: User = Depends(
        require_role("employee")
    ),
    db: Session = Depends(get_db),
):
    tickets = db.query(Ticket).filter(
        Ticket.employee_id == user.id
    ).order_by(
        Ticket.created_at.desc()
    ).all()

    return [
        serialize_ticket(ticket)
        for ticket in tickets
    ]


# ============================================================
# AGENT - ALL TICKETS
# ============================================================

@app.get("/api/tickets")
def all_tickets(
    status: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    search: str | None = None,

    user: User = Depends(
        require_role("agent")
    ),

    db: Session = Depends(get_db),
):
    query = db.query(Ticket)

    if status:
        query = query.filter(
            Ticket.status == status
        )

    if category:
        query = query.filter(
            Ticket.category == category
        )

    if priority:
        query = query.filter(
            Ticket.priority == priority
        )

    if search:
        query = query.filter(
            Ticket.title.ilike(
                f"%{search}%"
            )
        )

    tickets = query.order_by(
        Ticket.created_at.desc()
    ).all()

    return [
        serialize_ticket(ticket)
        for ticket in tickets
    ]


# ============================================================
# TICKET DETAIL
# ============================================================

@app.get("/api/tickets/{ticket_id}")
def ticket_detail(
    ticket_id: int,

    user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    # Employee can only see own tickets
    if (
        user.role == "employee"
        and ticket.employee_id != user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You can only view your own tickets",
        )

    return serialize_ticket(ticket)


# ============================================================
# AGENT - GENERATE AI DRAFT
# ============================================================

@app.post(
    "/api/tickets/{ticket_id}/draft"
)
def generate_draft(
    ticket_id: int,

    user: User = Depends(
        require_role("agent")
    ),

    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    result = rag_engine.generate_draft(
        ticket.title,
        ticket.description,
    )

    ticket.ai_draft = result["draft"]

    ticket.citations = ",".join(
        result["citations"]
    )

    db.commit()

    return {
        "draft": ticket.ai_draft,
        "citations": result["citations"],
    }


# ============================================================
# AGENT - OVERRIDE AI VALUES
# ============================================================

@app.patch(
    "/api/tickets/{ticket_id}/override"
)
def override_ticket(
    ticket_id: int,

    data: TicketOverride,

    user: User = Depends(
        require_role("agent")
    ),

    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    # -------------------------
    # CATEGORY OVERRIDE
    # -------------------------

    if data.category:

        if data.category not in ALLOWED_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail="Invalid category",
            )

        if data.category != ticket.category:

            audit = OverrideAudit(
                ticket_id=ticket.id,
                agent_id=user.id,
                field="category",
                old_value=ticket.category,
                new_value=data.category,
            )

            db.add(audit)

            ticket.category = data.category

    # -------------------------
    # PRIORITY OVERRIDE
    # -------------------------

    if data.priority:

        if data.priority not in ALLOWED_PRIORITIES:
            raise HTTPException(
                status_code=400,
                detail="Invalid priority",
            )

        if data.priority != ticket.priority:

            audit = OverrideAudit(
                ticket_id=ticket.id,
                agent_id=user.id,
                field="priority",
                old_value=ticket.priority,
                new_value=data.priority,
            )

            db.add(audit)

            ticket.priority = data.priority

    db.commit()

    return serialize_ticket(ticket)


# ============================================================
# AGENT - REPLY AND RESOLVE
# ============================================================

@app.post(
    "/api/tickets/{ticket_id}/reply"
)
async def reply_ticket(
    ticket_id: int,

    data: TicketReply,

    user: User = Depends(
        require_role("agent")
    ),

    db: Session = Depends(get_db),
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    ticket.final_reply = data.reply

    ticket.status = "Resolved"

    ticket.resolved_at = datetime.utcnow()

    db.commit()

    await manager.broadcast({
        "type": "ticket_resolved",
        "ticket_id": ticket.id,
        "employee_id": ticket.employee_id,
    })

    return serialize_ticket(ticket)


# ============================================================
# AGENT - AUDIT LOG
# ============================================================

@app.get(
    "/api/tickets/{ticket_id}/audits"
)
def audits(
    ticket_id: int,

    user: User = Depends(
        require_role("agent")
    ),

    db: Session = Depends(get_db),
):
    records = db.query(
        OverrideAudit
    ).filter(
        OverrideAudit.ticket_id == ticket_id
    ).order_by(
        OverrideAudit.created_at.desc()
    ).all()

    return [
        {
            "id": item.id,
            "field": item.field,
            "old_value": item.old_value,
            "new_value": item.new_value,
            "agent_id": item.agent_id,
            "created_at": item.created_at,
        }
        for item in records
    ]


# ============================================================
# AGENT - METRICS
# ============================================================

@app.get("/api/metrics")
def metrics(
    user: User = Depends(
        require_role("agent")
    ),

    db: Session = Depends(get_db),
):
    total = db.query(
        func.count(Ticket.id)
    ).scalar() or 0

    open_count = db.query(
        func.count(Ticket.id)
    ).filter(
        Ticket.status == "Open"
    ).scalar() or 0

    resolved_count = db.query(
        func.count(Ticket.id)
    ).filter(
        Ticket.status == "Resolved"
    ).scalar() or 0

    category_rows = db.query(
        Ticket.category,
        func.count(Ticket.id),
    ).group_by(
        Ticket.category
    ).all()

    categories = {
        category: count
        for category, count in category_rows
    }

    override_count = db.query(
        func.count(OverrideAudit.id)
    ).filter(
        OverrideAudit.field == "category"
    ).scalar() or 0

    override_percentage = (
        override_count / total * 100
        if total
        else 0
    )

    return {
        "total": total,

        "status": {
            "Open": open_count,
            "Resolved": resolved_count,
        },

        "categories": categories,

        "category_override_percentage":
            round(
                override_percentage,
                2,
            ),
    }


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):
    await manager.connect(websocket)

    try:

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:

        manager.disconnect(websocket)


# ============================================================
# SERIALIZER
# ============================================================

def serialize_ticket(ticket: Ticket):

    return {
        "id": ticket.id,

        "employee_id":
            ticket.employee_id,

        "employee_name": (
            ticket.employee.name
            if ticket.employee
            else None
        ),

        "title":
            ticket.title,

        "description":
            ticket.description,

        "attachment_filename":
            ticket.attachment_filename,

        "category":
            ticket.category,

        "priority":
            ticket.priority,

        "ai_category":
            ticket.ai_category,

        "ai_priority":
            ticket.ai_priority,

        "ai_draft":
            ticket.ai_draft,

        "final_reply":
            ticket.final_reply,

        "citations":
            ticket.citations.split(",")
            if ticket.citations
            else [],

        "status":
            ticket.status,

        "created_at":
            ticket.created_at,

        "resolved_at":
            ticket.resolved_at,
    }