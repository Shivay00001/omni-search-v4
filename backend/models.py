from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String) # user or assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    conversation = relationship("Conversation", back_populates="messages")

class ResearchStep(Base):
    __tablename__ = "research_steps"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    query = Column(String)
    results_json = Column(Text) # JSON string of results
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class RL_Feedback(Base):
    """Reinforcement Learning Feedback Store"""
    __tablename__ = "rl_feedback"
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String)
    url = Column(String)
    domain = Column(String)
    score = Column(Float, default=0.0) # Positive for like, negative for dislike
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
