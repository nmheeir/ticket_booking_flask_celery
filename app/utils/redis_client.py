import redis
from app.config import Config

redis_client = redis.from_url(Config.REDIS_URL)

def set_key(key, value, expiry=None):
    """Set a key-value pair in Redis with optional expiry time"""
    if expiry:
        redis_client.setex(key, expiry, value)
    else:
        redis_client.set(key, value)

def get_key(key):
    """Get value for a key from Redis"""
    return redis_client.get(key)

def delete_key(key):
    """Delete a key from Redis"""
    redis_client.delete(key)

def set_hash(name, mapping):
    """Set a hash map in Redis"""
    redis_client.hmset(name, mapping)

def get_hash(name):
    """Get all fields and values in a hash"""
    return redis_client.hgetall(name)

def increment_key(key):
    """Increment a key's value"""
    return redis_client.incr(key)

def add_to_set(name, *values):
    """Add values to a set"""
    redis_client.sadd(name, *values)

def get_set_members(name):
    """Get all members of a set"""
    return redis_client.smembers(name) 