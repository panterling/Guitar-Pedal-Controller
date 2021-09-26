import hashlib
def stringToNumericHash(text: str):
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16)