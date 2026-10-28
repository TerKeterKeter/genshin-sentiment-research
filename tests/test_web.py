"""Browser workflow with SYNTHETIC comments/revenue and a mocked YouTube API."""
import io
import json
import os
import re
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from genshin_research.web import create_app
from genshin_research.workbench import SETTINGS,csv_text


class FakeAPI:
    def official_channel_id(self): return 'SYNTHETIC_OFFICIAL'
    def metadata(self,video_id):
        return dict(video_id=video_id,title='SYNTHETIC TEST TITLE',channel_id='SYNTHETIC_OFFICIAL',
                    video_published_at_utc='2026-03-01T00:00:00Z',duration='PT15S')
    def __call__(self,resource,params):
        return {'items':[{'snippet':{'topLevelComment':{'id':'SYNTHETIC_'+str(i),'snippet':{
            'textDisplay':text,'publishedAt':'2026-03-01T01:00:00Z','updatedAt':'2026-03-01T01:00:00Z','likeCount':4}}}}
            for i,text in enumerate(['I absolutely love this wonderful character design and the amazing beautiful colors!',
                                    'I really hate this terrible awful character design and the disappointing colors.'])]}


class FakeModel:
    def tokenizer(self,text,**kwargs): return {'input_ids':[1,2,3]}
    def __call__(self,texts,**kwargs):
        return [dict(label='negative' if 'hate' in text else 'positive',score=.9) for text in texts]


class WebTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.old=os.getcwd();os.chdir(self.temporary.name)
        self.app=create_app();self.app.testing=True
        self.client=self.app.test_client()
        self.store=self.app.extensions['store']
        self.token=re.search(r'name="csrf-token" content="([^"]+)"',self.client.get('/').text).group(1)
        self.store.save_json('settings.json',{**SETTINGS,'dry_run':False,'metadata_allowed':True,
            'collection_allowed':True,'derived_analysis_allowed':True,'external_join_allowed':True,
            'policy_review_status':'documented','policy_reviewed_at':'2026-10-26','evidence_reference':'SYNTHETIC TEST ONLY'})
        self.app.config['YOUTUBE_API_KEY']='SYNTHETIC_KEY_ONLY'

    def tearDown(self):
        # No test may leave a worker writing into a deleted temporary project.
        deadline=time.time()+15
        while self.app.extensions['jobs'].busy() and time.time()<deadline: time.sleep(.02)
        os.chdir(self.old);self.temporary.cleanup()

    def post(self,path,data=None,**kwargs):
        return self.client.post(path,data={'csrf':self.token,**(data or {})},**kwargs)

    def wait_job(self,response):
        self.assertEqual(response.status_code,302,response.text)
        path=response.headers['Location']
        self.assertIn('/jobs/',path)
        deadline=time.time()+20
        while time.time()<deadline:
            result=self.client.get(path+'/status').json
            if result['status']!='running':
                self.assertEqual(result['status'],'done',result)
                return result
            time.sleep(.02)
        self.fail('Background synthetic job did not finish')

    def add(self):
        response=self.post('/events',dict(link='https://youtube.com/shorts/AbCdEfGhI12',character_name='SYNTHETIC'))
        self.assertEqual(response.status_code,302)
        return self.store.events()[0]['event_id']

    def test_csrf_default_modes_and_key_never_persisted(self):
        self.assertEqual(self.client.post('/events',data={'link':'anything'}).status_code,400)
        for route in ['/','/events','/datasets','/settings','/revenue','/coverage','/guide']:
            response=self.client.get(route)
            self.assertEqual(response.status_code,200)
            self.assertNotIn('SYNTHETIC_KEY_ONLY',response.text)
        self.post('/settings',dict(dry_run='on',retention_days='30',api_key='SYNTHETIC_PRIVATE_NEW'))
        self.assertTrue(self.store.settings()['dry_run'])
        self.assertNotIn('SYNTHETIC_PRIVATE_NEW',(self.store.root/'settings.json').read_text())

    def test_missing_settings_explain_fields_and_retry_without_enabling_other_scopes(self):
        event_id = self.add()
        self.store.save_json('settings.json', {
            **SETTINGS, 'dry_run': False, 'metadata_allowed': True,
        })
        with patch('genshin_research.web.YouTube', return_value=FakeAPI()) as api:
            response = self.post('/events/' + event_id + '/metadata')
            self.assertEqual(response.status_code, 400)
            self.assertIn('Tanggal tinjauan kebijakan', response.text)
            self.assertIn('Referensi dasar penggunaan proyek', response.text)
            self.assertIn('href="/settings"', response.text)
            self.assertIn('href="/guide#pengaturan"', response.text)
            self.assertNotIn('Document the requested', response.text)
            # A valid 30-day retention must not be reported as a cause of this error.
            self.assertNotIn('bilangan bulat 1–30', response.text)
            api.assert_not_called()
            self.assertFalse(self.app.extensions['jobs'].busy())
            self.assertEqual(self.store.settings()['policy_reviewed_at'], '')

            saved = self.post('/settings', dict(
                metadata_allowed='on', retention_days='30',
                policy_reviewed_at='2026-10-28', evidence_reference='SYNTHETIC REVIEW ONLY',
            ))
            self.assertEqual(saved.status_code, 302)
            self.wait_job(self.post('/events/' + event_id + '/metadata'))
            self.assertTrue(self.store.event(event_id)['api_verified_at_utc'])
            self.assertFalse(self.store.settings()['collection_allowed'])

            api.reset_mock()
            blocked = self.post('/datasets/collect', {'mode': 'all'})
            self.assertEqual(blocked.status_code, 400)
            self.assertIn('Kumpulkan komentar utama', blocked.text)
            self.assertNotIn('Isi &#34;Tanggal tinjauan kebijakan&#34;', blocked.text)
            api.assert_not_called()

    def test_offline_and_invalid_retention_report_actual_causes_without_network(self):
        event_id = self.add()
        self.store.save_json('settings.json', {
            **self.store.settings(), 'dry_run': True, 'retention_days': 0,
        })
        with patch('genshin_research.web.YouTube') as api:
            response = self.post('/events/' + event_id + '/metadata')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Offline / dry-run masih aktif', response.text)
        self.assertIn('Masa simpan data / retensi (hari)', response.text)
        self.assertIn('bukan jumlah hari komentar', response.text)
        self.assertNotIn('Isi &#34;Tanggal tinjauan kebijakan&#34;', response.text)
        self.assertNotIn('Operasi &#34;Baca metadata YouTube&#34; belum', response.text)
        api.assert_not_called()

    def test_in_app_guide_explains_first_collection_and_preserves_offline_mode(self):
        self.store.save_json('settings.json', SETTINGS)
        page = self.client.get('/guide')
        self.assertEqual(page.status_code, 200)
        self.assertIn('id="pengaturan"', page.text)
        self.assertIn('Semua event included (boleh untuk uji kecil)', page.text)
        self.assertIn('bukan 100 komentar total', page.text)
        self.assertIn('href="/events"', page.text)
        self.assertIn('href="/settings"', page.text)
        self.assertTrue(self.store.settings()['dry_run'])

    def test_full_crud_collection_nlp_annotation_and_analysis(self):
        event_id=self.add()
        fields=dict(character_name='SYNTHETIC',announcement_source_url='https://example.invalid/SYNTHETIC',
            initial_announcement_at_utc='2026-03-01T00:00:00Z',content_type='verified_initial_drip_short',
            inclusion_status='included',verification_notes='SYNTHETIC HUMAN REVIEW',exclusion_reason='')
        self.assertEqual(self.post('/events/'+event_id,fields).status_code,400) # API verification required.
        with patch('genshin_research.web.YouTube',return_value=FakeAPI()):
            self.wait_job(self.post('/events/'+event_id+'/metadata'))
            self.assertEqual(self.post('/events/'+event_id,fields).status_code,302)
            self.wait_job(self.post('/datasets/collect',{'mode':'all'}))
        run_id=self.store.runs()[0]['run_id']
        self.assertTrue(self.store.manifest(run_id)['collection_complete'])
        with patch('genshin_research.sentiment.classifier',return_value=FakeModel()):
            self.wait_job(self.post('/datasets/'+run_id+'/nlp'))
        self.assertTrue(self.store.manifest(run_id)['nlp_complete'])
        self.assertEqual(self.client.get('/datasets/'+run_id).status_code,200)
        self.assertEqual(self.post('/datasets/'+run_id+'/annotations').status_code,302)
        annotations=self.store.run_path(run_id)/'annotations.csv'
        self.assertTrue(annotations.exists())
        from genshin_research.core import read_csv
        rows=read_csv(annotations)
        self.assertEqual(len(rows),2)
        for row in rows:
            row.update(annotator_1='negative' if 'hate' in row['text_display'] else 'positive',
                       annotator_2='negative' if 'hate' in row['text_display'] else 'positive',
                       adjudicated_label='negative' if 'hate' in row['text_display'] else 'positive')
        upload=io.BytesIO(csv_text(rows).encode())
        self.assertEqual(self.post('/datasets/'+run_id+'/annotations',{'file':(upload,'annotations.csv')}).status_code,302)
        self.assertEqual(self.post('/datasets/'+run_id+'/evaluate').status_code,302)
        self.wait_job(self.post('/datasets/'+run_id+'/analyze'))
        analysis=json.loads((self.store.run_path(run_id)/'analysis.json').read_text())
        self.assertEqual(analysis['actual_pair_count'],0)
        self.assertEqual(self.client.get('/datasets/'+run_id).status_code,200)
        self.wait_job(self.post('/datasets/'+run_id+'/forecast'))
        self.assertEqual(json.loads((self.store.run_path(run_id)/'forecast.json').read_text())['status'],'blocked')
        self.assertEqual(self.post('/events/'+event_id+'/delete',{'confirm':'yes'}).status_code,302)
        self.assertFalse(self.store.events())
        self.assertFalse(self.store.run_path(run_id).exists())

    def test_partial_or_expired_runs_are_not_analyzable(self):
        run_id=self.store.new_run([],synthetic=True)
        self.assertEqual(self.post('/datasets/'+run_id+'/nlp').status_code,400)
        manifest=self.store.manifest(run_id)
        manifest.update(collection_complete=True,expires_at='2000-01-01T00:00:00Z')
        self.store.save_json(f'runs/{run_id}/manifest.json',manifest)
        self.client.get('/')
        self.assertFalse(self.store.run_path(run_id).exists())

    def test_link_edit_invalidates_manual_inclusion_and_metadata(self):
        event_id=self.add()
        self.store.update_event(event_id,dict(inclusion_status='included',channel_id='SYNTHETIC_OFFICIAL',
            api_verified_at_utc='2026-10-26T00:00:00Z',api_expires_at_utc='2099-01-01T00:00:00Z',
            official_channel_match='true',content_type='verified_initial_drip_short'))
        response=self.post('/events/'+event_id,dict(video_url='https://youtube.com/shorts/-ABCDEFGHIJ',
            character_name='SYNTHETIC',inclusion_status='included',content_type='verified_initial_drip_short'))
        self.assertEqual(response.status_code,302)
        row=self.store.event(event_id)
        self.assertEqual(row['inclusion_status'],'pending')
        self.assertEqual(row['channel_id'],'')
        self.assertEqual(row['video_id'],'-ABCDEFGHIJ')

    def test_event_without_matching_short_can_be_recorded_manually(self):
        response=self.post('/events',dict(link='',character_name='SYNTHETIC NO SHORT'))
        self.assertEqual(response.status_code,302)
        event_id=self.store.events()[0]['event_id']
        response=self.post('/events/'+event_id,dict(character_name='SYNTHETIC NO SHORT',
            inclusion_status='no_matching_short',exclusion_reason='SYNTHETIC SEARCH FOUND NO SHORT',
            verification_notes='SYNTHETIC REVIEW'))
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.store.event(event_id)['inclusion_status'],'no_matching_short')
