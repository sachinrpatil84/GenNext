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
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (
                euda_info.get('filename'),
                euda_info.get('file_path'),
                euda_info.get('complexity_score'),
                euda_info.get('has_macros'),
                euda_info.get('has_formulas'),
                euda_info.get('has_external_connections'),
                analysis.get('data_sensitivity') if analysis else 'Unknown',
                analysis.get('description') if analysis else None,
                analysis.get('purpose') if analysis else None
            ))
            
            # Get the EUDA ID
            euda_id = cursor.fetchone()[0]
            
            # Generate and store embedding for the EUDA
            embedding = self.embedder.generate_euda_embedding(euda_info)
            if embedding:
                cursor.execute("""
                    INSERT INTO embeddings (
                        euda_id, content_type, content_id, embedding
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    euda_id,
                    'euda',
                    euda_id,
                    embedding
                ))
            
            # Store macros if available
            if 'macros' in euda_info and euda_info['macros']:
                self._store_macros(cursor, euda_id, euda_info['macros'])
            
            # Store formulas if available
            if 'formulas' in euda_info and euda_info['formulas']:
                self._store_formulas(cursor, euda_id, euda_info['formulas'])
            
            self.conn.commit()
            cursor.close()
            
            return euda_id
        except Exception as e:
            print(f"Error storing EUDA: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return None
    
    def _store_macros(self, cursor, euda_id, macros):
        """Store macro information and generate embeddings"""
        for macro in macros:
            try:
                # Insert macro information
                cursor.execute("""
                    INSERT INTO macros (
                        euda_id, macro_name, macro_code, purpose, complexity_score
                    ) VALUES (%s, %s, %s, %s, %s) RETURNING id
                """, (
                    euda_id,
                    macro.get('name'),
                    macro.get('code'),
                    macro.get('purpose'),
                    macro.get('complexity', 0)
                ))
                
                # Get the macro ID
                macro_id = cursor.fetchone()[0]
                
                # Generate and store embedding for the macro
                embedding = self.embedder.generate_macro_embedding(macro)
                if embedding:
                    cursor.execute("""
                        INSERT INTO embeddings (
                            euda_id, content_type, content_id, embedding
                        ) VALUES (%s, %s, %s, %s)
                    """, (
                        euda_id,
                        'macro',
                        macro_id,
                        embedding
                    ))
            except Exception as e:
                print(f"Error storing macro: {str(e)}")
                # Continue with other macros even if one fails
    
    def _store_formulas(self, cursor, euda_id, formulas):
        """Store formula information and generate embeddings"""
        for formula in formulas:
            try:
                # Insert formula information
                cursor.execute("""
                    INSERT INTO formulas (
                        euda_id, worksheet, cell_reference, formula, purpose
                    ) VALUES (%s, %s, %s, %s, %s) RETURNING id
                """, (
                    euda_id,
                    formula.get('sheet'),
                    formula.get('cell'),
                    formula.get('formula'),
                    formula.get('purpose', 'Unknown')
                ))
                
                # Get the formula ID
                formula_id = cursor.fetchone()[0]
                
                # Generate and store embedding for the formula
                embedding = self.embedder.generate_formula_embedding(formula)
                if embedding:
                    cursor.execute("""
                        INSERT INTO embeddings (
                            euda_id, content_type, content_id, embedding
                        ) VALUES (%s, %s, %s, %s)
                    """, (
                        euda_id,
                        'formula',
                        formula_id,
                        embedding
                    ))
            except Exception as e:
                print(f"Error storing formula: {str(e)}")
                # Continue with other formulas even if one fails
    
    def search_similar_eudas(self, query, limit=5):
        """Search for similar EUDAs using vector similarity"""
        try:
            # Generate embedding for the query
            query_embedding = self.embedder.embed_text(query)
            if not query_embedding:
                return []
            
            cursor = self.conn.cursor()
            
            # Search for similar EUDAs using vector similarity
            cursor.execute("""
                SELECT e.id, e.filename, e.complexity_score, e.description, e.purpose,
                       1 - (emb.embedding <=> %s) as similarity
                FROM eudas e
                JOIN embeddings emb ON e.id = emb.euda_id
                WHERE emb.content_type = 'euda'
                ORDER BY similarity DESC
                LIMIT %s
            """, (query_embedding, limit))
            
            results = cursor.fetchall()
            cursor.close()
            
            # Format the results
            return [{
                'id': row[0],
                'filename': row[1],
                'complexity_score': row[2],
                'description': row[3],
                'purpose': row[4],
                'similarity': row[5]
            } for row in results]
        except Exception as e:
            print(f"Error searching similar EUDAs: {str(e)}")
            return []
    
    def close(self):
        """Close the database connection"""
        self.db.close()