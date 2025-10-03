# """
# view_download_helper.py

# This file contains helper functions specific to the views in specific for downloads.

# Purpose:
# - Keep views.py clean and uncluttered.
# - Provide functionality that is specific to the view logic.

# Notes:
# - Not a general-purpose utilities module.
# - Functions here are intended to work only with the views.
# - Can be expanded in the future with more view-specific helpers.
# """


from django.conf import settings

from django_auth_recovery_codes.utils.exporters.file_converters import to_csv, to_pdf, to_text



def get_desired_format():
    """
    Takes settings and returns the desired format to save as e.g txt, pdf, or csv
    """
    format_to_save = getattr(settings, 'DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT', 'txt')
    file_name      = getattr(settings, "DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME", "recovery_codes")

    return format_to_save, file_name


def format_recovery_codes_for_download(raw_codes):
    """
    Convert a list of recovery codes into the desired file format for download.

    This function checks the project settings to determine the default
    format (TXT, CSV, or PDF) and generates the appropriate file content,
    content type, and file name for use in an HTTP response.

    Args:
        raw_codes (List[str]): A list of recovery code strings.

    Returns:
        Tuple[bytes, str, str]:
            - response_content: The encoded content of the file, ready for download.
            - content_type: The MIME type corresponding to the file format.
            - file_name: The name of the file to be used in the download header.
    
    Notes:
        - The default format is 'txt' if not specified in settings.
        - CSV and PDF formats require the corresponding `to_csv` or `to_pdf` helper functions.
    """
  
    format_to_save, file_name = get_desired_format()

    # Default filename and content
    default_file_name = "recovery_codes.txt"
    response_content  = b""
    content_type      = "text/plain"

    match format_to_save:
        case "txt":
            file_name        = f"{file_name}.txt"
            response_content = to_text(raw_codes).encode("utf-8")

        case "csv":
            file_name        = f"{file_name}.csv"
            response_content = to_csv(raw_codes).encode("utf-8")
            content_type     = "text/csv"

        case "pdf":
            file_name        = f"{file_name}.pdf"
            response_content = to_pdf(raw_codes)
            content_type     = "application/pdf"

    if not file_name:
        file_name = default_file_name

    return response_content, content_type, file_name
