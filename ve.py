# embedding/vector_embedder.py
import boto3
import json
import base64
import uuid
from config.settings import (
    AWS_ACCESS_KEY_ID, 
    AWS_SECRET_ACCESS_KEY, 
    AWS_REGION,
    TITAN_TEXT_MODEL,
    TITAN_IMAGE_MODEL
)

class TitanEmbedder:
    def __init__(self):
        # Initialize Bedrock client
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        self.text_model_id = TITAN_TEXT_MODEL
        self.image_model_id = TITAN_IMAGE_MODEL
    
    def embed_text(self, text):
        """Generate embeddings for text using Amazon Titan"""
        try:
            # Prepare the request body
            request_body = {
                "inputText": text
            }
            
            # Convert the request body to JSON
            body = json.dumps(request_body)
            
            # Make the API call
            response = self.bedrock_client.invoke_model(
                modelId=self.text_model_id,
                contentType='application/json',
                accept='application/json',
                body=body
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            
            # Extract and return the embedding
            if 'embedding' in response_body:
                return response_body['embedding']
            else:
                print(f"Error: Unexpected response format: {response_body}")
                return None
        except Exception as e:
            print(f"Error generating text embedding: {str(e)}")
            return None
    
    def embed_image(self, image_path):
        """Generate embeddings for an image using Amazon Titan"""
        try:
            # Read the image file
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            # Encode the image in base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # Prepare the request body
            request_body = {
                "inputImage": base64_image
            }
            
            # Convert the request body to JSON
            body = json.dumps(request_body)
            
            # Make the API call
            response = self.bedrock_client.invoke_model(
                modelId=self.image_model_id,
                contentType='application/json',
                accept='application/json',
                body=body
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            
            # Extract and return the embedding
            if 'embedding' in response_body:
                return response_body['embedding']
            else:
                print(f"Error: Unexpected response format: {response_body}")
                return None
        except Exception as e:
            print(f"Error generating image embedding: {str(e)}")
            return None

    def generate_euda_embedding(self, euda_info):
        """Generate embeddings for an EUDA based on its summary information"""
        # Create a descriptive text about the EUDA
        euda_description = f"""
        Filename: {euda_info.get('filename', 'Unknown')}
        Number of sheets: {len(euda_info.get('sheets', []))}
        Has macros: {euda_info.get('has_macros', False)}
        Has formulas: {euda_info.get('has_formulas', False)}
        Has external connections: {euda_info.get('has_external_connections', False)}
        Complexity score: {euda_info.get('complexity_score', 0)}
        Formula count: {euda_info.get('formula_count', 0)}
        Sheet names: {', '.join(euda_info.get('sheets', []))}
        """
        
        # Generate embedding for the EUDA description
        return self.embed_text(euda_description)
    
    def generate_macro_embedding(self, macro_info):
        """Generate embeddings for a macro based on its code and metadata"""
        # Create a descriptive text about the macro
        macro_description = f"""
        Macro name: {macro_info.get('name', 'Unknown')}
        Macro type: {macro_info.get('type', 'Unknown')}
        Purpose: {macro_info.get('purpose', 'Unknown')}
        Complexity: {macro_info.get('complexity', 0)}
        Interacts with database: {macro_info.get('interacts_with_database', False)}
        Interacts with external files: {macro_info.get('interacts_with_external_files', False)}
        Handles events: {macro_info.get('handles_events', False)}
        Has user interface: {macro_info.get('has_user_interface', False)}
        
        Code:
        {macro_info.get('code', '')}
        """
        
        # Generate embedding for the macro description
        return self.embed_text(macro_description)
    
    def generate_formula_embedding(self, formula_info):
        """Generate embeddings for a formula based on its details"""
        # Create a descriptive text about the formula
        formula_description = f"""
        Sheet: {formula_info.get('sheet', 'Unknown')}
        Cell: {formula_info.get('cell', 'Unknown')}
        Formula: {formula_info.get('formula', 'Unknown')}
        Formula type: {formula_info.get('type', 'Unknown')}
        """
        
        # Generate embedding for the formula description
        return self.embed_text(formula_description)