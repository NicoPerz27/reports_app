import io
import os
from django.conf import settings
from django.http import HttpResponse
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject, TextStringObject

def generate_s21_pdf(publisher, service_year_start=2024):
    """
    Fills the S-21 PDF template with publisher data.
    """
    template_path = os.path.join(settings.BASE_DIR, 'plantilla.pdf')
    
    if not os.path.exists(template_path):
        return HttpResponse("Error: Plantilla PDF no encontrada.", status=500)

    reader = PdfReader(template_path)
    writer = PdfWriter()

    # Copy all pages (usually just one for S-21)
    # Copy all pages and form structure
    # NOTE: append_pages_from_reader should copy AcroForm, but sometimes fails.
    # We will manually ensure AcroForm is present.
    writer.append_pages_from_reader(reader)

    # Manually copy AcroForm if missing in writer but present in reader
    if "/AcroForm" not in writer.root_object and "/AcroForm" in reader.trailer["/Root"]:
        writer.root_object.update({
            NameObject("/AcroForm"): reader.trailer["/Root"]["/AcroForm"]
        })
    
    # Force NeedAppearances to ensure fields are visible
    if "/AcroForm" in writer.root_object:
        writer.root_object["/AcroForm"].update({
            NameObject("/NeedAppearances"): BooleanObject(True)
        })

    # Prepare data mapping
    fields = {}

    # --- 1. Personal Data ---
    fields['full_name'] = f"{publisher.last_name}, {publisher.first_name}"
    
    if publisher.date_of_birth:
        fields['birth_date'] = publisher.date_of_birth.strftime("%d/%m/%Y")
    
    if publisher.baptism_date:
        fields['baptism_date'] = publisher.baptism_date.strftime("%d/%m/%Y")

    # --- 2. Checkboxes (Gender, Hope, Privileges) ---
    # Helper to check a box
    # For pypdf, checking a box often means setting its value to '/Yes' (or the export value)
    # The inspection showed just field names. We'll try setting '/V': '/Yes'
    
    # Gender
    if publisher.gender == 'MALE':
        fields['gender_male'] = '/Yes'
    elif publisher.gender == 'FEMALE':
        fields['gender_female'] = '/Yes'

    # Hope
    if publisher.spiritual_hope == 'OTHER_SHEEP':
        fields['other_sheep'] = '/Yes'
    elif publisher.spiritual_hope == 'ANOINTED':
        fields['anointed'] = '/Yes'

    # Privileges
    if publisher.is_elder: fields['elder'] = '/Yes'
    if publisher.is_ministerial_servant: fields['ministerial_servant'] = '/Yes'
    if publisher.is_regular_pioneer: fields['regular_pioner'] = '/Yes' # Note typo in PDF "pioner"
    if publisher.is_special_pioneer: fields['special_pioner'] = '/Yes'
    if publisher.is_missionary: fields['missionary'] = '/Yes'

    # --- 3. Monthly Reports ---
    # We need logic to fetch the correct reports for the service year.
    # Service Year 2024: Sept 2023 - Aug 2024
    # Service Year 2025: Sept 2024 - Aug 2025
    
    # For now, let's assume we want the *current* service year relative to the request, 
    # or pass it as an argument. The prompt implied current context.
    # Let's map months names in English as they appear in PDF fields
    month_map = {
        9: 'september', 10: 'october', 11: 'november', 12: 'december',
        1: 'january', 2: 'february', 3: 'march', 4: 'april',
        5: 'may', 6: 'june', 7: 'july', 8: 'august'
    }

    # Fetch reports for this service year
    # If service_year_start is 2024, it means Sept 2024 to Aug 2025? 
    # Usually "Service Year 2025" starts Sept 2024.
    # Let's look at the dates.
    
    reports = publisher.reports.filter(
        month__year__in=[service_year_start, service_year_start + 1]
    )
    
    total_hours = 0

    for rep in reports:
        m_num = rep.month.month
        y_num = rep.month.year
        
        # Check if report belongs to strict service year range
        # Sy start: Sept of service_year_start
        # Sy end: Aug of service_year_start + 1
        if m_num >= 9 and y_num == service_year_start:
            pass # OK
        elif m_num <= 8 and y_num == service_year_start + 1:
            pass # OK
        else:
            continue # Skip reports outside this service year

        m_name = month_map.get(m_num)
        if not m_name: continue

        # 1. Participation (Checkbox)
        # If they participated OR have hours, we check the box
        if rep.participation or (rep.hours and rep.hours > 0):
            fields[m_name] = '/Yes'

        # 2. Hours (Text)
        if rep.hours and rep.hours > 0:
            fields[f'{m_name}_hours'] = str(rep.hours)
            total_hours += rep.hours

        # 3. Courses (Text)
        if rep.bible_studies and rep.bible_studies > 0:
            fields[f'{m_name}_courses'] = str(rep.bible_studies)

        # 4. Aux Pioneer (Checkbox)
        if rep.auxiliary_pioneer:
            fields[f'{m_name}_pionner'] = '/Yes' # Note typo in PDF "pionner"

    fields['total_hours'] = str(total_hours)

    # Update form fields
    # pypdf 3.x+ way:
    # We iterate over pages, then annotations, update values.
    # A simpler way with PdfWriter.update_page_form_field_values
    
    writer.update_page_form_field_values(
        writer.pages[0], fields
    )

    # Output
    buffer = io.BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    
    filename = f"S-21_{publisher.last_name}_{publisher.first_name}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
