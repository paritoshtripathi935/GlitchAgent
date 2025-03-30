from typing import Any, Dict, List, Optional, Tuple
from src.database.connectors.mongo_connector import get_mongo_instance
import logging
from bson import ObjectId
from src.utils.serializers import serialize_doc

class MongoHandler:
    def __init__(self):
        self.db = get_mongo_instance()

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a single document into MongoDB"""
        try:
            result = self.db[collection].insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logging.error(f"Error inserting document: {str(e)}")
            raise

    async def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document in MongoDB"""
        try:
            doc = self.db[collection].find_one(query)
            return serialize_doc(doc) if doc else None
        except Exception as e:
            logging.error(f"Error finding document: {str(e)}")
            raise

    async def find_many(self, 
                       collection: str, 
                       query: Dict[str, Any], 
                       skip: int = 0, 
                       limit: int = 100,
                       sort: List[Tuple[str, int]] = None) -> List[Dict[str, Any]]:
        """Find multiple documents in MongoDB with pagination and sorting"""
        try:
            cursor = self.db[collection].find(query)
            
            if sort:
                cursor = cursor.sort(sort)
            
            cursor = cursor.skip(skip).limit(limit)
            return [serialize_doc(doc) for doc in cursor]
        except Exception as e:
            logging.error(f"Error finding documents: {str(e)}")
            raise

    async def update_one(self, 
                        collection: str, 
                        query: Dict[str, Any], 
                        update: Dict[str, Any]) -> bool:
        """Update a single document in MongoDB
        
        Args:
            collection: Collection name
            query: Query to find the document
            update: Update to apply (will be wrapped with $set if it doesn't already have operators)
        """
        try:
            # Check if the update already contains MongoDB operators
            if any(key.startswith('$') for key in update.keys()):
                # If it already has operators, use it as is
                result = self.db[collection].update_one(query, update)
            else:
                # Otherwise, wrap it with $set
                result = self.db[collection].update_one(query, {"$set": update})
            
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Error updating document: {str(e)}")
            raise

    async def delete_one(self, collection: str, query: Dict[str, Any]) -> bool:
        """Delete a single document from MongoDB"""
        try:
            result = self.db[collection].delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error deleting document: {str(e)}")
            raise

    async def count_documents(self, collection: str, query: Dict[str, Any]) -> int:
        """Count documents matching a query"""
        try:
            return self.db[collection].count_documents(query)
        except Exception as e:
            logging.error(f"Error counting documents: {str(e)}")
            raise