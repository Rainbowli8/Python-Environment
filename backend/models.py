from sqlalchemy import Column, Integer, Text
from .database import Base

class Code(Base):
    __tablename__ = "codes"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    output = Column(Text, nullable=True)
