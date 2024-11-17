# utils.py

import os
import magic

def validate_csv(file):
    CSV_EXTENSIONS = {'csv'}
    CSV_MIME_TYPES = {'text/csv', 'application/vnd.ms-excel', 'text/plain'}

    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in CSV_EXTENSIONS):
        return False, "Invalid CSV extension."

    file.seek(0)
    mime = magic.Magic(mime=True)
    file_mime_type = mime.from_buffer(file.read(1024))
    if file_mime_type not in CSV_MIME_TYPES:
        file.seek(0)
        return False, "CSV file type does not match signature."

    MAX_CSV_SIZE = 10 * 1024 * 1024  # 10 MB
    file.seek(0, os.SEEK_END)
    if file.tell() > MAX_CSV_SIZE:
        file.seek(0)
        return False, "CSV file size exceeds limit."

    file.seek(0)
    return True, "CSV is valid."
