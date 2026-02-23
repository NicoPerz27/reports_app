from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from organization.models import Group
from accounts.models import User
import os

@login_required
def scan_group_report_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    
    # Authorization Check (Cong Admin or Group Admin)
    # Reusing the strict logic from bulk view
    can_access = False
    if request.user.is_superuser:
        can_access = True
    elif request.user.role == User.Role.CONG_ADMIN and request.user.congregation == group.congregation:
        can_access = True
    elif group in request.user.managed_groups.all():
        can_access = True
        
    if not can_access:
        return render(request, '403.html', status=403)

    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        
        # Save temp file for processing
        import tempfile
        # Create a temp file to pass path to service
        # Alternatively we can pass bytes to service, but tempfile is safer for file systems
        ext = os.path.splitext(image_file.name)[1]
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf:
            for chunk in image_file.chunks():
                tf.write(chunk)
            temp_path = tf.name
        
        # Preprocess image to improve AI recognition
        try:
            from .image_utils import preprocess_image
            temp_path = preprocess_image(temp_path)
        except Exception as e:
            # If preprocessing fails, continue with original image
            print(f"Warning: Image preprocessing failed: {e}")
            
        try:
            # Prepare context list
            publishers = group.publishers.filter(active=True)
            pub_list = [{'id': p.id, 'name': f"{p.first_name} {p.last_name}"} for p in publishers]
            
            from .ai_service import scan_report_image
            extracted_data = scan_report_image(temp_path, pub_list)
            
            # extracted_data is a list of dicts: {id, hours, studies...}
            
            # For the new Modal flow, we return JSON directly
            return JsonResponse({
                'status': 'success',
                'data': extracted_data,
                'message': f"Se detectaron datos para {len(extracted_data)} publicadores."
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
                
    # If Access via GET, redirect to bulk view
    return redirect('reports:bulk_report', group_id=group.id)
