
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from organization.models import Publisher
from reports.models import MonthlyReport
from .forms import PublicReportForm
from django.contrib import messages

def publisher_report_view(request, publisher_uuid):
    """
    View for publishers to submit their report via a unique link.
    Accessible without login, validated by UUID.
    Shows only the current month's report.
    """
    publisher = get_object_or_404(Publisher, uuid=publisher_uuid)
    
    # Determine the current month (simplification: using current calendar month)
    # In a real app, this might need logic to handle end-of-month reporting for previous month
    # But user requirement says "SOLO puede ingresar datos del mes actual"
    today = timezone.localtime().date()
    current_month_date = today.replace(day=1)
    
    # Check if report already exists
    report, created = MonthlyReport.objects.get_or_create(
        publisher=publisher,
        month=current_month_date
    )
    
    if report.status == MonthlyReport.Status.APPROVED:
        return render(request, 'public_access/already_submitted.html', {
            'publisher': publisher,
            'message': 'Su informe ya ha sido confirmado por el administrador.'
        })

    if request.method == 'POST':
        form = PublicReportForm(request.POST, instance=report)
        if form.is_valid():
            report = form.save(commit=False)
            report.status = MonthlyReport.Status.SUBMITTED
            report.save()
            return render(request, 'public_access/success.html', {'publisher': publisher})
    else:
        form = PublicReportForm(instance=report)

    return render(request, 'public_access/report_form.html', {
        'form': form, 
        'publisher': publisher,
        'month': current_month_date.strftime('%B %Y') # Month name will be localized if configured
    })
