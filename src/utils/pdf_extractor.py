import os
import tempfile

import fitz  # PyMuPDF


class PDFExtractor:
    """
    Класс для извлечения текста из PDF-файлов
    """

    @staticmethod
    def extract_text_from_bytes(pdf_bytes: bytes):
        """
        Извлекает текст из PDF-файла, переданного в виде байтов
        
        :param pdf_bytes: PDF-файл в виде байтов
        :return: Извлеченный текст
        """
        # Создаем временный файл для сохранения PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name

        try:
            # Извлекаем текст из временного файла
            text = PDFExtractor.extract_text_from_file(temp_pdf_path)
            return text
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)

    @staticmethod
    def extract_text_from_file(pdf_path: str):
        """
        Извлекает текст из PDF-файла по указанному пути
        
        :param pdf_path: Путь к PDF-файлу
        :return: Извлеченный текст
        """
        text = ""

        try:
            # Открываем PDF-файл
            doc = fitz.open(pdf_path)

            # Извлекаем текст из каждой страницы
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()

            # Закрываем документ
            doc.close()

        except Exception as e:
            raise ValueError(f"Ошибка при извлечении текста из PDF: {str(e)}")

        return text

    @staticmethod
    def get_metadata(pdf_bytes: bytes):
        """
        Извлекает метаданные из PDF-файла
        
        :param pdf_bytes: PDF-файл в виде байтов
        :return: Кортеж (метаданные, список ошибок)
        """
        errors = []
        metadata = None

        # Создаем временный файл для сохранения PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name

        try:
            # Открываем PDF-файл
            doc = fitz.open(temp_pdf_path)

            # Извлекаем метаданные
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "page_count": len(doc),
                "file_size_kb": os.path.getsize(temp_pdf_path) // 1024
            }

            # Закрываем документ
            doc.close()

        except Exception as e:
            errors.append(f"Ошибка при извлечении метаданных: {str(e)}")

        finally:
            # Удаляем временный файл
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)

        return metadata, errors
