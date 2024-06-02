from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .models import Base, Code
import subprocess
import sys
import os
import re
import psutil
import threading
import time

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

    @validator('content')
    def validate_content(cls, value):
        dangerous_patterns = [
            r'while\s+True',                    # Infinite loop
            r'for\s+\w+\s+in\s+range\(.+\)',    # Large range loops
            r'def\s+\w+\(\):\s*\w+\(\)',        # Recursive functions
            r'eval\(',                          # Use of eval
            r'exec\(',                          # Use of exec
            r'import\s+os',                     # Import os module
            r'import\s+sys',                    # Import sys module
            r'import\s+subprocess',             # Import subprocess module
            r'import\s+shutil',                 # Import shutil module
        ]
        if any(re.search(pattern, value) for pattern in dangerous_patterns):
            raise ValueError("code contains dangerous patterns and cannot be executed.")
        return value

class CodeResponse(BaseModel):
    id: int
    content: str
    output: str

def execute_python_code(code: str, memory_limit: int):
    def memory_watcher(proc):
        while proc.is_running():
            mem_usage = proc.memory_info().rss / (1024 * 1024)  # Convert bytes to MB
            if mem_usage > memory_limit:
                proc.terminate()
                raise MemoryError(f"Process exceeded memory limit of {memory_limit} MB")
            time.sleep(0.1)
    
    try:
        # Prepend necessary imports to the user code
        complete_code = f"""
import numpy as np
import pandas as pd
import scipy.stats as stats
{code}"""
        proc = psutil.Popen([sys.executable, "-c", complete_code], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        watcher = threading.Thread(target=memory_watcher, args=(proc,))
        watcher.start()
        stdout, stderr = proc.communicate()
        watcher.join()
        return stdout, stderr
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=400, detail="Execution timed out")
    except MemoryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/store/", response_model=CodeResponse)
async def store_code(code: CodeCreate):
    output, error = execute_python_code(code.content, memory_limit=512)  # Set memory limit to 512MB
    if error:
        raise HTTPException(status_code=400, detail=f"Code execution failed: {error}")
    db: Session = SessionLocal()
    db_code = Code(content=code.content, output=output)
    db.add(db_code)
    db.commit()
    db.refresh(db_code)
    return CodeResponse(id=db_code.id, content=db_code.content, output=db_code.output)

@app.post("/execute/")
async def execute_code(code: CodeCreate):
    output, error = execute_python_code(code.content, memory_limit=512)  # Set memory limit to 512MB
    return {"output": output, "error": error}
