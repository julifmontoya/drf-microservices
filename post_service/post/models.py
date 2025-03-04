import uuid
from django.db import models

class Post(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    user_id = models.UUIDField()  # Storing only the user ID, not a direct FK
    title = models.CharField(max_length=100, blank=False)
    description = models.TextField(null=True, blank=True)
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']