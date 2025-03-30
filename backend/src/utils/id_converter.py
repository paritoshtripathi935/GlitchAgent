from bson import ObjectId

def mongo_id_to_str(mongo_id: ObjectId) -> str:
    """Convert MongoDB ObjectId to string"""
    return str(mongo_id)

def str_to_mongo_id(id_str: str) -> ObjectId:
    """Convert string to MongoDB ObjectId"""
    try:
        return ObjectId(id_str)
    except:
        raise ValueError("Invalid MongoDB ObjectId format")
