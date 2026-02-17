import json
import sys
import os
from fpdf import FPDF
from datetime import datetime

# Definición de colores
COLOR_PRIMARY = (10, 40, 90)   # Azul oscuro institucional
COLOR_SECONDARY = (100, 100, 100) # Gris oscuro
COLOR_ACCENT = (230, 240, 255) # Azul muy claro para fondos

class PDFReport(FPDF):
    def __init__(self):
        super().__init__()
        # Intentar cargar fuente Arial para soporte Unicode
        try:
            self.add_font("Arial", "", "c:/windows/fonts/arial.ttf", uni=True)
            self.add_font("Arial", "B", "c:/windows/fonts/arialbd.ttf", uni=True)
            self.add_font("Arial", "I", "c:/windows/fonts/ariali.ttf", uni=True)
            self.default_font = "Arial"
        except Exception as e:
            print(f"Warning: Could not load Arial font: {e}. Fallback to default (may fail with Unicode).")
            self.default_font = "Helvetica"
            
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Insertar imagen de encabezado si existe
        header_path = "header.jpg"
        if os.path.exists(header_path):
            # Asumiendo A4 (210mm ancho), dejamos márgenes pequeños
            # x=0, y=0, w=210 para cubrir todo el ancho superior
            self.image(header_path, x=0, y=0, w=210)
            self.ln(35) # Espacio para bajar después de la imagen (ajustar según altura real de la imagen visualmente)
        else:
            # Fallback si no hay imagen
            self.set_fill_color(*COLOR_PRIMARY)
            self.rect(0, 0, 210, 30, 'F')
            self.set_font(self.default_font, 'B', 20)
            self.set_text_color(255, 255, 255)
            self.cell(0, 20, 'LLM Council Report', 0, 1, 'C')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.default_font, 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font(self.default_font, 'B', 14)
        self.set_text_color(*COLOR_PRIMARY)
        self.set_fill_color(*COLOR_ACCENT)
        self.cell(0, 10, label, 0, 1, 'L', True)
        self.ln(4)

    def chapter_body(self, text):
        self.set_font(self.default_font, '', 11)
        self.set_text_color(0, 0, 0)
        
        # Limpieza básica de markdown
        cleaned_text = text.replace('**', '').replace('##', '').replace('###', '')
        
        self.multi_cell(0, 6, cleaned_text)
        self.ln()

    def add_section_header(self, title):
        self.ln(5)
        self.set_font(self.default_font, 'B', 12)
        self.set_text_color(*COLOR_SECONDARY)
        self.cell(0, 8, title, 'B', 1, 'L') # Subrayado
        self.ln(3)

def generate_pdf(conversation_id, output_dir="data/pdf"):
    # Construir rutas
    json_path = os.path.join("data", "conversations", f"{conversation_id}.json")
    output_path = os.path.join(output_dir, f"{conversation_id}.pdf")
    
    # Asegurar que el directorio de salida existe
    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Archivo no encontrado en {json_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: JSON inválido en {json_path}")
        return None

    pdf = PDFReport()
    pdf.add_page()
    
    # Metadatos del reporte
    pdf.set_font(pdf.default_font, 'B', 18)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.multi_cell(0, 10, data.get('title', 'Conversación Sin Título'))
    self_y = pdf.get_y()
    
    pdf.set_font(pdf.default_font, '', 10)
    pdf.set_text_color(*COLOR_SECONDARY)
    pdf.cell(0, 6, f"ID: {data.get('id', 'N/A')}", 0, 1, 'L')
    
    # Parsear y formatear fecha
    created_at = data.get('created_at', '')
    try:
        dt = datetime.fromisoformat(created_at)
        formatted_date = dt.strftime("%d/%m/%Y %H:%M")
    except:
        formatted_date = created_at
        
    pdf.cell(0, 6, f"Fecha: {formatted_date}", 0, 1, 'L')
    pdf.ln(10)

    # Procesar Mensajes
    messages = data.get('messages', [])
    
    # 1. Consulta del Usuario
    user_msgs = [m for m in messages if m.get('role') == 'user']
    if user_msgs:
        pdf.chapter_title("Consulta Inicial")
        for msg in user_msgs:
             pdf.chapter_body(msg.get('content', ''))
        pdf.ln(5)
    
    # 2. Respuesta Sintetizada (Etapa 3) - Lo más importante
    assistant_msgs = [m for m in messages if m.get('role') == 'assistant']
    
    for msg in assistant_msgs:
        if 'stage3' in msg and msg['stage3']:
            pdf.chapter_title("Respuesta Final del Consejo")
            stage3 = msg['stage3']
            response_text = stage3.get('response', '') if isinstance(stage3, dict) else str(stage3)
            
            # Indicar el modelo "Presidente"
            model_name = "Desconocido"
            if isinstance(stage3, dict):
                model_name = stage3.get('model', 'Desconocido')
                # Simplificar nombre modelo
                if '/' in model_name:
                    model_name = model_name.split('/')[1]
            
            pdf.set_font(pdf.default_font, 'I', 10)
            pdf.set_text_color(*COLOR_PRIMARY)
            pdf.cell(0, 6, f"Presidente de la Sesión: {model_name}", 0, 1)
            pdf.ln(2)
            
            pdf.chapter_body(response_text)
            pdf.ln(10)

    # 3. Apéndice: Respuestas Individuales (Etapa 1)
    # Crear nueva página para el apéndice para no saturar el reporte principal
    pdf.add_page()
    pdf.chapter_title("Apéndice: Respuestas Individuales")
    
    for msg in assistant_msgs:
        if 'stage1' in msg and msg['stage1']:
            for resp in msg['stage1']:
                model_full = resp.get('model', 'Modelo Desconocido')
                model_simple = model_full.split('/')[1] if '/' in model_full else model_full
                
                pdf.add_section_header(f"Modelo: {model_simple}")
                pdf.chapter_body(resp.get('response', ''))
                pdf.ln(5)

    try:
        pdf.output(output_path)
        print(f"PDF generado exitosamente en: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error guardando PDF: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generate_report.py <conversation_id>")
        sys.exit(1)
    
    conversation_id = sys.argv[1]
    generate_pdf(conversation_id)
