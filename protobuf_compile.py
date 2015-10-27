import re, sys

from collections import namedtuple

Token = namedtuple("Token", "name, data")

class ProtoCompiler:
    regexes = [("TOKEN_LSBRACKET", "\["),
               ("TOKEN_RSBRACKET", "\]"),
               ("TOKEN_LBRACKET", "\{"),
               ("TOKEN_RBRACKET", "\}"),
               ("TOKEN_LBRACKET", "\{"),
               ("TOKEN_RBRACKET", "\}"),
               ("TOKEN_SCOLON", ";"),
               ("TOKEN_EQUALS", "\="),
               ("TOKEN_COMMENT", "//"),
               ("TOKEN_VALUE", "[\"'a-zA-Z0-9\.\-_]+"),
               ("TOKEN_WHITESPACE", "[ \t]+"),
               ("TOKEN_NEWLINE", "(\n|\r\n)")]
    
    def __init__(self, code):
        self.code = code

        for name, regex in self.regexes:
            setattr(self, name, name)

        self.line = 1
        self.col = 1

        self.token = None
        self.next = self.tokenize_one()
        self.skip_whitespace()

    def tokenize_one(self):
        if len(self.code) <= 0:
            return None
            
        for name, regex in self.regexes:
            match = re.match(regex, self.code, re.I)
            if match is not None:
                data = match.group(0)
                data_len = len(data)
                
                self.code = self.code[data_len:]

                if name == self.TOKEN_NEWLINE:
                    self.line += 1
                    self.col = 1
                elif name == self.TOKEN_COMMENT:
                    newline = re.search("(\n|\r\n)", self.code)
                    if newline is None:
                        self.code = ""
                        return None
                    else:
                        self.code = self.code[newline.start():]
                        continue # note: TOKEN_COMMENT before TOKEN_NEWLINE
                else:
                    self.col += data_len
                
                return Token(name, data)
            
        raise Exception("get_next_token: unknown token: %s... (%d:%d)" % (self.code[:10], self.line, self.col))

    def skip_whitespace(self):
        while self.next is not None:
            if self.next.name == self.TOKEN_WHITESPACE or self.next.name == self.TOKEN_NEWLINE:
                self.next = self.tokenize_one()
            else:
                break

    def next_token(self, token_name):
        if self.next is None:
            return False

        if self.next.name == token_name:
            self.token = self.next
            self.next = self.tokenize_one()
            self.skip_whitespace()
            return True
        
        self.skip_whitespace()
        return False

    def expect_token(self, token_name):
        if not self.next_token(token_name):
            raise Exception("expect_token: unexpected token: %s (%d:%d)" % (self.next, self.line, self.col))

    def parse_message_statement(self):
        res = Statement()
        
        self.expect_token(self.TOKEN_VALUE)
        res.prefix = self.token.data
        self.expect_token(self.TOKEN_VALUE)
        res.type = self.token.data
        self.expect_token(self.TOKEN_VALUE)
        res.name = self.token.data

        self.expect_token(self.TOKEN_EQUALS)
        self.expect_token(self.TOKEN_VALUE)
        res.value = self.token.data

        if self.next_token(self.TOKEN_LSBRACKET):
            self.expect_token(self.TOKEN_VALUE)
            if self.token.data == "default":
                self.expect_token(self.TOKEN_EQUALS)
                self.expect_token(self.TOKEN_VALUE)
                res.default = self.token.data
            else:
                raise Exception("parse_message_statement: only `default` option is supported (%d:%d)" % (self.line, self.col))
            self.expect_token(self.TOKEN_RSBRACKET)
            
        self.expect_token(self.TOKEN_SCOLON)
        return res

    def parse_message(self):
        # 
        
        res = Message()

        self.expect_token(self.TOKEN_VALUE)
        res.name = self.token.data
        self.expect_token(self.TOKEN_LBRACKET)
        res.properties = []
        res.children = {}

        while not self.next_token(self.TOKEN_RBRACKET):
            if self.next is None:
                raise Exception("parse_message: EOF before end of message declaration")
            if self.next.data == "enum":
                self.expect_token(self.TOKEN_VALUE)
                data = self.parse_enum()
                data.parent = res
                if data.name in res.children:
                    raise Exception("parse_message: multiple enums with same name (%d:%d)" % (self.line, self.col))
                res.children[data.name] = data
            elif self.next.data == "message":
                self.expect_token(self.TOKEN_VALUE)
                data = self.parse_message()
                data.parent = res
                if data.name in res.children:
                    raise Exception("parse_message: multiple messages with same name (%d:%d)" % (self.line, self.col))
                res.children[data.name] = data
            else:
                statement = self.parse_message_statement()
                statement.parent = res
                res.properties.append(statement)

        return res

    def parse_enum(self):
        # after `enum` token
        
        res = Enum()
        
        self.expect_token(self.TOKEN_VALUE)
        res.name = self.token.data
        self.expect_token(self.TOKEN_LBRACKET)
        res.properties = {}
        
        while not self.next_token(self.TOKEN_RBRACKET):
            self.expect_token(self.TOKEN_VALUE)
            name = self.token.data
            self.expect_token(self.TOKEN_EQUALS)
            self.expect_token(self.TOKEN_VALUE)
            value = self.token.data

            res.properties[name] = value
            
            while self.next_token(self.TOKEN_SCOLON):
                pass

        return res

    def parse_statement(self):
        if self.next is None:
            return None # eof
        
        self.expect_token(self.TOKEN_VALUE)
        if self.token.data == "message":
            return self.parse_message()
        elif self.token.data == "enum":
            return self.parse_enum()
        else:
            raise NotImplementedError("parse_statement: `%s` directives not implemented (%d:%d)" % (self.token.data, self.line, self.col))

    def parse_proto(self):
        res = Proto()
        res.children = {}
        while 1:
            statement = self.parse_statement()
            if statement is None:
                break
            statement.parent = res
            if statement.name in res.children:
                raise Exception("parse_proto: `%s` is already declared (%d:%d)" % (statement.name, self.line, self.col))
            res.children[statement.name] = statement
        return res

class Proto:
    children = None
    parent = None
    
    def __repr__(self):
        return "<Proto: %s>" % self.children
    
    def to_code(self):
        res = "from protobuf_utils import *\n\n"
        for name, child in self.children.items():
            res += child.to_code() + "\n"
        return res

class Message:
    name = None
    properties = None

    parent = None
    children = None
    
    def __repr__(self):
        return "<Message: %s: %s, children: %s>" % (self.name, self.properties, self.children)
    
    def to_code(self):
        res = "class " + self.name + "(Message):\n"
        
        for name, child in self.children.items():
            lines = child.to_code().splitlines()
            res += '\n'.join(map(lambda x: "    " + x, lines)) + "\n\n"
                
        lookups = []
        defaults = []
        for prop in self.properties:
            if isinstance(prop, Statement):
                res += "    %s = None\n" % prop.name
                code, default = prop.to_code()
                lookups.append(code)
                if default is not None:
                    defaults.append(default)

        if len(lookups) > 0:
            res += "\n    def __init__(self):\n"
            res += "        self.__lookup__ = ["
            res += ",\n                           ".join(lookups)
            res += "]\n"
        
            if len(defaults) > 0:
                res += "\n        "
                res += "\n        ".join(defaults)
                res += "\n"
        else:
            res += "    pass\n"
        
        return res

class Statement:
    prefix = None
    type = None
    name = None
    value = None
    default = None

    parent = None
    
    def __repr__(self):
        return "<Statement: %s %s %s: %s>" % (self.prefix, self.type, self.name, self.value)

    def to_code(self):
        builtin_types = ["double", "float", "int32", "int64",
                         "uint32", "uint64", "sint32", "sint64",
                         "fixed32", "fixed64", "sfixed32", "sfixed64",
                         "bool", "string", "bytes"]

        default = self.default
        if default is not None:
            if default.lower() == "false":
                default = "False"
            if default.lower() == "true":
                default = "True"
        
        if self.type.lower() not in builtin_types:
            type = self.get_absolute_type(self.type)
            node = self.get_type(type)
            if isinstance(node, Enum):
                type = "type_enum"
                
                if self.default in node.properties:
                    default = node.properties[self.default]
        else:
            type = "type_" + self.type.lower()

        code = "(\"%s\", %s, \"%s\", %s)" % (self.prefix, type, self.name, int(self.value))

        if default is not None:
            default = "self.%s = %s" % (self.name, default)
        
        return (code, default)

    #TODO: two slightly out-of-place functions below, find a better place for them

    def get_type(self, name):
        " traverses AST looking for type declaration "

        root = self
        while root.parent is not None:
            root = root.parent

        if name.startswith("."):
            name = name[1:]

        node = root
        path = name.split(".")
        while len(path) > 0:
            target_name = path.pop(0)
            if target_name not in node.children:
                return None
            node = node.children[target_name]

        return node

    def get_absolute_type(self, name):
        " transforms relative typing to absolute form "
        
        if name.startswith("."):
            name = name[1:]

        top_level = name
        lower_levels = ""
        if "." in name:
            top_level, lower_levels = name.split(".", 1)
            lower_levels = "." + lower_levels

        path = []
        found_top_level = False
        node = self.parent
        while node is not None:
            if top_level in node.children and not found_top_level:
                found_top_level = True
                path.append(top_level)
            if found_top_level and node.parent is not None:
                path.append(node.name)
            node = node.parent

        if not found_top_level:
            raise Exception("get_absolute_type: can't find type (%s)" % name)

        path.reverse()
        return '.'.join(path) + lower_levels

class Enum:
    name = None
    properties = None

    parent = None
    
    def __repr__(self):
        return "<Enum: %s: %s>" % (self.name, self.properties)
    
    def to_code(self):
        res = "class %s:\n" % self.name
        for prop, value in self.properties.items():
            res += "    %s = %s\n" % (prop, value)
        return res

def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1].startswith("-h"):
        print "usage: %s < myprotobufs.proto > myprotobufs.py" % sys.argv[0]
        return

    data = sys.stdin.read()
    compiler = ProtoCompiler(data)
    proto = compiler.parse_proto()
    
    print proto.to_code()

if __name__ == "__main__":
    main()
