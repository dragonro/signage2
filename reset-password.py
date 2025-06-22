#!/usr/bin/env python3
"""
Digital Signage - Admin Password Reset Utility
This utility allows you to reset the admin password for the digital signage application.
"""

import os
import sqlite3
import hashlib
import getpass
import sys

def find_database():
    """Find the database file location."""
    possible_paths = ['data/signage.db', 'signage.db']
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def reset_admin_password():
    """Reset the admin password."""
    db_path = find_database()
    if not db_path:
        print("❌ Error: Database not found. Please run the application first to create the database.")
        return False
    
    print("🔐 Digital Signage - Admin Password Reset")
    print("=" * 40)
    
    # Get current admin username or create new one
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT username FROM users')
    users = cursor.fetchall()
    
    if users:
        print("📋 Current users:")
        for i, (username,) in enumerate(users, 1):
            print(f"  {i}. {username}")
        print()
        
        choice = input("Enter the username to reset (or press Enter for 'admin'): ").strip()
        if not choice:
            username = 'admin'
        else:
            username = choice
    else:
        print("📝 No users found. Creating new admin user.")
        username = input("Enter admin username (default: admin): ").strip()
        if not username:
            username = 'admin'
    
    # Get new password
    while True:
        password = getpass.getpass("Enter new password: ")
        if len(password) < 4:
            print("❌ Password must be at least 4 characters long.")
            continue
        
        confirm_password = getpass.getpass("Confirm new password: ")
        if password != confirm_password:
            print("❌ Passwords do not match. Please try again.")
            continue
        
        break
    
    # Update password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Delete existing user with same username and create new one
    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
    cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                   (username, password_hash))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Password reset successfully for user: {username}")
    print("🌐 You can now login at: http://localhost:5000")
    return True

if __name__ == '__main__':
    try:
        reset_admin_password()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
