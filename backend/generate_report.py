import json
import sys
import os
from fpdf import FPDF
from datetime import datetime

# Definición de colores
COLOR_PRIMARY = (0, 123, 255)   # Azul corporativo (ejemplo basado en solicitud)
COLOR_TEXT_HEADER = (10, 40, 90) # Azul oscuro para textos principales
COLOR_SECONDARY = (100, 100, 100) # Gris oscuro
COLOR_ACCENT = (245, 245, 245) # Gris muy claro para fondos

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
        # Logo en esquina superior izquierda
        header_path = "logo.png"
        if os.path.exists(header_path):
            self.image(header_path, x=10, y=10, w=40) 
        
        # Título de la aplicación alineado a la derecha o centro
        self.set_y(15)
        self.set_x(60) # Mover a la derecha del logo
        self.set_font(self.default_font, 'B', 24)
        self.set_text_color(*COLOR_TEXT_HEADER)
        self.cell(0, 10, 'Consejo CrediBusiness LLM', 0, 1, 'R')
        
        # Línea separadora
        self.ln(10)
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.default_font, 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font(self.default_font, 'B', 14)
        self.set_text_color(*COLOR_TEXT_HEADER)
        # Borde izquierdo decorativo
        self.set_line_width(1)
        self.set_draw_color(*COLOR_PRIMARY)
        self.line(10, self.get_y(), 10, self.get_y() + 8)
        
        self.set_x(12)
        self.cell(0, 8, label, 0, 1, 'L')
        self.ln(2)

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
    
    # Título del Reporte (Metadata)
    pdf.set_font(pdf.default_font, 'B', 16)
    pdf.set_text_color(*COLOR_PRIMARY)
    pdf.multi_cell(0, 10, data.get('title', 'Conversación Sin Título'))
    
    pdf.ln(2)
    
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
    
    # FORZAR NUEVA PÁGINA PARA RESPUESTAS INDIVIDUALES
    pdf.add_page()
    
    # 2. Apéndice: Respuestas Individuales (Etapa 1)
    # El usuario pidió: Pregunta -> Respuestas Miembros -> Final
    assistant_msgs = [m for m in messages if m.get('role') == 'assistant']
    
    pdf.chapter_title("Respuestas de los Miembros del Consejo")
    pdf.ln(5)
    
    for msg in assistant_msgs:
        if 'stage1' in msg and msg['stage1']:
            for i, resp in enumerate(msg['stage1']):
                if i > 0:
                    pdf.add_page() # Cada modelo en una hoja nueva (o al menos separado si es la misma sección)
                    # Reiniciar título de sección si cambiamos de hoja para claridad
                    pdf.chapter_title("Respuestas de los Miembros del Consejo (Cont.)")
                    pdf.ln(5)
                
                model_full = resp.get('model', 'Modelo Desconocido')
                model_simple = model_full.split('/')[1] if '/' in model_full else model_full
                
                # Encabezado del Modelo
                pdf.set_font(pdf.default_font, 'B', 14)
                pdf.set_text_color(*COLOR_TEXT_HEADER)
                pdf.cell(0, 10, f"Miembro: {model_simple}", 0, 1, 'L')
                pdf.ln(2)
                
                # Cuerpo de la respuesta
                pdf.chapter_body(resp.get('response', ''))

    # FORZAR NUEVA PÁGINA PARA RESPUESTA FINAL
    pdf.add_page()

    # 3. Respuesta Final del Presidente (Etapa 3)
    for msg in assistant_msgs:
        if 'stage3' in msg and msg['stage3']:
            pdf.chapter_title("Resolución Final del Presidente")
            pdf.ln(5)
            
            stage3 = msg['stage3']
            response_text = stage3.get('response', '') if isinstance(stage3, dict) else str(stage3)
            
            # Indicar el modelo "Presidente"
            model_name = "Desconocido"
            if isinstance(stage3, dict):
                model_name = stage3.get('model', 'Desconocido')
                # Simplificar nombre modelo
                if '/' in model_name:
                    model_name = model_name.split('/')[1]
            
            pdf.set_font(pdf.default_font, 'B', 12)
            pdf.set_text_color(*COLOR_PRIMARY)
            pdf.cell(0, 6, f"Presidente de la Sesión: {model_name}", 0, 1)
            pdf.ln(5)
            
            pdf.chapter_body(response_text)

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
