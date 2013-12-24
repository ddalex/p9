# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UF'
        db.create_table(u'recv_uf', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('remoteIP', self.gf('django.db.models.fields.GenericIPAddressField')(max_length=39)),
            ('useragent', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal(u'recv', ['UF'])


    def backwards(self, orm):
        # Deleting model 'UF'
        db.delete_table(u'recv_uf')


    models = {
        u'recv.uf': {
            'Meta': {'object_name': 'UF'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'remoteIP': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39'}),
            'useragent': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        }
    }

    complete_apps = ['recv']