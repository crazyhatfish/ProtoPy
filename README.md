# ProtoPy
tiny pure python protobuf implementation

this isn't anywhere near a good implementation (actually not complete either) of Protobufs (see Google's) but it doesn't require any non-std libraries and the runtime is around 400 lines.

## Example usage
First, compile the Protobufs to Python with the `protobuf_compile.py` script.
```
python protobuf_compile.py < exampleprotos.proto > exampleprotos.py
```
Then the Protobufs can be used as follows:
```python
from exampleprotos import *

# encoding
>>> msg = message_CMsgClientGamePlayed()
>>> msg.game_id = 1234
>>> msg.names = ["cat", "dog", "fish"]
>>> msg.token = "TOKENTOKENTOKENTOKEN"

>>> encoded = msg.encode()
>>> encoded
'\x11\xd2\x04\x00\x00\x00\x00\x00\x002\x14TOKENTOKENTOKENTOKENj\x03catj\x03dogj\x04fish'

# decoding
>>> msg = message_CMsgClientGamePlayed(encoded)
>>> print msg.game_id
1234
>>> print msg.names
["cat", "dog", "fish"]
>>> print msg.token
"TOKENTOKENTOKENTOKEN"
```
