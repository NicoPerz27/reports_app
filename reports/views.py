
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from organization.models import Group, Publisher
from reports.models import MonthlyReport
from accounts.models import User
from django.db.models import Prefetch
from django.contrib import messages
import os

# Import Scan Logic
from .scan_views import scan_group_report_view


@login_required
def dashboard_view(request):
    """
    Main dashboard for Group Admins.
    Displays list of publishers in their groups and current month's report status.
    """
    user = request.user
    
    # Logic for Congregation Admin or Group Admin
    if user.is_superuser:
        groups = Group.objects.all()
    elif user.role == User.Role.CONG_ADMIN and user.congregation:
        # Cong Admin sees all groups in their congregation
        groups = Group.objects.filter(congregation=user.congregation)
    else:
        # Group Admin sees only assigned groups
        groups = user.managed_groups.all()

    # Current month context
    today = timezone.localtime().date()
    current_month_date = today.replace(day=1)
    
    # Pre-fetch reports for the current month to avoid N+1 queries
    current_reports_prefetch = Prefetch(
        'reports',
        queryset=MonthlyReport.objects.filter(month=current_month_date),
        to_attr='current_report_list'
    )

    context_groups = []
    
    for group in groups:
        publishers = Publisher.objects.filter(group=group).filter(active=True).prefetch_related(current_reports_prefetch)
        
        group_data = {
            'group': group, # Pass full object for token access
            'id': group.id,
            'name': group.name,
            'publishers_data': []
        }
        
        for pub in publishers:
            # Get the report if it exists in the pre-fetched list
            report = pub.current_report_list[0] if pub.current_report_list else None
            status = report.status if report else 'MISSING' # 'MISSING' means no report object created yet
            
            group_data['publishers_data'].append({
                'publisher': pub,
                'report': report,
                'status': status
            })
            
        context_groups.append(group_data)


    
    # Statistics Calculation
    total_publishers = 0
    total_reports_submitted = 0
    total_reports_pending = 0
    
    for group_data in context_groups:
        pubs = group_data['publishers_data']
        total_publishers += len(pubs)
        total_reports_submitted += sum(1 for p in pubs if p['status'] in ['SUBMITTED', 'APPROVED'])
        total_reports_pending += sum(1 for p in pubs if p['status'] in ['PENDING', 'MISSING'])

    percent_complete = 0
    if total_publishers > 0:
        percent_complete = int((total_reports_submitted / total_publishers) * 100)

    return render(request, 'reports/dashboard.html', {
        'groups': context_groups,
        'current_month': current_month_date,
        'congregation': user.congregation if hasattr(user, 'congregation') else None,
        'stats': {
            'publishers': total_publishers,
            'submitted': total_reports_submitted,
            'pending': total_reports_pending,
            'percent': percent_complete
        },
        'is_cong_admin': user.role == User.Role.CONG_ADMIN or user.is_superuser
    })

@login_required
def download_pdf_view(request, publisher_id):
    """
    Generates and returns the S-21 PDF card for a publisher.
    """
    # Ensure user has access to this publisher's group
    publisher = get_object_or_404(Publisher, id=publisher_id)
    
    has_access = False
    if request.user.is_superuser:
        has_access = True
    elif request.user.role == User.Role.CONG_ADMIN and request.user.congregation == publisher.group.congregation:
        has_access = True
    elif publisher.group in request.user.managed_groups.all():
        has_access = True
        
    if not has_access:
         return render(request, '403.html', status=403)

    # Get reports for the current service year (Sept-Aug logic needed here really, 
    # but for prototype we fetch all or just last 12)
    reports = publisher.reports.all().order_by('month')
    
    # Calculate simple totals
    total_hours = sum(r.hours for r in reports if r.hours)

    context = {
        'publisher': publisher,
        'reports': reports,
        'service_year': '2024-2025', # Dynamic year logic can be added
        'total_hours': total_hours
    }
    # Get reports for the current service year (Sept-Aug logic needed here really, 
    # but for prototype we fetch all or just last 12)
    # logic to determine current service year:
    today = timezone.localtime().date()
    # If today is Sept-Dec, service year starts this year. 
    # If Jan-Aug, service year started last year.
    if today.month >= 9:
        sy_start = today.year
    else:
        sy_start = today.year - 1
        
    from .utils import generate_s21_pdf
    return generate_s21_pdf(publisher, service_year_start=sy_start)

@login_required
def report_edit_view(request, publisher_id, year, month):
    publisher = get_object_or_404(Publisher, id=publisher_id)
    
    # Permission Check
    has_access = False
    if request.user.is_superuser:
        has_access = True
    elif request.user.role == User.Role.CONG_ADMIN and request.user.congregation == publisher.group.congregation:
        has_access = True
    elif publisher.group in request.user.managed_groups.all():
        has_access = True
        
    if not has_access:
        return render(request, '403.html', status=403)

    import datetime
    try:
        target_date = datetime.date(year, month, 1)
    except ValueError:
        return render(request, '404.html') # Invalid date
    
    # Get or create report
    report, created = MonthlyReport.objects.get_or_create(
        publisher=publisher,
        month=target_date,
        defaults={'status': MonthlyReport.Status.PENDING}
    )

    if request.method == 'POST':
        from .forms import MonthlyReportForm
        form = MonthlyReportForm(request.POST, instance=report)
        if form.is_valid():
            saved_report = form.save(commit=False)
            # If admin edits, we can auto-approve or keep as is. Usually admin edit = approved.
            saved_report.status = MonthlyReport.Status.APPROVED 
            
            # Determine who submitted/edited
            if request.user.role == User.Role.CONG_ADMIN:
                saved_report.submitted_by = MonthlyReport.SubmissionSource.ADMIN
            elif request.user.role == User.Role.GROUP_ADMIN:
                saved_report.submitted_by = MonthlyReport.SubmissionSource.SUBADMIN
            
            saved_report.save()
            messages.success(request, f'Informe de {target_date.strftime("%b %Y")} actualizado.')
            return redirect('reports:dashboard')
    else:
        from .forms import MonthlyReportForm
        form = MonthlyReportForm(instance=report)

    return render(request, 'reports/report_form_admin.html', {
        'form': form, 
        'publisher': publisher,
        'date': target_date
    })

@login_required
def bulk_report_view(request, group_id, year=None, month=None):
    from datetime import date
    from django.db import transaction
    today = timezone.localtime().date()
    
    # Default to current month/year if not provided
    if not year or not month:
        target_date = today.replace(day=1)
    else:
        try:
            target_date = date(year, month, 1)
        except ValueError:
            return render(request, '404.html')

    group = get_object_or_404(Group, id=group_id)
    
    # Permission Check
    if not (request.user.is_superuser or 
            (request.user.role == User.Role.CONG_ADMIN and request.user.congregation == group.congregation) or
            group in request.user.managed_groups.all()):
        return render(request, '403.html', status=403)

    publishers = group.publishers.filter(active=True).order_by('last_name')
    
    if request.method == 'POST':
        count_updated = 0
        with transaction.atomic():
            for pub in publishers:
                prefix = f'report_{pub.id}_'
                
                participation = request.POST.get(f'{prefix}participation') == 'on'
                aux_pioneer = request.POST.get(f'{prefix}aux_pioneer') == 'on'
                
                hours_str = request.POST.get(f'{prefix}hours', '').strip()
                hours = int(hours_str) if hours_str.isdigit() else 0
                
                studies_str = request.POST.get(f'{prefix}studies', '').strip()
                studies = int(studies_str) if studies_str.isdigit() else 0
                
                remarks = request.POST.get(f'{prefix}remarks', '').strip()
                
                # Check validation rules for clearing flags if not eligible?
                # For now, trust admin input or rely on model validation if we called full_clean()
                
                should_save = participation or aux_pioneer or hours > 0 or studies > 0 or remarks
                
                if should_save:
                    report, created = MonthlyReport.objects.get_or_create(
                        publisher=pub,
                        month=target_date,
                        defaults={'status': MonthlyReport.Status.APPROVED}
                    )
                    
                    report.participation = participation
                    report.auxiliary_pioneer = aux_pioneer
                    report.hours = hours
                    report.bible_studies = studies
                    report.remarks = remarks
                    report.status = MonthlyReport.Status.APPROVED
                    
                    if request.user.role == User.Role.CONG_ADMIN:
                        report.submitted_by = MonthlyReport.SubmissionSource.ADMIN
                    else:
                        report.submitted_by = MonthlyReport.SubmissionSource.SUBADMIN
                        
                    report.save()
                    count_updated += 1
                
        messages.success(request, f'Se actualizaron {count_updated} informes para {target_date.strftime("%B %Y")}.')
        return redirect('reports:dashboard')

    # Prepare data for template
    reports_map = {}
    current_reports = MonthlyReport.objects.filter(
        publisher__group=group, 
        month=target_date
    )
    for r in current_reports:
        reports_map[r.publisher_id] = r
        
    # CHECK FOR SCANNED DATA IN SESSION
    session_key = f'scan_data_{group_id}'
    scanned_data = request.session.pop(session_key, None) # Pop to clear after use
    scan_map = {item['id']: item for item in scanned_data} if scanned_data else {}
    scan_message = f"Se han pre-cargado datos para {len(scanned_data)} publicadores desde el escaneo." if scanned_data else None

    rows = []
    for pub in publishers:
        report = reports_map.get(pub.id)
        scanned = scan_map.get(pub.id)
        
        # Logic: If report exists, use DB data. 
        # If DB is empty/pending but we have scan data, use scan data as "temporary" object for display
        
        display_report = report
        
        if not report and scanned:
            # Create a dummy object (not saved) for the template to render
            display_report = MonthlyReport(
                publisher=pub,
                month=target_date, # Add month to avoid error if template uses it
                hours=scanned.get('hours', 0),
                bible_studies=scanned.get('studies', 0),
                participation=scanned.get('participation', False),
                auxiliary_pioneer=scanned.get('aux_pioneer', False),
                remarks=scanned.get('remarks', '')
            )
        
        rows.append({
            'publisher': pub,
            'report': display_report
        })
        
    return render(request, 'reports/bulk_report_form.html', {
        'group': group,
        'rows': rows,
        'target_date': target_date,
        'scan_message': scan_message
    })
