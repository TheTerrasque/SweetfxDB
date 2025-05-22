# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DownloadCategory'
        db.create_table('downloads_downloadcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('sortweight', self.gf('django.db.models.fields.IntegerField')(default=100)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('downloads', ['DownloadCategory'])

        # Adding model 'DownloadFile'
        db.create_table('downloads_downloadfile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dlfile', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['downloads.DownloadCategory'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('sortweight', self.gf('django.db.models.fields.IntegerField')(default=100)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('downloads', ['DownloadFile'])


    def backwards(self, orm):
        # Deleting model 'DownloadCategory'
        db.delete_table('downloads_downloadcategory')

        # Deleting model 'DownloadFile'
        db.delete_table('downloads_downloadfile')


    models = {
        'downloads.downloadcategory': {
            'Meta': {'ordering': "['sortweight', '-id']", 'object_name': 'DownloadCategory'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'sortweight': ('django.db.models.fields.IntegerField', [], {'default': '100'})
        },
        'downloads.downloadfile': {
            'Meta': {'ordering': "['sortweight', '-id']", 'object_name': 'DownloadFile'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['downloads.DownloadCategory']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'dlfile': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sortweight': ('django.db.models.fields.IntegerField', [], {'default': '100'})
        }
    }

    complete_apps = ['downloads']