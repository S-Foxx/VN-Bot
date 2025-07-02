"""
Database models for Discord Voice Nickname Bot.
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, BigInteger, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from typing import List, Optional

Base = declarative_base()

class Guild(Base):
    """
    Represents a Discord server (guild) that has added the bot.
    Each guild gets unique nickname management.
    """
    __tablename__ = 'guilds'
    
    id = Column(BigInteger, primary_key=True)  # Discord Guild ID
    name = Column(String(100), nullable=False)  # Guild name for reference
    owner_id = Column(BigInteger, nullable=False)  # Discord Guild Owner ID
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationship to nicknames
    nicknames = relationship("Nickname", back_populates="guild", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Guild(id={self.id}, name='{self.name}')>"

class Nickname(Base):
    """
    Represents a nickname template that can be used in a specific guild.
    Format will be: "{nickname} {3-digit-counter}"
    """
    __tablename__ = 'nicknames'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, ForeignKey('guilds.id'), nullable=False)
    nickname = Column(String(50), nullable=False)  # The base nickname (e.g., "Subject", "Operator")
    is_active = Column(Boolean, default=True)  # Allow soft deletion
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(BigInteger, nullable=False)  # Discord User ID who added it
    
    # Relationship to guild
    guild = relationship("Guild", back_populates="nicknames")
    
    def __repr__(self):
        return f"<Nickname(id={self.id}, guild_id={self.guild_id}, nickname='{self.nickname}')>"

class DatabaseManager:
    """
    Manages database connections and operations for the nickname bot.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        if not database_url:
            database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    def ensure_guild_exists(self, guild_id: int, guild_name: str, owner_id: int) -> Guild:
        """
        Ensure a guild exists in the database, create if it doesn't.
        
        Args:
            guild_id: Discord guild ID
            guild_name: Discord guild name
            owner_id: Discord guild owner ID
            
        Returns:
            Guild object
        """
        session = self.get_session()
        try:
            guild = session.query(Guild).filter(Guild.id == guild_id).first()
            if not guild:
                guild = Guild(id=guild_id, name=guild_name, owner_id=owner_id)
                session.add(guild)
                session.commit()
                session.refresh(guild)
            else:
                # Update guild info if it changed
                if guild.name != guild_name or guild.owner_id != owner_id:
                    guild.name = guild_name
                    guild.owner_id = owner_id
                    session.commit()
            return guild
        finally:
            session.close()
    
    def add_nickname(self, guild_id: int, nickname: str, created_by: int) -> Optional[Nickname]:
        """
        Add a new nickname to a guild.
        
        Args:
            guild_id: Discord guild ID
            nickname: The nickname to add (will be cleaned)
            created_by: Discord user ID who added it
            
        Returns:
            Nickname object if successful, None if duplicate
        """
        # Clean the nickname
        cleaned_nickname = nickname.strip()
        if not cleaned_nickname:
            return None
        
        session = self.get_session()
        try:
            # Check if nickname already exists for this guild
            existing = session.query(Nickname).filter(
                Nickname.guild_id == guild_id,
                Nickname.nickname.ilike(cleaned_nickname),
                Nickname.is_active == True
            ).first()
            
            if existing:
                return None  # Duplicate
            
            new_nickname = Nickname(
                guild_id=guild_id,
                nickname=cleaned_nickname,
                created_by=created_by
            )
            session.add(new_nickname)
            session.commit()
            session.refresh(new_nickname)
            return new_nickname
        finally:
            session.close()
    
    def remove_nickname(self, guild_id: int, nickname: str, requester_id: int) -> tuple[bool, str]:
        """
        Remove (soft delete) a nickname from a guild.
        
        Args:
            guild_id: Discord guild ID
            nickname: The nickname to remove
            requester_id: Discord user ID making the request
            
        Returns:
            (success: bool, message: str)
        """
        cleaned_nickname = nickname.strip()
        session = self.get_session()
        try:
            # Check if requester is guild owner
            guild = session.query(Guild).filter(Guild.id == guild_id).first()
            if not guild:
                return False, "Guild not found"
            
            if guild.owner_id != requester_id:
                return False, "Only the server owner can remove nicknames"
            
            # Find the nickname
            nickname_obj = session.query(Nickname).filter(
                Nickname.guild_id == guild_id,
                Nickname.nickname.ilike(cleaned_nickname),
                Nickname.is_active == True
            ).first()
            
            if not nickname_obj:
                return False, f"Nickname '{cleaned_nickname}' not found"
            
            # Soft delete
            nickname_obj.is_active = False
            session.commit()
            return True, f"Nickname '{cleaned_nickname}' removed successfully"
        finally:
            session.close()
    
    def get_guild_nicknames(self, guild_id: int) -> List[Nickname]:
        """
        Get all active nicknames for a guild.
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            List of active Nickname objects
        """
        session = self.get_session()
        try:
            nicknames = session.query(Nickname).filter(
                Nickname.guild_id == guild_id,
                Nickname.is_active == True
            ).order_by(Nickname.nickname).all()
            return nicknames
        finally:
            session.close()
    
    def get_random_nickname(self, guild_id: int) -> Optional[str]:
        """
        Get a random active nickname for a guild.
        
        Args:
            guild_id: Discord guild ID
            
        Returns:
            Random nickname string or None if no nicknames available
        """
        session = self.get_session()
        try:
            # Use SQL random function for better performance
            nickname = session.query(Nickname).filter(
                Nickname.guild_id == guild_id,
                Nickname.is_active == True
            ).order_by(func.random()).first()
            
            return nickname.nickname if nickname else None
        finally:
            session.close()