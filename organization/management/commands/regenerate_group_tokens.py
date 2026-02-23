from django.core.management.base import BaseCommand
from organization.models import Group
import uuid

class Command(BaseCommand):
    help = 'Regenerates invitation tokens for all groups to ensure uniqueness.'

    def handle(self, *args, **kwargs):
        groups = Group.objects.all()
        count = 0
        for group in groups:
            group.invitation_token = uuid.uuid4()
            group.save()
            count += 1
            self.stdout.write(f'Updated token for group: {group.name}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully regenerated tokens for {count} groups.'))
