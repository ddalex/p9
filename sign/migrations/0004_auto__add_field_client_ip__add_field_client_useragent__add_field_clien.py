# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Client.ip'
        db.add_column(u'sign_client', 'ip',
                      self.gf('django.db.models.fields.GenericIPAddressField')(default='0.0.0.0', max_length=39, blank=True),
                      keep_default=False)

        # Adding field 'Client.useragent'
        db.add_column(u'sign_client', 'useragent',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True),
                      keep_default=False)

        # Adding field 'Client.created'
        db.add_column(u'sign_client', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, default=datetime.datetime(2014, 4, 30, 0, 0), blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Client.ip'
        db.delete_column(u'sign_client', 'ip')

        # Deleting field 'Client.useragent'
        db.delete_column(u'sign_client', 'useragent')

        # Deleting field 'Client.created'
        db.delete_column(u'sign_client', 'created')


    models = {
        u'sign.channel': {
            'Meta': {'object_name': 'Channel'},
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sign.Client']"}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'sign.channelrelay': {
            'Meta': {'object_name': 'ChannelRelay'},
            'channel': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sign.Channel']"}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sign.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        },
        u'sign.client': {
            'Meta': {'object_name': 'Client'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'externid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.GenericIPAddressField', [], {'max_length': '39', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'useragent': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'})
        },
        u'sign.clientlog': {
            'Meta': {'object_name': 'ClientLog'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sign.Client']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
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