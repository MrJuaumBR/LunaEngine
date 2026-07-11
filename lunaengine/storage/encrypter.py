import random
import os
import json
import base64
import hashlib
import zlib
import zipfile
import uuid

from typing import Union, ClassVar

class MachineEncryption:
    def get_hwid_key(self, data_length: Union[int, float]) -> bytes:
        data_length = int(data_length)
        
        hwid:bytes = str(uuid.getnode()).encode()
        key_stream = b""
        counter = 0
        while len(key_stream) < data_length:
            chunk = hashlib.sha256(hwid + str(counter).encode()).digest()
            key_stream += chunk
            counter += 1
        
        return key_stream[:data_length]
    
    def xor_cipher(self, data: bytes) -> bytes:
        key_stream = self.get_hwid_key(len(data))
        
        return bytes(a ^ b for a, b in zip(data, key_stream))
    
    def encryptClass(self, obj: dict) -> bytes:
        data = json.dumps(obj).encode()
        
        data = zlib.compress(data)
        data = self.xor_cipher(data)
        data = base64.b64encode(data)
        
        return data
    
    def decryptClass(self, data: bytes) -> dict:
        data:bytes = base64.b64decode(data)
        data:bytes = self.xor_cipher(data)
        data:bytes = zlib.decompress(data)
        ddata:dict = json.loads(data.decode())
        return ddata
