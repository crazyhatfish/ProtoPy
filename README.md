# ProtoPy
tiny pure python protobuf implementation

this isn't anywhere near a good implementation (actually not complete either) of Protobufs (see Google's) but it doesn't require any non-std libraries and the runtime is around 400 lines.

## Example usage
First, compile the Protobufs to Python with the `protobuf_compile.py` script.
```
python protobuf_compile.py < exampleproto.proto > exampleproto.py
```
Then the Protobufs can be used as follows:
```python
from exampleproto import *

# encoding
>>> game = CMsgClientGamesPlayed.Game()
>>> game.game_id = 1234
>>> game.game_name = "blah"
>>> game.game_version = EGameVersion.k_EGameVersionNone

>>> msg = CMsgClientGamesPlayed()
>>> msg.game_ip_address = 0x11223344
>>> msg.game_port = 1337
>>> msg.games = [game]
>>> msg.token = "TOKENTOKENTOKENTOKEN"

>>> encoded = msg.encode()
>>> encoded
'\x10\xc4\xe6\x88\x89\x01\x18\xb9\n*\x14TOKENTOKENTOKENTOKENR\x11\t\xd2\x04\x00\x00\x00\x00\x00\x00\x12\x04blah(\x00'

# decoding
>>> msg = CMsgClientGamesPlayed()
>>> msg.decode(encoded)
>>> msg.games
[{'game_id': 1234L, 'game_name': 'blah', 'game_version': 0L}]
>>> msg.games[0].game_name
'blah'
>>> msg.token
'TOKENTOKENTOKENTOKEN'
>>> msg.to_dict()
{'game_port': 1337, 'token': 'TOKENTOKENTOKENTOKEN', 'game_ip_address': 287454020, 'games': [{'game_id': 1234, 'game_name': 'blah', 'game_version': 0}]}
```
