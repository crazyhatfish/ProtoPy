import re

TOKEN_MESSAGE = 1
TOKEN_LBRACKET = 3
TOKEN_RBRACKET = 4
TOKEN_LSBRACKET = 5
TOKEN_RSBRACKET = 6
TOKEN_SCOLON = 7
TOKEN_EQUALS = 8
TOKEN_VALUE = 9
TOKEN_PREFIX = 10
TOKEN_ENUM = 11
TOKEN_WHITESPACE = 12
TOKEN_NEWLINE = 13

regexes = [(TOKEN_LSBRACKET, "\["),
           (TOKEN_RSBRACKET, "\]"),
           (TOKEN_LBRACKET, "\{"),
           (TOKEN_RBRACKET, "\}"),
           (TOKEN_LBRACKET, "\{"),
           (TOKEN_RBRACKET, "\}"),
           (TOKEN_SCOLON, ";"),
           (TOKEN_EQUALS, "\="),
           (TOKEN_VALUE, "[\"'a-zA-Z0-9\.\-_]+"),
           (TOKEN_WHITESPACE, "[ \t]+"),
           (TOKEN_NEWLINE, "(\n|\r\n)")]

#TODO: turn this into a few classes,
#        get rid of the horrible globals

tokens = None
token = None

next = None

line = 1; col = 1

def tokenize(s):
    while len(s) > 0:
        found = False
        for regex in regexes:
            match = re.match(regex[1], s, re.I)
            if match != None:
                data = match.group(0)
                s = s[len(data):]
                found = True
                yield (regex[0], match.group(0))
                break
        if not found:
            raise Exception("tokenize: unknown token: %s" % s[:100])
    yield None

def next_token(token_type):
    global tokens, token, next, line, col
    if next == None:
        try:
            next = tokens.next()
        except StopIteration:
            next = None
    while next:
        if next[0] == TOKEN_WHITESPACE:
            col += len(next[1])
        elif next[0] == TOKEN_NEWLINE:
            line += 1
            col = 1
        else:
            break
        next = tokens.next()
    if next and token_type == next[0]:
        token = next
        col += len(token[1])
        try:
            next = tokens.next()
        except StopIteration:
            next = None
        return True
    return False

def expect_token(token_type):
    if not next_token(token_type) and next:
        raise Exception("expect_token: unexpected token: %s" % str(next))

def parse_statement():
    expect_token(TOKEN_VALUE)
    if token[1] == "enum":
        res = Enum()
        expect_token(TOKEN_VALUE)
        res.name = token[1]
        expect_token(TOKEN_LBRACKET)
        res.properties = {}
        while not next_token(TOKEN_RBRACKET):
            expect_token(TOKEN_VALUE)
            name = token[1]
            expect_token(TOKEN_EQUALS)
            expect_token(TOKEN_VALUE)
            value = token[1]
            while next_token(TOKEN_SCOLON):
                pass
            res.properties[name] = value
        return res
    else:
        res = Statement()
        res.prefix = token[1]
        expect_token(TOKEN_VALUE)
        res.type = token[1]
        expect_token(TOKEN_VALUE)
        res.name = token[1]
        expect_token(TOKEN_EQUALS)
        expect_token(TOKEN_VALUE)
        res.value = token[1]
        if next_token(TOKEN_LSBRACKET):
            expect_token(TOKEN_VALUE)
            if token[1] == "default":
                expect_token(TOKEN_EQUALS)
                expect_token(TOKEN_VALUE)
                res.default = token[1]
            else:
                raise Exception("parse_statement: only `default` option is supported")
            expect_token(TOKEN_RSBRACKET)
        expect_token(TOKEN_SCOLON)
        return res
    #elif next != None:
    #    raise Exception("parse_statement: expected enum or field declaration: %s" % str(next))

def parse_block():
    expect_token(TOKEN_VALUE)
    if token[1] == "message":
        expect_token(TOKEN_VALUE)
        res = Message()
        res.name = token[1]
        res.properties = []
        expect_token(TOKEN_LBRACKET)
        while not next_token(TOKEN_RBRACKET):
            statement = parse_statement()
            res.properties.append(statement)
        return res
    else:
        res = GlobalProperty()
        res.prefix = token[1]
        expect_token(TOKEN_VALUE)
        res.name = token[1]
        if next_token(TOKEN_EQUALS):
            expect_token(TOKEN_VALUE)
            res.value = token[1]
        expect_token(TOKEN_SCOLON)
        return res
    #elif next != None:
    #    raise Exception("parse_block: expected message or global property")

def parse_blocks():
    res = []
    next_token(0) #pull first token
    while next:
        block = parse_block()
        res.append(block)
    return res

""" AST Classes """

class Message:
    name = None
    properties = None
    def __repr__(self):
        return "<Message: %s: %s>" % (self.name, self.properties)
    def to_code(self):
        res = "class message_" + self.name + "(Message):\n"
        enums = []
        for prop in self.properties:
            if isinstance(prop, Enum):
                enums.append(prop.name)
        lookups = []
        defaults = []
        for prop in self.properties:
            if isinstance(prop, Statement):
                res += "    %s = None\n" % prop.name
                lookups.append(prop.to_code(prop.type in enums))
                if prop.default:
                    if prop.default.lower() == "false":
                        prop.default = "False"
                    if prop.default.lower() == "true":
                        prop.default = "True"
                    defaults.append("self.%s = %s" % (prop.name, prop.default))
        res += "\n    def __init__(self):\n"
        res += "        self.__lookup__ = ["
        res += ",\n                           ".join(lookups)
        res += "]\n\n        "
        res += "\n        ".join(defaults)
        res += "\n"
        return res

class GlobalProperty:
    prefix = None
    name = None
    value = None
    def __repr__(self):
        return "<GP: %s %s: %s>" % (self.prefix ,self.name, self.value)
    def to_code(self):
        return ""

class Statement:
    prefix = None
    type = None
    name = None
    value = None
    default = None
    def __repr__(self):
        return "<Statement: %s %s %s: %s>" % (self.prefix, self.type, self.name, self.value)
    def to_code(self, is_enum=False):
        builtin_types = ["double", "float", "int32", "int64",
                         "uint32", "uint64", "sint32", "sint64",
                         "fixed32", "fixed64", "sfixed32", "sfixed64",
                         "bool", "string", "bytes"]
        if not is_enum:
            if self.type.lower() not in builtin_types:
                type = "message_" + self.type
            else:
                type = "type_" + self.type.lower()
        else:
            type = "type_enum"
        return "(\"%s\", %s, \"%s\", %s)" % (self.prefix, type, self.name, int(self.value))

class Enum:
    name = None
    properties = None
    def __repr__(self):
        return "<Enum: %s: %s>" % (self.name, self.properties)

def main():
    global tokens
    
    import sys

    if len(sys.argv) > 1 and sys.argv[1].startswith("-h"):
        print "usage: %s < myprotobufs.proto > myprotobufs.py" % sys.argv[0]
        return

    proto = sys.stdin.read()
    tokens = tokenize(proto)

    print "from protobuf_utils import *"
    print
    
    res = parse_blocks()
    for b in res:
        print b.to_code()

if __name__ == "__main__":
    main()
