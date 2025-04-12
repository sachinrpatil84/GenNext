# embedding/vector_store.py
import psycopg2
from psycopg2.extras import execute_values
from core.database import Database
from embedding.vector_embedder import TitanEmbedder
import json

class VectorStore:
    def __init__(self):
        """Initialize the vector store with database connection"""
        self.db = Database()
        self.conn = self.db.connect()
        self.embedder = TitanEmbedder()
    
    def store_euda(self, euda_info, analysis=None):
        """Store EUDA information and generate embeddings"""
        try:
            cursor = self.conn.cursor()
            
            # Insert EUDA information
            cursor.execute("""
                INSERT INTO eudas (
                    filename, file_path, complexity_score, has_macros, 
                    has_formulas, has_external_connections, data_sensitivity,
                    description, purpose
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s