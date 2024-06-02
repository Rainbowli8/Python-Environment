from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base, Code
import subprocess

app = FastAPI()

# Allow CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

class CodeCreate(BaseModel):
    content: str
    output: str = None

class CodeResponse(BaseModel):
    id: int
    content: str
    output: str

@app.post("/store/", response_model=CodeResponse)
async def store_code(code: CodeCreate):
    db: Session = SessionLocal()
    db_code = Code(content=code.content, output=code.output)
    db.add(db_code)
    db.commit()
    db.refresh(db_code)
    return CodeResponse(id=db_code.id, content=db_code.content, output=db_code.output)

@app.post("/execute/")
async def execute_code(code: CodeCreate):
    try:
        # Prepend necessary imports to the user code
        complete_code = f"""
#import numpy as np
#import pandas as pd
#import scipy.stats as stats
{code.content}"""
        # Execute the complete code
        result = subprocess.run(
            ["python", "-c", complete_code],
            capture_output=True,
            text=True,
            timeout=10
        )
        return {"output": result.stdout, "error": result.stderr}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=400, detail="Execution timed out")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
