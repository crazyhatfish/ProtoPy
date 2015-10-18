# ProtoPy
tiny pure python protobuf implementation

this isn't anywhere near a good implementation of Protobufs (see Google's) but it doesn't require any non-std libraries and the runtime is around 400 lines.

## Example usage
After compiling the Protobuf to Python with the `protobuf_compile.py` script, the Protobuf can be used as follows:
```python
from exampleprotos import *

# encoding
>>> msg = message_example()
>>> msg.a = 1
>>> msg.b = [1, 2, 3]

>>> encoded = msg.encode()

# decoding
>>> msg = message_example(encoded)
>>> print msg.a
1
>>> print msg.b
[1, 2, 3]
```
