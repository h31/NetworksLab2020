from datetime import datetime
from schema import Schema, And, Use, SchemaError


class MessageValidator:
    message_schema = {}

    def __init__(self):
        self.message_schema = Schema({
            'name': And(str),
            'time_sent': And(datetime),
            'content': And(str)
        })

    def check(self, msg):
        try:
            self.message_schema.validate(msg)
            return True
        except SchemaError:
            return False
