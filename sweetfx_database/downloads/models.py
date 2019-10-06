from django.db import models

# Create your models here.

class DownloadCategory(models.Model):
    name = models.CharField(max_length=50)
    sortweight = models.IntegerField(default=100)
    description = models.TextField(blank=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["sortweight", "-id"]
        
class DownloadFile(models.Model):
    dlfile = models.FileField(upload_to="downloads")
    category = models.ForeignKey(DownloadCategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    
    added = models.DateTimeField(auto_now_add=True)
    
    sortweight = models.IntegerField(default=100)
    description = models.TextField(blank=True)
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ["sortweight", "-id"]
