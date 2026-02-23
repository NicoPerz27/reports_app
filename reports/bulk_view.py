@login_required
def bulk_report_view(request, group_id, year=None, month=None):
    from datetime import date
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
        return render(request, '403.html')

    publishers = group.publishers.filter(active=True).order_by('last_name')
    
    if request.method == 'POST':
        # Manual processing of form data to handle grid input
        # Inputs name format: "report_{pub_id}_{field}"
        # e.g. "report_5_hours", "report_5_participation"
        
        count_updated = 0
        with transaction.atomic():
            for pub in publishers:
                prefix = f'report_{pub.id}_'
                
                # Check if this row was touched? 
                # Actually, we should probably update/create for all active publishers 
                # if data is present.
                
                participation = request.POST.get(f'{prefix}participation') == 'on'
                aux_pioneer = request.POST.get(f'{prefix}aux_pioneer') == 'on'
                
                hours_str = request.POST.get(f'{prefix}hours', '').strip()
                hours = int(hours_str) if hours_str.isdigit() else 0
                
                studies_str = request.POST.get(f'{prefix}studies', '').strip()
                studies = int(studies_str) if studies_str.isdigit() else 0
                
                remarks = request.POST.get(f'{prefix}remarks', '').strip()
                
                # Validation logic (simplified for bulk)
                # If participation is checked OR hours > 0 OR studies > 0, we create a report
                # BUT: If user explicitly unchecks everything, we might need to delete or zero out?
                # Let's assume we update existing or create new.
                
                should_save = participation or aux_pioneer or hours > 0 or studies > 0 or remarks
                
                if should_save:
                    report, created = MonthlyReport.objects.get_or_create(
                        publisher=pub,
                        month=target_date,
                        defaults={'status': MonthlyReport.Status.APPROVED} # Auto-approve bulk admin entry
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
    # We need to pre-fill existing reports
    reports_map = {}
    current_reports = MonthlyReport.objects.filter(
        publisher__group=group, 
        month=target_date
    )
    for r in current_reports:
        reports_map[r.publisher_id] = r

    # Check for AI Scan Data in Session
    scan_data = request.session.pop(f'scan_data_{group_id}', None)
    scan_message = None
    
    scan_map_id = {}
    scan_map_name = {}

    if scan_data:
        scan_message = f"Se han pre-cargado datos para {len(scan_data)} publicadores desde el escaneo."
        # Map scan data to publisher IDs AND Names
        for item in scan_data:
            if 'id' in item:
                scan_map_id[item['id']] = item
            if 'name' in item and item['name']:
                # Normalize name for matching: "First Last" -> "first last"
                scan_map_name[item['name'].lower().strip()] = item
        
    # Combine publishers with their report data
    rows = []
    for pub in publishers:
        report = reports_map.get(pub.id)
        
        # If no DB report, check if we have scan data
        if not report and scan_data:
            # TRY 1: Match by ID
            data = scan_map_id.get(pub.id)
            
            # TRY 2: Match by Name (Fallback if ID fails or user prefers)
            if not data:
                full_name = f"{pub.first_name} {pub.last_name}".lower().strip()
                data = scan_map_name.get(full_name)
            
            # TRY 3: Fuzzy Name Match (Simple containment) if exact fail
            if not data:
                full_name = f"{pub.first_name} {pub.last_name}".lower().strip()
                for key_name, item in scan_map_name.items():
                    if key_name in full_name or full_name in key_name:
                        # Very simple fuzzy check
                        data = item
                        break

            if data:
                # Create a temporary (unsaved) report object for the template
                report = MonthlyReport(
                    publisher=pub,
                    month=target_date,
                    participation=data.get('participation', False),
                    hours=data.get('hours', 0),
                    bible_studies=data.get('studies', 0),
                    auxiliary_pioneer=data.get('aux_pioneer', False),
                    remarks=data.get('remarks', '')
                )
        
        rows.append({
            'publisher': pub,
            'report': report
        })
        
    return render(request, 'reports/bulk_report_form.html', {
        'group': group,
        'rows': rows,
        'target_date': target_date,
        'scan_message': scan_message
    })
