from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.errors import FileNotDecryptedError
class PDF():
    def __init__(self, filepath=None) -> None:
        if filepath:
            self.reader = PdfReader(filepath)
            if not self.reader.is_encrypted:
                self.meta = self.reader.metadata
            self.filepath = ".".join(filepath.split(".")[:-1])


    def save_pdf(self, writer, filepath):
        # Save the file
        with open(filepath, "wb") as f:
            writer.write(f)

    def encrypt(self, password):
        try:
            writer = PdfWriter()
            # Add all pages to the writer
            for page in self.reader.pages:
                writer.add_page(page)
            
            # Add a password to the new PDF
            writer.encrypt(password)

            # Save the file
            self.save_pdf(writer, f'{self.filepath}_encrypted.pdf')
        except Exception as e:
            return e

    def decrypt(self, password):
        try:
            # First check if file is actually encrypted
            if self.reader.is_encrypted:
                print("Detected file is encrypted. Decrypting...")
                result = self.reader.decrypt(password)

                if result.NOT_DECRYPTED == 0:
                    return FileNotDecryptedError('Please make sure your password is correct')
            else:
                print("File is not encrypted")
                return None
            
            writer = PdfWriter()
            # Add all pages to the writer
            for page in self.reader.pages:
                writer.add_page(page)

            # Save the new PDF to a file
            self.save_pdf(writer, f'{self.filepath}_decrypted.pdf')
        except Exception as e:
            return e


    def merge(self, files):        
        try:
            merger = PdfWriter()
            # Add all pages to the writer
            for pdf in files:
                merger.append(pdf)

            # Save the new PDF to a file
            self.save_pdf(merger, "uploads/merged.pdf")
        except Exception as e:
            return e