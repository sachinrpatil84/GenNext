# core/database.py
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Database:
    def __init__(self):
        self.conn = None
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "postgres")
        self.dbname = os.getenv("DB_NAME", "euda_remediation")
        
    def connect(self):
        """Connect to the PostgreSQL database"""
        try:
            # Connect to PostgreSQL server
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.dbname
            )
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print("Connected to the database successfully")
            return self.conn
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error connecting to the database: {error}")
            # Try to create the database if it doesn't exist
            if "database does not exist" in str(error):
                self._create_database()
                return self.connect()
            return None
        
    def _create_database(self):
        """Create the database if it doesn't exist"""
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {self.dbname}")
            cursor.close()
            conn.close()
            print(f"Database {self.dbname} created successfully")
            
            # Now connect to the newly created database and create extensions
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.dbname
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cursor.close()
            conn.close()
            print("Vector extension created successfully")
            
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error creating database: {error}")
    
    def create_tables(self):
        """Create necessary tables for the application"""
        try:
            cursor = self.conn.cursor()
            
            # Create table to store EUDA information
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS eudas (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    file_path TEXT NOT NULL,
                    complexity_score FLOAT,
                    has_macros BOOLEAN,
                    has_formulas BOOLEAN,
                    has_external_connections BOOLEAN,
                    data_sensitivity VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    purpose TEXT
                )
            """)
            
            # Create table for storing macros
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS macros (
                    id SERIAL PRIMARY KEY,
                    euda_id INTEGER REFERENCES eudas(id),
                    macro_name VARCHAR(255),
                    macro_code TEXT,
                    purpose TEXT,
                    complexity_score FLOAT
                )
            """)
            
            # Create table for storing formulas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS formulas (
                    id SERIAL PRIMARY KEY,
                    euda_id INTEGER REFERENCES eudas(id),
                    worksheet VARCHAR(255),
                    cell_reference VARCHAR(20),
                    formula TEXT,
                    purpose TEXT
                )
            """)
            
            # Create table for storing vector embeddings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id SERIAL PRIMARY KEY,
                    euda_id INTEGER REFERENCES eudas(id),
                    content_type VARCHAR(50),
                    content_id INTEGER,
                    embedding VECTOR(1536)
                )
            """)
            
            self.conn.commit()
            cursor.close()
            print("Tables created successfully")
            return True
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error creating tables: {error}")
            return False
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            print("Database connection closed")