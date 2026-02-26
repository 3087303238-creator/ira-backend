#!/usr/bin/env python3
"""
IRA System Backend - Cloud Deployment Version
For Railway/Render/Heroku deployment
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, func, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os

# ==================== 配置 ====================
SECRET_KEY = os.environ.get("SECRET_KEY", "ira-system-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 使用环境变量或SQLite
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./ira_system.db")

# ==================== 数据库设置 ====================
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== 数据模型 ====================
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String, default="recruiter")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    phone = Column(String)
    position = Column(String)
    education = Column(String)
    experience = Column(String)
    status = Column(String, default="待初筛")
    score = Column(Integer, default=0)
    match_skills = Column(JSON)
    resume_content = Column(Text)
    ai_summary = Column(Text)
    source = Column(String)
    applied_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    department = Column(String)
    description = Column(Text)
    requirements = Column(Text)
    salary = Column(String)
    headcount = Column(Integer, default=1)
    status = Column(String, default="招聘中")
    created_at = Column(DateTime, default=datetime.utcnow)

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    candidate_name = Column(String)
    position = Column(String)
    interviewer = Column(String)
    interview_time = Column(DateTime)
    duration = Column(Integer, default=60)
    interview_type = Column(String)
    status = Column(String, default="待确认")
    meeting_link = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    role = Column(String)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    target = Column(String)
    status = Column(String, default="completed")
    timestamp = Column(DateTime, default=datetime.utcnow)

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String)
    question = Column(Text)
    answer = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==================== Pydantic模型 ====================
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class CandidateCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    position: str
    education: str
    experience: str
    source: str = "手动添加"

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    status: Optional[str] = None
    score: Optional[int] = None
    match_skills: Optional[List[str]] = None
    ai_summary: Optional[str] = None

class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    position: str
    education: str
    experience: str
    status: str
    score: int
    match_skills: List[str]
    ai_summary: Optional[str]
    source: str
    applied_date: datetime

    class Config:
        from_attributes = True

class JobResponse(BaseModel):
    id: int
    title: str
    department: str
    description: str
    requirements: str
    salary: str
    headcount: int
    status: str

    class Config:
        from_attributes = True

class InterviewCreate(BaseModel):
    candidate_id: int
    candidate_name: str
    position: str
    interviewer: str
    interview_time: datetime
    interview_type: str
    meeting_link: str = ""

class InterviewUpdate(BaseModel):
    interviewer: Optional[str] = None
    interview_time: Optional[datetime] = None
    interview_type: Optional[str] = None
    status: Optional[str] = None
    meeting_link: Optional[str] = None

class InterviewResponse(BaseModel):
    id: int
    candidate_id: int
    candidate_name: str
    position: str
    interviewer: str
    interview_time: datetime
    interview_type: str
    status: str
    meeting_link: str

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    candidate_id: int
    role: str
    content: str

class ChatMessageResponse(BaseModel):
    id: int
    candidate_id: int
    role: str
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True

class ActivityLogResponse(BaseModel):
    id: int
    action: str
    target: str
    status: str
    timestamp: datetime

    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    pending_resumes: int
    pending_interviews: int
    today_interviews: int
    ai_saved_hours: int
    week_growth: float
    conversion_rate: float

class FunnelStage(BaseModel):
    stage: str
    count: int
    rate: float

class KnowledgeBaseCreate(BaseModel):
    category: str
    question: str
    answer: str

class KnowledgeBaseResponse(BaseModel):
    id: int
    category: str
    question: str
    answer: str

    class Config:
        from_attributes = True

# ==================== 依赖 ====================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# ==================== 初始化数据库 ====================
def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin_user = User(
                email="admin@ira-system.com",
                username="admin",
                full_name="系统管理员",
                hashed_password=get_password_hash("admin123"),
                role="admin"
            )
            db.add(admin_user)

            initial_candidates = [
                Candidate(name="王五", email="wangwu@email.com", phone="138****8888",
                         position="高级前端工程师", education="硕士", experience="5年",
                         score=92, status="待初试", match_skills=["React", "TypeScript", "Vue", "Node.js"],
                         source="BOSS直聘"),
                Candidate(name="李明", email="liming@email.com", phone="139****9999",
                         position="全栈工程师", education="本科", experience="4年",
                         score=88, status="待沟通", match_skills=["Python", "Django", "React", "PostgreSQL"],
                         source="拉勾网"),
                Candidate(name="张伟", email="zhangwei@email.com", phone="137****7777",
                         position="Python开发工程师", education="本科", experience="3年",
                         score=85, status="已推荐", match_skills=["Python", "FastAPI", "MongoDB", "Docker"],
                         source="猎聘"),
                Candidate(name="赵婷", email="zhaoting@email.com", phone="136****6666",
                         position="数据分析师", education="硕士", experience="2年",
                         score=90, status="待复试", match_skills=["Python", "SQL", "Tableau", "Machine Learning"],
                         source="内推"),
                Candidate(name="陈军", email="chenjun@email.com", phone="135****5555",
                         position="DevOps工程师", education="本科", experience="6年",
                         score=87, status="待初筛", match_skills=["Kubernetes", "Docker", "Jenkins", "AWS"],
                         source="BOSS直聘"),
                Candidate(name="刘芳", email="liufang@email.com", phone="134****4444",
                         position="产品经理", education="本科", experience="5年",
                         score=83, status="待沟通", match_skills=["产品设计", "数据分析", "Axure", "用户研究"],
                         source="官网"),
            ]
            db.add_all(initial_candidates)

            initial_jobs = [
                Job(title="高级前端工程师", department="技术部", description="负责前端架构设计和开发",
                    requirements="5年以上前端开发经验，精通React/Vue", salary="25K-40K", headcount=2),
                Job(title="全栈工程师", department="技术部", description="负责全栈开发",
                    requirements="3年以上开发经验，熟悉Python和React", salary="20K-35K", headcount=3),
                Job(title="Python开发工程师", department="技术部", description="负责后端服务开发",
                    requirements="2年以上Python开发经验", salary="18K-30K", headcount=2),
                Job(title="数据分析师", department="数据部", description="负责数据分析工作",
                    requirements="统计学或计算机相关专业", salary="15K-25K", headcount=1),
                Job(title="DevOps工程师", department="技术部", description="负责运维和自动化",
                    requirements="3年以上DevOps经验", salary="22K-35K", headcount=1),
                Job(title="产品经理", department="产品部", description="负责产品规划",
                    requirements="3年以上产品经验", salary="20K-30K", headcount=1),
            ]
            db.add_all(initial_jobs)

            today = datetime.now()
            initial_interviews = [
                Interview(candidate_id=1, candidate_name="王五", position="高级前端工程师",
                         interviewer="张经理", interview_time=datetime(today.year, today.month, today.day, 14, 0),
                         interview_type="技术面试", status="已确认", meeting_link="https://meet.example.com/abc123"),
                Interview(candidate_id=4, candidate_name="赵婷", position="数据分析师",
                         interviewer="李总监", interview_time=datetime(today.year, today.month, today.day, 10, 0),
                         interview_type="综合面试", status="已确认", meeting_link="https://meet.example.com/def456"),
                Interview(candidate_id=2, candidate_name="李明", position="全栈工程师",
                         interviewer="王技术", interview_time=datetime(today.year, today.month, today.day + 1, 15, 0),
                         interview_type="技术面试", status="待确认"),
            ]
            db.add_all(initial_interviews)

            initial_logs = [
                ActivityLog(action="筛选简历", target="王五 - 高级前端工程师", status="completed"),
                ActivityLog(action="发送面试邀请", target="李明 - 全栈工程师", status="completed"),
                ActivityLog(action="解答候选人问题", target="张伟 - Python开发工程师", status="completed"),
                ActivityLog(action="生成JD优化建议", target="后端工程师岗位", status="completed"),
                ActivityLog(action="安排面试时间", target="赵婷 - 数据分析师", status="completed"),
            ]
            db.add_all(initial_logs)

            initial_kb = [
                KnowledgeBase(category="福利", question="公司有什么福利？",
                            answer="公司提供以下福利：\n1. 六险一金\n2. 年度体检\n3. 带薪年假15天\n4. 餐补+交通补贴\n5. 节假日礼品\n6. 扁平化管理\n7. 技术氛围浓厚\n8. 弹性工作制"),
                KnowledgeBase(category="薪资", question="薪资结构是怎样的？",
                            answer="薪资结构为：基本工资 + 绩效奖金 + 年终奖。具体面议，会根据候选人的经验和能力定级。"),
                KnowledgeBase(category="技术", question="技术栈是什么？",
                            answer="后端使用Python(Django/FastAPI)，前端使用React，数据库使用PostgreSQL，注重DevOps能力。"),
            ]
            db.add_all(initial_kb)

            db.commit()
            print("数据库初始化完成！默认账号: admin / admin123")
    finally:
        db.close()

# ==================== API端点 ====================
app = FastAPI(title="IRA System API", description="智能招聘Agent系统后端API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 认证
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# 工作台统计
@app.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    pending_resumes = db.query(Candidate).filter(Candidate.status.in_(["待初筛", "待沟通"])).count()
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    today_interviews = db.query(Interview).filter(
        Interview.interview_time >= today_start,
        Interview.interview_time <= today_end
    ).count()
    pending_interviews = db.query(Interview).filter(Interview.status == "待确认").count()
    ai_saved_hours = db.query(Candidate).count() * 2 + 120

    total = db.query(Candidate).count()
    converted = db.query(Candidate).filter(Candidate.status.in_(["待初试", "待复试", "已推荐"])).count()
    conversion_rate = round(converted / total * 100, 1) if total > 0 else 0

    return DashboardStats(
        pending_resumes=pending_resumes,
        pending_interviews=pending_interviews,
        today_interviews=today_interviews,
        ai_saved_hours=ai_saved_hours,
        week_growth=12.5,
        conversion_rate=conversion_rate
    )

@app.get("/dashboard/funnel", response_model=List[FunnelStage])
async def get_funnel_data(db: Session = Depends(get_db)):
    total = db.query(Candidate).count() or 1
    stages = [
        ("简历投递", db.query(Candidate).count()),
        ("AI初筛", db.query(Candidate).filter(Candidate.score >= 70).count()),
        ("HR筛选", db.query(Candidate).filter(Candidate.status.in_(["待初试", "待复试", "已推荐"])).count()),
        ("初试", db.query(Candidate).filter(Candidate.status.in_(["待初试", "待复试"])).count()),
        ("复试", db.query(Candidate).filter(Candidate.status == "待复试").count()),
        ("Offer", db.query(Candidate).filter(Candidate.status == "已推荐").count()),
    ]
    return [
        FunnelStage(stage=name, count=count, rate=round(count / total * 100, 1))
        for name, count in stages
    ]

@app.get("/dashboard/activity", response_model=List[ActivityLogResponse])
async def get_activity_logs(limit: int = 10, db: Session = Depends(get_db)):
    logs = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
    return logs

# 候选人列表
@app.get("/candidates", response_model=List[CandidateResponse])
async def get_candidates(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Candidate)
    if status:
        query = query.filter(Candidate.status == status)
    if search:
        query = query.filter(Candidate.name.contains(search) | Candidate.position.contains(search))
    return query.offset(skip).limit(limit).all()

@app.get("/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="候选人未找到")
    return candidate

@app.post("/candidates", response_model=CandidateResponse)
async def create_candidate(candidate: CandidateCreate, db: Session = Depends(get_db)):
    db_candidate = Candidate(**candidate.dict())
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    log = ActivityLog(action="新增候选人", target=f"{candidate.name} - {candidate.position}")
    db.add(log)
    db.commit()
    return db_candidate

@app.patch("/candidates/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(candidate_id: int, candidate: CandidateUpdate, db: Session = Depends(get_db)):
    db_candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not db_candidate:
        raise HTTPException(status_code=404, detail="候选人未找到")
    update_data = candidate.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_candidate, key, value)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

@app.delete("/candidates/{candidate_id}")
async def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="候选人未找到")
    db.delete(candidate)
    db.commit()
    return {"message": "候选人已删除"}

# 职位管理
@app.get("/jobs", response_model=List[JobResponse])
async def get_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()

@app.post("/jobs", response_model=JobResponse)
async def create_job(job: dict, db: Session = Depends(get_db)):
    db_job = Job(**job)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

# 面试安排
@app.get("/interviews", response_model=List[InterviewResponse])
async def get_interviews(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Interview)
    if start_date:
        query = query.filter(Interview.interview_time >= start_date)
    if end_date:
        query = query.filter(Interview.interview_time <= end_date)
    return query.order_by(Interview.interview_time).all()

@app.post("/interviews", response_model=InterviewResponse)
async def create_interview(interview: InterviewCreate, db: Session = Depends(get_db)):
    db_interview = Interview(**interview.dict())
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    candidate = db.query(Candidate).filter(Candidate.id == interview.candidate_id).first()
    if candidate:
        candidate.status = "待初试"
        db.commit()
    log = ActivityLog(action="安排面试", target=f"{interview.candidate_name} - {interview.position}")
    db.add(log)
    db.commit()
    return db_interview

@app.patch("/interviews/{interview_id}", response_model=InterviewResponse)
async def update_interview(interview_id: int, interview: InterviewUpdate, db: Session = Depends(get_db)):
    db_interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not db_interview:
        raise HTTPException(status_code=404, detail="面试未找到")
    update_data = interview.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_interview, key, value)
    db.commit()
    db.refresh(db_interview)
    return db_interview

# 聊天记录
@app.get("/chat/{candidate_id}", response_model=List[ChatMessageResponse])
async def get_chat_history(candidate_id: int, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(
        ChatMessage.candidate_id == candidate_id
    ).order_by(ChatMessage.timestamp).all()
    return messages

@app.post("/chat", response_model=ChatMessageResponse)
async def send_message(message: ChatMessageCreate, db: Session = Depends(get_db)):
    db_message = ChatMessage(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

# 知识库
@app.get("/knowledge-base", response_model=List[KnowledgeBaseResponse])
async def get_knowledge_base(category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(KnowledgeBase)
    if category:
        query = query.filter(KnowledgeBase.category == category)
    return query.all()

@app.post("/knowledge-base", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(item: KnowledgeBaseCreate, db: Session = Depends(get_db)):
    db_item = KnowledgeBase(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# AI回复建议
@app.post("/chat/ai-reply")
async def get_ai_reply(candidate_id: int, user_message: str, db: Session = Depends(get_db)):
    kb_items = db.query(KnowledgeBase).all()
    relevant_answers = []
    for kb in kb_items:
        if any(keyword in user_message for keyword in kb.question.split()):
            relevant_answers.append(kb.answer)
    if relevant_answers:
        ai_reply = relevant_answers[0]
    else:
        ai_reply = "感谢您的咨询。如果您有更多问题，欢迎随时向我提问。"
    db_message = ChatMessage(candidate_id=candidate_id, role="ai", content=ai_reply)
    db.add(db_message)
    db.commit()
    return {"reply": ai_reply}

# 渠道分析数据
@app.get("/analytics/channels")
async def get_channel_data(db: Session = Depends(get_db)):
    sources = db.query(Candidate.source, func.count(Candidate.id)).group_by(Candidate.source).all()
    channel_data = []
    for source, count in sources:
        channel_data.append({
            "channel": source,
            "resumes": count,
            "hired": int(count * 0.1),
            "cost": count * 100,
            "roi": round(count * 0.1 * 10 / (count * 100) * 100, 1) if count > 0 else 0
        })
    return channel_data

# AI效能数据
@app.get("/analytics/ai-performance")
async def get_ai_performance(db: Session = Depends(get_db)):
    candidate_count = db.query(Candidate).count()
    return [
        {"month": "10月", "screening": 120, "communication": 80, "scheduling": 45, "savedHours": 120},
        {"month": "11月", "screening": 180, "communication": 120, "scheduling": 65, "savedHours": 180},
        {"month": "12月", "screening": 250, "communication": 160, "scheduling": 85, "savedHours": 245},
        {"month": "1月", "screening": candidate_count + 50, "communication": candidate_count + 30,
         "scheduling": candidate_count + 10, "savedHours": candidate_count * 2}
    ]

# ==================== 启动 ====================
@app.on_event("startup")
async def startup_event():
    init_db()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
