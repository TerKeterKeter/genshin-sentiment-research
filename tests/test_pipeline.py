"""Entirely SYNTHETIC research fixtures. No actual comments or revenue."""
import unittest
from datetime import datetime,timezone
from genshin_research.collection import collect_event,eligibility
from genshin_research.analysis import aggregate,pair_months,forecast,next_month,validate_revenue
from genshin_research.sentiment import normalize,annotation_sample,evaluate,infer

START='2026-03-01T00:00:00Z'
EVENT=dict(event_id='SYNTHETIC',video_id='SYNTHETIC00',video_published_at_utc=START)


def comment(cid,published=START,updated=START):
    return {'snippet':{'topLevelComment':{'id':cid,'snippet':{'textDisplay':'SYNTHETIC TEST TEXT',
        'publishedAt':published,'updatedAt':updated,'likeCount':99}}}}


def revenue(month='2026-04',value='100'):
    return dict(month=month,revenue_usd=value,platform_scope='SYNTHETIC mobile',region_scope='TEST',
        cn_android_included='false',cn_android_multiplier='',source_url='https://example.invalid/SYNTHETIC',
        retrieved_at='2026-10-26',revision_notes='SYNTHETIC TEST VALUE',available_at_utc=next_month(month)+'-01T00:00:00Z')


class PipelineTests(unittest.TestCase):
    def test_pagination_dedup_boundary_edits_and_no_authors(self):
        calls=[]
        def api(resource,params):
            calls.append(params)
            if 'pageToken' not in params:
                return {'items':[comment('a'),comment('edited',updated='2026-03-04T00:00:00Z')],'nextPageToken':'two'}
            return {'items':[comment('a'),comment('cutoff',published='2026-03-04T00:00:00Z',updated='2026-03-04T00:00:00Z')]}
        rows,status=collect_event(api,EVENT)
        self.assertTrue(status['pagination_complete'])
        self.assertEqual(status['duplicate_ids'],1)
        self.assertEqual(len(rows),3)
        self.assertEqual(rows[1]['exclusion_reason'],'edited_at_or_after_cutoff')
        self.assertEqual(rows[2]['exclusion_reason'],'outside_window')
        self.assertEqual(calls[0]['maxResults'],100)
        self.assertEqual(calls[0]['order'],'time')
        self.assertEqual(calls[0]['textFormat'],'plainText')
        self.assertNotIn('author',str(rows))
        self.assertEqual(eligibility(START,START,START)[0],'eligible')

    def test_partial_capture_is_saved_but_not_complete(self):
        checkpoints=[]
        def api(resource,params):
            if 'pageToken' in params: raise RuntimeError('SYNTHETIC INTERRUPTED')
            return {'items':[comment('a')],'nextPageToken':'next'}
        rows,status=collect_event(api,EVENT,checkpoint=lambda r,s:checkpoints.append((len(r),dict(s))))
        self.assertEqual(len(rows),1)
        self.assertFalse(status['pagination_complete'])
        self.assertEqual(checkpoints[-1][1]['error'],'SYNTHETIC INTERRUPTED')

    def test_month_end_no_event_vs_neutral_and_lag(self):
        event={**EVENT,'video_published_at_utc':'2026-03-31T00:00:00Z'}
        comments=[dict(comment_id='a',event_id='SYNTHETIC',eligibility_status='eligible',sentiment='neutral')]
        monthly=aggregate([event],comments)
        self.assertEqual(monthly[0]['month'],'2026-04')
        self.assertEqual(monthly[0]['net_sentiment'],0)
        self.assertIsNone(aggregate([event],[])[0]['net_sentiment'])
        pairs,coverage=pair_months(monthly,[revenue('2026-05')],datetime(2026,10,26,tzinfo=timezone.utc))
        self.assertEqual(pairs[0]['revenue_month'],'2026-05')
        self.assertEqual(coverage[0]['status'],'paired')

    def test_revenue_validation_and_unfinished_month(self):
        for rows in [[revenue(),revenue()], [revenue(),{**revenue('2026-05'),'region_scope':'OTHER'}],
                     [{**revenue(),'revenue_usd':'nan'}],[{**revenue(),'available_at_utc':'2026-04-01T00:00:00Z'}]]:
            with self.assertRaises(ValueError): validate_revenue(rows)
        pairs,coverage=pair_months([dict(month='2026-09',net_sentiment=.5)],[revenue('2026-10')],datetime(2026,10,26,tzinfo=timezone.utc))
        self.assertEqual(pairs,[])
        self.assertEqual(coverage[0]['status'],'revenue_month_not_complete')

    def test_annotation_is_blind_and_order_reproducible(self):
        rows=[dict(comment_id=str(i),event_id='SYNTHETIC',published_at_utc=f'2026-03-0{1+i%3}T01:00:00Z',
                   eligibility_status='eligible',text_display='SYNTHETIC',sentiment='positive') for i in range(30)]
        sample=annotation_sample(rows,[EVENT],n=9)
        self.assertEqual(sample,annotation_sample(list(reversed(rows)),[EVENT],n=9))
        self.assertEqual({r['interval_24h'] for r in sample},{0,1,2})
        self.assertNotIn('sentiment',sample[0])
        self.assertEqual(normalize(' not   bad 😄\n'),'not bad 😄')

    def test_gold_is_required_and_evaluation_has_real_counts(self):
        predictions=[dict(comment_id=str(i),sentiment=label) for i,label in enumerate(['positive','negative','neutral'])]
        annotations=[dict(comment_id=r['comment_id'],adjudicated_label=r['sentiment'],annotator_1=r['sentiment'],annotator_2=r['sentiment']) for r in predictions]
        result=evaluate(annotations,predictions)
        self.assertEqual(result['macro_f1'],1)
        self.assertEqual(result['cohen_kappa'],1)
        self.assertEqual(result['n'],3)
        with self.assertRaises(ValueError): evaluate([dict(comment_id='0',adjudicated_label='')],predictions)

    def test_no_eligible_comments_does_not_load_model(self):
        rows=[dict(comment_id='x',eligibility_status='excluded')]
        self.assertEqual(infer(rows),rows)

    def test_forecast_blocks_small_gapped_or_unavailable_data(self):
        self.assertEqual(forecast([],[],discovery_complete=False)['status'],'blocked')
        pairs=[]
        for i in range(1,9):
            month=f'2026-{i:02d}'
            pairs.append(dict(month=month,net_sentiment=i/20,revenue_month=next_month(month),revenue_usd=100+i*5,
                              available_at_utc=next_month(next_month(month))+'-01T00:00:00Z'))
        monthly=[dict(month='2026-09',net_sentiment=.4)]
        result=forecast(monthly,pairs,datetime(2026,10,26,tzinfo=timezone.utc),True)
        self.assertEqual(result['status'],'experimental_projection')
        self.assertEqual(result['projection_kind'],'nowcast_bulan_berjalan')
        self.assertGreaterEqual(len(result['folds']),3)
        self.assertIn('naive_mae',result)
        self.assertTrue(all(r['n_train']>=4 for r in result['folds']))
        invalid=[{**r,'available_at_utc':''} for r in pairs]
        self.assertEqual(forecast(monthly,invalid,discovery_complete=True)['status'],'blocked')
        self.assertEqual(forecast(monthly,pairs[:-2]+pairs[-1:],discovery_complete=True)['status'],'blocked')

    def test_spearman_uses_monthly_pairs_and_known_order(self):
        from genshin_research.analysis import spearman
        pairs=[dict(net_sentiment=x,revenue_usd=y) for x,y in [(-.5,150),(0,100),(.5,50)]]
        result=spearman(pairs)
        self.assertEqual(result['actual_pair_count'],3)
        self.assertAlmostEqual(result['spearman_rho'],-1)
        self.assertEqual(spearman(pairs[:2])['status'],'insufficient_or_constant_data')
