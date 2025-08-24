import io
import re
import csv
from typing import Union
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from django_auth_recovery_codes.utils.utils import flatten_to_lines

def to_text(data):
    """Return data as plain text string."""
    
    if not isinstance(data, (list, str)):
        raise TypeError(f"Expected the data as a list or string but got object with type {type(data).__name__}")
    
    lines = flatten_to_lines(data)
    return "\n".join(lines)

    

def to_csv(data: Union[str, list]) -> str:
    """
    Convert input data to a CSV-formatted string.

    Handles three main types of input:
    
    1. **String**: splits into rows by whitespace, commas, or newlines.
       Example:
           to_csv("code1 code2,code3\\ncode4")
           # Output:
           # code1
           # code2
           # code3
           # code4

    2. **List of strings**: each string becomes a separate row.
       Example:
           to_csv(["code1", "code2", "code3"])
           # Output:
           # code1
           # code2
           # code3

    3. **List of lists**: treated as structured rows (written exactly as-is).
       Example:
           to_csv([["id", "code"], [1, "code1"], [2, "code2"]])
           # Output:
           # id,code
           # 1,code1
           # 2,code2

    Raises:
        TypeError: if `data` is not a string or a list.

    Returns:
        str: CSV-formatted string representing the input data.

    """
    if not isinstance(data, (list, str)):
        raise TypeError(f"The data must either be a list or a string but got {data} type {type(data).__name__}")
    
    
    data_list = []

    if isinstance(data, list):
        if all(isinstance(item, list) for item in data):
            data_list = data
        else:
            data_list = [[str(item)] for item in data]
      
    elif isinstance(data, str):
        values = re.split(r"[,\s]+", data.strip())
        data_list = [[str(value)] for value in values if value]

    # write them to file at once
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(data_list)
    return output.getvalue()


def to_pdf(data: list[str]) -> bytes:
    """Return data as PDF bytes."""

    if not isinstance(data, list):
        raise TypeError(f"The data must be a list but got type {type(data).__name__}")
    
    
    buffer      = io.BytesIO()
    can         = canvas.Canvas(buffer, pagesize=letter)
    text_object = can.beginText(40, 750)

    for _, code in data:
        text_object.textLine(str(code))

    can.drawText(text_object)
    can.save()
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data
