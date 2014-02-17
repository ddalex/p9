# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Client'
        db.create_table(u'sign_client', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('externid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'sign', ['Client'])

        # Adding model 'Message'
        db.create_table(u'sign_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sign.Client'])),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='recipient', to=orm['sign.Client'])),
            ('msgtype', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('content', self.gf('django.db.models.fields.CharField')(max_length=4096)),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'sign', ['Message'])


    def backwards(self, orm):
        # Deleting model 'Client'
        db.delete_table(u'sign_client')

        # Deleting model 'Message'
        db.delete_table(u'sign_message')


    models = {
        u'sign.client': {
            'Meta': {'object_name': 'Client'},
            'externid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        u'sign.message': {
            'Meta': {'object_name': 'Message'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sign.Client']"}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '4096'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'msgtype': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recipient'", 'to': u"orm['sign.Client']"})
        }
    }

    complete_apps = ['sign']