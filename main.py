from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./databse.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    score = Column(Integer, default=0)

Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models
from pydantic import BaseModel

class ScoreUpdate(BaseModel):
    name: str
    status: str

# Routes
@app.post("/score/")
def update_score(score_update: ScoreUpdate, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.name == score_update.name).first()

    if not player:
        player = Player(name=score_update.name, score=0)
        db.add(player)

    if score_update.status == "WIN":
        player.score += 1
    elif score_update.status == "LOSE":
        player.score -= 1
    else:
        raise HTTPException(status_code=400, detail="Invalid status. Use 'WIN' or 'LOSE'.")

    db.commit()
    db.refresh(player)
    return {"name": player.name, "score": player.score}

@app.get("/top10/")
def get_top_10_players(db: Session = Depends(get_db)):
    players = db.query(Player).order_by(Player.score.desc()).limit(10).all()
    return players

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
