from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TimeLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sign_in_time = models.DateTimeField(default=timezone.now)
    sign_out_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-sign_in_time']

    def __str__(self):
        return f"{self.user.username} - {self.sign_in_time.strftime('%Y-%m-%d %H:%M')}"

    @property
    def duration(self):
        if self.sign_out_time:
            delta = self.sign_out_time - self.sign_in_time
            hours, remainder = divmod(delta.total_seconds(), 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{int(hours)}h {int(minutes)}m"
        return "Active"

    def sign_out(self):
        if self.is_active:
            self.sign_out_time = timezone.now()
            self.is_active = False
            self.save()