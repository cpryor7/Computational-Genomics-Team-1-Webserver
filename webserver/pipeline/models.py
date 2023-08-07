from django.db import models
from django.urls import reverse

# Create your models here.
class get_Input(models.Model):
    """A typical class defining a model, derived from the Model class."""

    # Fields
    my_field_name = models.FileField(help_text='Enter field documentation')
    # …

    # Metadata
    class Meta:
        ordering = ['-my_field_name']

    # Methods
    def get_absolute_url(self):
        """Returns the URL to access a particular instance of MyModelName."""
        return reverse('model-detail-view', args=[str(self.id)])

    def __str__(self):
        """String for representing the MyModelName object (in Admin site etc.)."""
        return self.my_field_name