from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, exc
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy.orm import sessionmaker

# Base model class
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(64), unique=True)
    password = Column(String(64))
    created_at = Column(DateTime, default=datetime.now)

    def __str__(self):
        return self.username

class File(Base):
    __tablename__ = 'files'
    id = Column(Integer, primary_key=True)
    path = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.now)

    def __str__(self):
        return self.path

class Job(Base):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    def __str__(self):
        return self.path

class DatabaseManager:
    def __init__(self, db_url='sqlite:///project.db'):
        self.engine = create_engine(db_url, echo=True)  # Set echo=False in production
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def open_db(self):
        return self.Session()

    def add_to_db(self, obj):
        session = self.open_db()
        try:
            session.add(obj)
            session.commit()
        except exc.SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()


            
if __name__ == "__main__":
    # Initialize the DatabaseManager
    db_manager = DatabaseManager()

    # Example usage: adding a job to the database
    job_title = 'Software Engineer'
    job_description = 'Developing web applications'
    db_manager.add_to_db(Job(title=job_title, description=job_description))

