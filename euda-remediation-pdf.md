# Excel EUDA to Python Remediation Application

## Table of Contents
1. [Environment Setup](#step-1-setup-the-environment-and-install-required-libraries)
2. [AWS Bedrock Integration](#step-2-connect-to-aws-bedrock-for-embeddings-and-llm-access)
3. [PostgreSQL Vector Database Setup](#step-3-connect-to-postgresql-vector-database)
4. [EUDA Analyzer Class](#step-4-excel-euda-analyzer-class)
5. [EUDA Chatbot](#step-5-create-the-euda-chatbot)
6. [Command Line Interface](#step-6-create-a-command-line-interface)
7. [Web Interface](#step-7-create-a-web-interface-optional)

## Step 1: Setup the Environment and Install Required Libraries

First, we need to set up our Python environment with all necessary libraries:

```python
# Install required packages
# pip install python-dotenv pandas openpyxl xlwings psycopg2-binary langchain openai tiktoken pillow boto3

import os
import pandas as pd
import xlwings as xw
import re
import json
import boto3
from dotenv import load_dotenv
import psycopg2
from langchain.vectorstores import PGVector
from langchain.embeddings import BedrockEmbeddings
from langchain.chat_models import BedrockChat
from langchain.callbacks import get_openai_callback
from langchain.schema import Document
import uuid
```

## Step 2: Connect to AWS Bedrock for Embeddings and LLM Access

Let's set up connections to AWS Bedrock for both embeddings and to communicate with Claude:

```python
load_dotenv()  # Load environment variables

# AWS Bedrock setup
bedrock_client = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

# Setup Amazon Titan for embeddings
titan_embeddings = BedrockEmbeddings(
    client=bedrock_client,
    model_id="amazon.titan-embed-text-v1"  # Using Titan text embeddings
)

# Setup Claude for analysis
claude_model = BedrockChat(
    client=bedrock_client,
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    model_kwargs={
        "temperature": 0.7,
        "max_tokens": 4000
    }
)
```

## Step 3: Connect to PostgreSQL Vector Database

Now we'll set up the connection to PostgreSQL, which will store our vector embeddings:

```python
# PostgreSQL connection information
CONNECTION_STRING = PGVector.connection_string_from_db_params(
    driver=os.getenv("PGVECTOR_DRIVER", "psycopg2"),
    host=os.getenv("PGVECTOR_HOST", "localhost"),
    port=os.getenv("PGVECTOR_PORT", "5432"),
    database=os.getenv("PGVECTOR_DATABASE", "vectordb"),
    user=os.getenv("PGVECTOR_USER", "postgres"),
    password=os.getenv("PGVECTOR_PASSWORD", "password")
)

# Create tables if they don't exist
def setup_database():
    conn = psycopg2.connect(
        host=os.getenv("PGVECTOR_HOST", "localhost"),
        port=os.getenv("PGVECTOR_PORT", "5432"),
        database=os.getenv("PGVECTOR_DATABASE", "vectordb"),
        user=os.getenv("PGVECTOR_USER", "postgres"),
        password=os.getenv("PGVECTOR_PASSWORD", "password")
    )
    
    cursor = conn.cursor()
    
    # Create extension if not exists
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # Create tables for storing EUDA analysis results
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS euda_analysis (
        id SERIAL PRIMARY KEY,
        file_name TEXT,
        analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        complexity_score FLOAT,
        sensitivity_score FLOAT,
        remediation_score FLOAT,
        macros_count INTEGER,
        formulas_count INTEGER,
        linked_data_sources TEXT[],
        summary TEXT,
        remediation_plan TEXT
    );
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

setup_database()
```

## Step 4: Excel EUDA Analyzer Class

Now, let's create a class to analyze Excel EUDAs:

```python
class EUDAAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.analysis_results = {}
        
    def extract_excel_content(self):
        """Extract content from Excel file including sheets, macros, formulas"""
        try:
            # Open Excel application in background
            app = xw.App(visible=False)
            wb = app.books.open(self.file_path)
            
            workbook_content = {
                "sheets": [],
                "vba_modules": [],
                "connections": []
            }
            
            # Extract sheet content
            for sheet in wb.sheets:
                sheet_data = {
                    "name": sheet.name,
                    "used_range": str(sheet.used_range.address),
                    "formulas": [],
                    "data_sample": []
                }
                
                # Get formulas
                if sheet.used_range:
                    for cell in sheet.used_range:
                        if cell.formula:
                            sheet_data["formulas"].append({
                                "cell": cell.address,
                                "formula": cell.formula
                            })
                
                # Get sample data (first 5 rows, max 10 columns)
                if sheet.used_range:
                    data_range = sheet.range((1, 1), (min(5, sheet.used_range.last_cell.row), 
                                                      min(10, sheet.used_range.last_cell.column)))
                    for row in data_range.rows:
                        row_data = [str(cell.value) for cell in row]
                        sheet_data["data_sample"].append(row_data)
                
                workbook_content["sheets"].append(sheet_data)
            
            # Extract VBA modules if present
            try:
                for vba_module in wb.vba_modules:
                    workbook_content["vba_modules"].append({
                        "name": vba_module.name,
                        "code": vba_module.code()
                    })
            except:
                # No VBA modules or not accessible
                pass
                
            # Extract external connections if available
            try:
                for connection in wb.connections:
                    workbook_content["connections"].append({
                        "name": connection.name,
                        "description": connection.description,
                        "connection_string": connection.connection_string
                    })
            except:
                # No connections or not accessible
                pass
            
            wb.close()
            app.quit()
            
            return workbook_content
            
        except Exception as e:
            print(f"Error extracting Excel content: {e}")
            return {"error": str(e)}
    
    def calculate_complexity_score(self, content):
        """Calculate complexity score based on formulas, macros, sheets, etc."""
        score = 0
        
        # Count formulas
        formula_count = sum(len(sheet["formulas"]) for sheet in content["sheets"])
        
        # Count macros/VBA
        macro_count = len(content["vba_modules"])
        vba_lines = sum(len(module["code"].split("\n")) for module in content["vba_modules"])
        
        # Count external connections
        connection_count = len(content["connections"])
        
        # Count sheets
        sheet_count = len(content["sheets"])
        
        # Calculate complexity metrics
        if formula_count > 500: score += 30
        elif formula_count > 100: score += 20
        elif formula_count > 10: score += 10
        
        if macro_count > 0: score += 20
        if vba_lines > 1000: score += 30
        elif vba_lines > 100: score += 20
        
        if connection_count > 0: score += 15
        
        if sheet_count > 10: score += 15
        elif sheet_count > 3: score += 5
        
        # Normalize score to 0-100
        normalized_score = min(max(score, 0), 100)
        
        self.analysis_results["complexity"] = {
            "score": normalized_score,
            "formula_count": formula_count,
            "macro_count": macro_count,
            "vba_lines": vba_lines,
            "connection_count": connection_count,
            "sheet_count": sheet_count
        }
        
        return normalized_score
    
    def assess_data_sensitivity(self, content):
        """Assess data sensitivity by looking for patterns in the data"""
        sensitivity_score = 0
        potential_sensitive_data = {
            "pii": False,
            "financial": False,
            "health": False,
            "confidential": False
        }
        
        # Keywords to check for different categories
        pii_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b(?:\d{3}[-.\s]??\d{3}[-.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-.\s]??\d{4}|\d{3}[-.\s]??\d{4})\b',  # Phone
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b'  # Credit card
        ]
        
        financial_patterns = [
            r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # Currency
            r'invoice',
            r'payment',
            r'salary',
            r'revenue'
        ]
        
        health_patterns = [
            r'patient',
            r'diagnosis',
            r'medical',
            r'health',
            r'treatment'
        ]
        
        confidential_patterns = [
            r'confidential',
            r'proprietary',
            r'secret',
            r'internal'
        ]
        
        # Check all sheet data for sensitivity patterns
        for sheet in content["sheets"]:
            sheet_text = str(sheet["data_sample"])
            
            # Check for PII
            for pattern in pii_patterns:
                if re.search(pattern, sheet_text, re.IGNORECASE):
                    potential_sensitive_data["pii"] = True
                    sensitivity_score += 25
                    break
            
            # Check for financial data
            for pattern in financial_patterns:
                if re.search(pattern, sheet_text, re.IGNORECASE):
                    potential_sensitive_data["financial"] = True
                    sensitivity_score += 20
                    break
            
            # Check for health data
            for pattern in health_patterns:
                if re.search(pattern, sheet_text, re.IGNORECASE):
                    potential_sensitive_data["health"] = True
                    sensitivity_score += 25
                    break
            
            # Check for confidential data
            for pattern in confidential_patterns:
                if re.search(pattern, sheet_text, re.IGNORECASE):
                    potential_sensitive_data["confidential"] = True
                    sensitivity_score += 15
                    break
        
        # Normalize sensitivity score to 0-100
        sensitivity_score = min(max(sensitivity_score, 0), 100)
        
        self.analysis_results["sensitivity"] = {
            "score": sensitivity_score,
            "potential_sensitive_data": potential_sensitive_data
        }
        
        return sensitivity_score
    
    def analyze_with_claude(self, content):
        """Use Claude to analyze the EUDA and extract insights"""
        # Convert content to simplified text format for Claude
        sheets_summary = []
        for sheet in content["sheets"]:
            formulas_text = "\n".join([f"{f['cell']}: {f['formula']}" for f in sheet["formulas"][:20]])
            sheet_text = f"Sheet: {sheet['name']}\nSample Data: {sheet['data_sample'][:5]}\nFormulas (sample): {formulas_text}"
            sheets_summary.append(sheet_text)
        
        macros_text = []
        for module in content["vba_modules"]:
            # Limit code length
            code_sample = module["code"][:2000] + ("..." if len(module["code"]) > 2000 else "")
            macros_text.append(f"Module: {module['name']}\nCode Sample: {code_sample}")
        
        connections_text = []
        for conn in content["connections"]:
            connections_text.append(f"Connection: {conn['name']}\nDescription: {conn['description']}")
        
        prompt = f"""
        Analyze this Excel EUDA (End User Developed Application) and provide the following information:
        
        1. Summary of the EUDA's purpose and functionality
        2. Main business processes this EUDA supports
        3. Key data transformation logic
        4. Recommendations for remediating this EUDA with a Python application
        5. Required data sources for remediation
        6. Architecture components needed for remediation
        7. Complexity assessment (1-10 scale with explanation)
        
        Excel File Information:
        {self.file_name}
        
        Sheets:
        {"".join(sheets_summary[:5])}
        
        {"Macros:" if macros_text else "No macros found."}
        {"".join(macros_text[:3])}
        
        {"External Connections:" if connections_text else "No external connections found."}
        {"".join(connections_text)}
        
        Based on this information, provide a comprehensive analysis to help remediate this EUDA with a proper Python application.
        """
        
        response = claude_model.invoke(prompt)
        
        # Extract insights from Claude's response
        analysis = response.content
        
        # Store analysis in results
        self.analysis_results["claude_analysis"] = analysis
        
        # Try to extract structured information
        try:
            # Extract remediation score based on Claude's analysis
            if "recommend" in analysis.lower() and "python" in analysis.lower():
                self.analysis_results["remediation_score"] = 80  # High if Claude recommends Python remediation
            else:
                self.analysis_results["remediation_score"] = 40  # Medium-low otherwise
                
            # Extract required data sources
            data_sources_match = re.search(r"Required data sources[:\n]+(.*?)(?:\n\n|\n\d\.)", analysis, re.DOTALL)
            if data_sources_match:
                data_sources = data_sources_match.group(1).strip()
                self.analysis_results["required_data_sources"] = data_sources
            
            # Extract architecture components
            arch_match = re.search(r"Architecture components[:\n]+(.*?)(?:\n\n|\n\d\.)", analysis, re.DOTALL)
            if arch_match:
                architecture = arch_match.group(1).strip()
                self.analysis_results["architecture"] = architecture
            
        except Exception as e:
            print(f"Error parsing Claude's analysis: {e}")
        
        return analysis
    
    def store_in_vector_db(self):
        """Store analysis in PostgreSQL vector database"""
        try:
            # Create documents for vector storage
            excel_content = json.dumps(self.analysis_results.get("excel_content", {}), default=str)
            claude_analysis = self.analysis_results.get("claude_analysis", "")
            
            documents = [
                Document(
                    page_content=f"EUDA Analysis for {self.file_name}: {claude_analysis}",
                    metadata={
                        "file_name": self.file_name,
                        "complexity_score": self.analysis_results.get("complexity", {}).get("score", 0),
                        "sensitivity_score": self.analysis_results.get("sensitivity", {}).get("score", 0),
                        "remediation_score": self.analysis_results.get("remediation_score", 0),
                        "source": "claude_analysis"
                    }
                ),
                Document(
                    page_content=f"EUDA Content for {self.file_name}: {excel_content[:1000]}",
                    metadata={
                        "file_name": self.file_name,
                        "source": "excel_content"
                    }
                )
            ]
            
            # Create vector store
            collection_name = f"euda_analysis_{uuid.uuid4().hex[:8]}"
            vector_store = PGVector.from_documents(
                documents=documents,
                embedding=titan_embeddings,
                collection_name=collection_name,
                connection_string=CONNECTION_STRING
            )
            
            self.analysis_results["vector_db_collection"] = collection_name
            
            # Also store structured data in regular table
            conn = psycopg2.connect(
                host=os.getenv("PGVECTOR_HOST", "localhost"),
                port=os.getenv("PGVECTOR_PORT", "5432"),
                database=os.getenv("PGVECTOR_DATABASE", "vectordb"),
                user=os.getenv("PGVECTOR_USER", "postgres"),
                password=os.getenv("PGVECTOR_PASSWORD", "password")
            )
            
            cursor = conn.cursor()
            
            # Insert analysis results
            cursor.execute("""
            INSERT INTO euda_analysis 
            (file_name, complexity_score, sensitivity_score, remediation_score, 
             macros_count, formulas_count, linked_data_sources, summary, remediation_plan)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.file_name,
                self.analysis_results.get("complexity", {}).get("score", 0),
                self.analysis_results.get("sensitivity", {}).get("score", 0),
                self.analysis_results.get("remediation_score", 0),
                self.analysis_results.get("complexity", {}).get("macro_count", 0),
                self.analysis_results.get("complexity", {}).get("formula_count", 0),
                [self.analysis_results.get("required_data_sources", "")],
                claude_analysis[:500],  # Summary (limited to 500 chars)
                self.analysis_results.get("architecture", "")
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return collection_name
            
        except Exception as e:
            print(f"Error storing in vector DB: {e}")
            return None
    
    def analyze(self):
        """Run full analysis on the EUDA"""
        print(f"Analyzing EUDA: {self.file_name}")
        
        # Extract content from Excel
        content = self.extract_excel_content()
        self.analysis_results["excel_content"] = content
        
        # Calculate complexity score
        complexity_score = self.calculate_complexity_score(content)
        print(f"Complexity Score: {complexity_score}")
        
        # Assess data sensitivity 
        sensitivity_score = self.assess_data_sensitivity(content)
        print(f"Sensitivity Score: {sensitivity_score}")
        
        # Analyze with Claude
        claude_analysis = self.analyze_with_claude(content)
        print("Claude Analysis Complete")
        
        # Store in vector database
        vector_collection = self.store_in_vector_db()
        print(f"Stored in Vector DB Collection: {vector_collection}")
        
        return self.analysis_results
```

## Step 5: Create the EUDA Chatbot

Now let's create a chatbot interface that can answer questions about EUDAs and provide remediation guidance:

```python
class EUDAChatbot:
    def __init__(self):
        # Connect to PostgreSQL for retrieving analysis
        self.conn = psycopg2.connect(
            host=os.getenv("PGVECTOR_HOST", "localhost"),
            port=os.getenv("PGVECTOR_PORT", "5432"),
            database=os.getenv("PGVECTOR_DATABASE", "vectordb"),
            user=os.getenv("PGVECTOR_USER", "postgres"),
            password=os.getenv("PGVECTOR_PASSWORD", "password")
        )
        
        # Setup Claude
        self.claude_model = claude_model
        
        # Setup vector search
        self.embeddings = titan_embeddings
    
    def get_euda_list(self):
        """Get list of analyzed EUDAs"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, file_name, analysis_date FROM euda_analysis ORDER BY analysis_date DESC")
        results = cursor.fetchall()
        cursor.close()
        
        return [{"id": r[0], "file_name": r[1], "analysis_date": r[2]} for r in results]
    
    def get_euda_analysis(self, euda_id):
        """Get full analysis for a specific EUDA"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT id, file_name, analysis_date, complexity_score, sensitivity_score, 
               remediation_score, macros_count, formulas_count, linked_data_sources, 
               summary, remediation_plan
        FROM euda_analysis
        WHERE id = %s
        """, (euda_id,))
        
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            return {"error": "EUDA not found"}
        
        return {
            "id": result[0],
            "file_name": result[1],
            "analysis_date": result[2],
            "complexity_score": result[3],
            "sensitivity_score": result[4],
            "remediation_score": result[5],
            "macros_count": result[6],
            "formulas_count": result[7],
            "linked_data_sources": result[8],
            "summary": result[9],
            "remediation_plan": result[10]
        }
    
    def vector_search(self, query, limit=3):
        """Search vector DB for relevant EUDA information"""
        try:
            # Get all collection names
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT collection_name FROM langchain_pg_embedding")
            collections = cursor.fetchall()
            cursor.close()
            
            results = []
            
            # Search each collection
            for collection in collections:
                collection_name = collection[0]
                vector_store = PGVector(
                    collection_name=collection_name,
                    connection_string=CONNECTION_STRING,
                    embedding_function=self.embeddings
                )
                
                # Search
                docs = vector_store.similarity_search(query, k=limit)
                results.extend(docs)
            
            # Sort by similarity and return top results
            return results[:limit]
            
        except Exception as e:
            print(f"Error in vector search: {e}")
            return []
    
    def ask(self, question, euda_id=None):
        """Ask a question about EUDAs or remediation"""
        # If euda_id is provided, get specific EUDA information
        euda_info = {}
        if euda_id:
            euda_info = self.get_euda_analysis(euda_id)
        
        # Search vector DB for relevant information
        relevant_docs = self.vector_search(question)
        relevant_info = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Prepare context for Claude
        context = f"""
        User Question: {question}
        
        {"EUDA Information:" if euda_id else ""}
        {json.dumps(euda_info, indent=2) if euda_id else ""}
        
        Relevant Analysis Information:
        {relevant_info}
        """
        
        # Build prompt for Claude
        prompt = f"""
        You are an expert in Excel EUDA (End User Developed Applications) remediation and Python development.
        Please answer the following question about EUDA remediation or Excel-to-Python conversion.
        
        {context}
        
        If the question is about remediation, provide specific steps, code examples, or architectural recommendations.
        Focus on how to convert Excel functionality (including formulas, macros, data processing) to Python code.
        
        If you don't have enough information to answer completely, suggest what additional information would be helpful.
        """
        
        # Get response from Claude
        response = self.claude_model.invoke(prompt)
        
        return response.content
    
    def generate_remediation_plan(self, euda_id):
        """Generate detailed remediation plan for converting EUDA to Python application"""
        # Get EUDA analysis
        euda_info = self.get_euda_analysis(euda_id)
        
        if "error" in euda_info:
            return {"error": euda_info["error"]}
        
        # Build prompt for detailed remediation plan
        prompt = f"""
        Create a detailed remediation plan to convert this Excel EUDA (End User Developed Application) to a Python application.
        
        EUDA Details:
        {json.dumps(euda_info, indent=2)}
        
        Please provide:
        
        1. High-level architecture diagram (describe in text)
        2. Required Python libraries and frameworks 
        3. Data model design
        4. Step-by-step migration plan
        5. Code examples for key functionality
        6. Testing approach
        7. Timeline estimate based on complexity
        
        Make specific recommendations for Python libraries that can replace Excel functionality,
        especially for data manipulation, calculations, UI (if needed), and reporting.
        """
        
        # Get response from Claude
        response = self.claude_model.invoke(prompt)
        
        # Update the database with the remediation plan
        cursor = self.conn.cursor()
        cursor.execute("""
        UPDATE euda_analysis
        SET remediation_plan = %s
        WHERE id = %s
        """, (response.content, euda_id))
        
        self.conn.commit()
        cursor.close()
        
        return response.content
    
    def generate_sample_code(self, euda_id, functionality):
        """Generate sample Python code for specific EUDA functionality"""
        # Get EUDA analysis
        euda_info = self.get_euda_analysis(euda_id)
        
        if "error" in euda_info:
            return {"error": euda_info["error"]}
        
        # Build prompt for code generation
        prompt = f"""
        Generate Python sample code for the following functionality from an Excel EUDA:
        
        EUDA: {euda_info['file_name']}
        Requested Functionality: {functionality}
        
        EUDA Details:
        {json.dumps(euda_info, indent=2)}
        
        Provide working Python code that implements this functionality.
        Include comments explaining how the code works and any dependencies required.
        Focus on best practices and maintainability.
        """
        
        # Get response from Claude
        response = self.claude_model.invoke(prompt)
        
        return response.content
```

## Step 6: Create a Command Line Interface

Let's create a simple command-line interface to use our EUDA analyzer and chatbot:

```python
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='EUDA Analyzer and Remediation Assistant')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze an Excel EUDA')
    analyze_parser.add_argument('file_path', help='Path to Excel file')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List analyzed EUDAs')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show EUDA analysis')
    show_parser.add_argument('euda_id', type=int, help='EUDA ID')
    
    # Ask command
    ask_parser = subparsers.add_parser('ask', help='Ask a question about EUDA remediation')
    ask_parser.add_argument('question', help='Question to ask')
    ask_parser.add_argument('--euda-id', type=int, help='EUDA ID (optional)')
    
    # Remediate command
    remediate_parser = subparsers.add_parser('remediate', help='Generate remediation plan')
    remediate_parser.add_argument('euda_id', type=int, help='EUDA ID')
    
    # Code command
    code_parser = subparsers.add_parser('code', help='Generate sample code')
    code_parser.add_argument('euda_id', type=int, help='EUDA ID')
    code_parser.add_argument('functionality', help='Functionality to implement')
    
    args = parser.parse_args()
    
    if args.command == 'analyze':
        analyzer = EUDAAnalyzer(args.file_path)
        results = analyzer.analyze()
        print(json.dumps(results, indent=2, default=str))
        
    elif args.command == 'list':
        chatbot = EUDAChatbot()
        eudas = chatbot.get_euda_list()
        print("Analyzed EUDAs:")
        for euda in eudas:
            print(f"ID: {euda['id']}, File: {euda['file_name']}, Date: {euda['analysis_date']}")
            
    elif args.command == 'show':
        chatbot = EUDAChatbot()
        euda = chatbot.get_euda_analysis(args.euda_id)
        print(json.dumps(euda, indent=2, default=str))
        
    elif args.command == 'ask':
        chatbot = EUDAChatbot()
        response = chatbot.ask(args.question, args.euda_id)
        print(response)
        
    elif args.command == 'remediate':
        chatbot = EUDAChatbot()
        plan = chatbot.generate_remediation_plan(args.euda_id)
        print(plan)
        
    elif args.command == 'code':
        chatbot = EUDAChatbot()
        code = chatbot.generate_sample_code(args.euda_id, args.functionality)
        print(code)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

## Step 7: Create a Web Interface (Optional)

For a complete web interface, you can create a Flask application with the following components:

```python
from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
from werkzeug.utils import secure_filename
from datetime import