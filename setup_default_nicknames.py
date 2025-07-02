#!/usr/bin/env python3
"""
Script to add default nicknames to the database for testing.
Run this once to populate the database with some starter nicknames.
"""

from models import DatabaseManager

def setup_default_nicknames():
    """Add some default nicknames to the database."""
    
    # Default nicknames to add (based on the original static ones)
    default_nicknames = [
        "Subject",
        "Operator", 
        "Agent",
        "Specimen",
        "Entity",
        "Unit",
        "Asset",
        "Contact",
        "Target",
        "Source"
    ]
    
    try:
        db = DatabaseManager()
        print("Connected to database successfully!")
        
        # You'll need to replace this with your actual guild ID
        # This is just an example - the bot will register guilds automatically
        print("Default nicknames ready to be added via Discord commands:")
        print("Use these commands in your Discord server:")
        print()
        
        for nickname in default_nicknames:
            print(f"!add_nickname {nickname}")
        
        print()
        print("After adding nicknames, test the bot by:")
        print("1. Join a voice channel")
        print("2. Your nickname should change to something like 'Subject 001'")
        print("3. Leave the voice channel to restore your original nickname")
        print()
        print("Use !list_nicknames to see all available nicknames")
        print("Use !remove_nickname <name> to remove a nickname (server owner only)")
        
    except Exception as e:
        print(f"Error setting up database: {e}")

if __name__ == "__main__":
    setup_default_nicknames()