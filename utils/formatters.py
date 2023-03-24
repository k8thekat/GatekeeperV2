def message_formatter(message: str) -> str:
    """Formats the message for Discord \n
    `Bold = \\x01, \\x02` \n
    `Italic = \\x03, \\x04` \n
    `Underline = \\x05, \\x06` \n"""
    # Bold
    message = message.replace('\x01', '**')
    message = message.replace('\x02', '**')
    # Italic
    message = message.replace('\x03', '*')
    message = message.replace('\x04', '*')
    # Underline
    message = message.replace('\x05', '__')
    message = message.replace('\x06', '__')
    return message
