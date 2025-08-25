#!/usr/bin/env python3
"""
ISRO Data ChromaDB Vector Database Creator

This script creates a ChromaDB vector database from the downloaded ISRO JSON files
with proper embedding and metadata configuration.
"""

import json
import os
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import hashlib
from typing import Dict, List, Any
import uuid

class ISROChromaDBBuilder:
    def __init__(self, db_path: str = "./chroma_db"):
        """
        Initialize the ChromaDB builder.
        
        Args:
            db_path (str): Path to store the ChromaDB
        """
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)
        
        # Initialize ChromaDB client with proper settings
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
        )
        
        # Use OpenAI compatible embedding function (can be changed to other models)
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Collection name for ISRO data
        self.collection_name = "isro_data"
        
    def load_json_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Load and parse JSON data from file.
        
        Args:
            file_path (Path): Path to JSON file
            
        Returns:
            List[Dict]: List of data records
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, dict):
                # If data is wrapped in a key (e.g., {"spacecrafts": [...]})
                for key, value in data.items():
                    if isinstance(value, list):
                        return value
                return []
            elif isinstance(data, list):
                return data
            else:
                return []
                
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return []
    
    def create_text_for_embedding(self, record: Dict[str, Any], data_type: str) -> str:
        """
        Create a text representation of the record for embedding.
        
        Args:
            record (Dict): The data record
            data_type (str): Type of data (spacecrafts, launchers, etc.)
            
        Returns:
            str: Text representation for embedding
        """
        if data_type == "spacecrafts":
            return f"Spacecraft: {record.get('name', 'Unknown')} with ID {record.get('id', 'Unknown')}"
        
        elif data_type == "launchers":
            return f"Launcher: {record.get('name', 'Unknown')} with ID {record.get('id', 'Unknown')}"
        
        elif data_type == "customer_satellites":
            return f"Customer Satellite: {record.get('name', 'Unknown')} with ID {record.get('id', 'Unknown')}"
        
        elif data_type == "centres":
            return f"ISRO Centre: {record.get('name', 'Unknown')} with ID {record.get('id', 'Unknown')}"
        
        else:
            # Generic fallback
            return str(record)
    
    def create_metadata(self, record: Dict[str, Any], data_type: str, source_file: str) -> Dict[str, Any]:
        """
        Create metadata for the record.
        
        Args:
            record (Dict): The data record
            data_type (str): Type of data
            source_file (str): Source JSON file name
            
        Returns:
            Dict: Metadata dictionary
        """
        metadata = {
            "data_type": data_type,
            "source_file": source_file,
            "record_id": str(record.get('id', '')),
            "record_name": str(record.get('name', '')),
            "timestamp": str(uuid.uuid4())  # Unique identifier
        }
        
        # Add all other fields as metadata
        for key, value in record.items():
            if key not in ['id', 'name']:
                metadata[f"field_{key}"] = str(value)
        
        return metadata
    
    def create_collection(self):
        """Create the ChromaDB collection with proper configuration."""
        try:
            # Delete existing collection if it exists
            try:
                self.client.delete_collection(self.collection_name)
                print(f"Deleted existing collection: {self.collection_name}")
            except:
                pass
            
            # Create new collection
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "ISRO Spacecraft, Launcher, and Centre data"}
            )
            print(f"Created collection: {self.collection_name}")
            
        except Exception as e:
            print(f"Error creating collection: {e}")
            raise
    
    def process_json_files(self):
        """Process all JSON files and add them to the vector database."""
        json_files = list(Path(".").glob("*.json"))
        
        if not json_files:
            print("No JSON files found in current directory")
            return
        
        print(f"Found {len(json_files)} JSON files to process")
        
        all_documents = []
        all_metadatas = []
        all_ids = []
        
        for json_file in json_files:
            if json_file.name in ["requirements.txt", "README.md"]:
                continue
                
            print(f"Processing {json_file.name}...")
            
            # Determine data type from filename
            data_type = json_file.stem
            
            # Load data
            records = self.load_json_data(json_file)
            
            if not records:
                print(f"No data found in {json_file.name}")
                continue
            
            print(f"  Found {len(records)} records")
            
            # Process each record
            for i, record in enumerate(records):
                # Create text for embedding
                text = self.create_text_for_embedding(record, data_type)
                
                # Create metadata
                metadata = self.create_metadata(record, data_type, json_file.name)
                
                # Create unique ID
                record_id = f"{data_type}_{record.get('id', i)}_{hashlib.md5(text.encode()).hexdigest()[:8]}"
                
                all_documents.append(text)
                all_metadatas.append(metadata)
                all_ids.append(record_id)
        
        # Add all documents to collection in batches
        if all_documents:
            print(f"\nAdding {len(all_documents)} documents to ChromaDB...")
            
            # Process in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(all_documents), batch_size):
                end_idx = min(i + batch_size, len(all_documents))
                batch_docs = all_documents[i:end_idx]
                batch_metadatas = all_metadatas[i:end_idx]
                batch_ids = all_ids[i:end_idx]
                
                self.collection.add(
                    documents=batch_docs,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                print(f"  Added batch {i//batch_size + 1}: {len(batch_docs)} documents")
            
            print(f"Successfully added {len(all_documents)} documents to ChromaDB")
        else:
            print("No documents to add")
    
    def test_collection(self):
        """Test the collection with a simple query."""
        try:
            print("\nTesting collection with sample query...")
            
            # Get collection info
            count = self.collection.count()
            print(f"Total documents in collection: {count}")
            
            # Sample query
            results = self.collection.query(
                query_texts=["spacecraft"],
                n_results=3
            )
            
            print("Sample query results:")
            for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                print(f"  {i+1}. {doc[:100]}...")
                print(f"     Type: {metadata.get('data_type', 'Unknown')}")
                print(f"     Name: {metadata.get('record_name', 'Unknown')}")
                print()
                
        except Exception as e:
            print(f"Error testing collection: {e}")
    
    def build_database(self):
        """Main method to build the complete database."""
        print("🚀 Building ISRO ChromaDB Vector Database")
        print("=" * 50)
        
        try:
            # Create collection
            self.create_collection()
            
            # Process JSON files
            self.process_json_files()
            
            # Test the collection
            self.test_collection()
            
            print("\n" + "=" * 50)
            print("✅ ChromaDB vector database created successfully!")
            print(f"Database location: {self.db_path.absolute()}")
            print(f"Collection name: {self.collection_name}")
            
        except Exception as e:
            print(f"❌ Error building database: {e}")
            raise

def main():
    """Main function to create the ChromaDB."""
    builder = ISROChromaDBBuilder()
    builder.build_database()

if __name__ == "__main__":
    main()
