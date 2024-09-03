from sqlmodel import Session
from models import engine, User
from auth import get_password_hash

def create_user(username: str, password: str):
    with Session(engine) as session:
        hashed_password = get_password_hash(password)
        user = User(username=username, hashed_password=hashed_password)
        session.add(user)
        session.commit()
        print(f"User {username} created successfully.")

if __name__ == "__main__":
    username = input("Enter username: ")
    password = input("Enter password: ")
    create_user(username, password)