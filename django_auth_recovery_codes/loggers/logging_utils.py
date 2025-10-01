import logging

class RightIndentedFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super().__init__(fmt, datefmt, style)

    def format(self, record):
        
        # Add a custom indent to the beginning of the log message
        original_message = super().format(record)
        return f"    {original_message}"  



