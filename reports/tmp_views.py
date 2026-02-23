from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import MonthlyReport
from organization.models import Publisher
from .forms import MonthlyReportForm
from accounts.models import User
import datetime

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

    target_date = datetime.date(year, month, 1)
    
    # Get or create report
    report, created = MonthlyReport.objects.get_or_create(
        publisher=publisher,
        month=target_date,
        defaults={'status': MonthlyReport.Status.PENDING}
    )

    if request.method == 'POST':
        form = MonthlyReportForm(request.POST, instance=report)
        if form.is_valid():
            saved_report = form.save(commit=False)
            saved_report.status = MonthlyReport.Status.APPROVED # Admin edit implies approval
            
            # Determine who submitted/edited
            if request.user.role == User.Role.CONG_ADMIN:
                saved_report.submitted_by = MonthlyReport.SubmissionSource.ADMIN
            elif request.user.role == User.Role.GROUP_ADMIN:
                saved_report.submitted_by = MonthlyReport.SubmissionSource.SUBADMIN # Or keep as Publisher if just fixing typo?
                # Requirement says "submitted_by admin/subadmin/publisher". Let's stick to ADMIN/SUBADMIN.
                saved_report.submitted_by = MonthlyReport.SubmissionSource.SUBADMIN
            
            saved_report.save()
            messages.success(request, f'Informe de {target_date.strftime("%b %Y")} actualizado.')
            return redirect('reports:dashboard')
    else:
        form = MonthlyReportForm(instance=report)

    return render(request, 'reports/report_form_admin.html', {
        'form': form, 
        'publisher': publisher,
        'date': target_date
    })
