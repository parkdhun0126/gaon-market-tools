import unittest
from dataclasses import dataclass
from decimal import Decimal as D
from gaon_market_tools import (
    MinuteBar, merge_observed_minute_buckets,
    merge_time_ordered_observed_minute_buckets, build_daily_session_display)

def bar(t,o,h,l,c,v):
    return MinuteBar(t,D(str(o)),D(str(h)),D(str(l)),D(str(c)),v)

@dataclass
class Budget:
    trading_date_kst: str
    starting_capital_krw: object
    session_net_pl_krw: object

class Tests(unittest.TestCase):
    def test_merge_observations(self):
        k='20261120103000'
        a=bar(k,100,103,99,102,5); b=bar(k,102,105,101,104,8)
        self.assertEqual(merge_observed_minute_buckets((a,),(b,)),(bar(k,100,105,99,104,13),))

    def test_no_interpolation(self):
        a=bar('20261120103000',100,100,100,100,1)
        b=bar('20261120103200',102,102,102,102,1)
        self.assertEqual(len(merge_observed_minute_buckets((a,),(b,))),2)

    def test_bounded_history(self):
        a=bar('20261120103000',100,100,100,100,1)
        b=bar('20261120103100',101,101,101,101,1)
        self.assertEqual(merge_observed_minute_buckets((a,),(b,),max_bars=1),(b,))

    def test_invalid_bar_rejected(self):
        bad=bar('20261120103000',100,90,110,100,1)
        with self.assertRaises(ValueError): merge_observed_minute_buckets((),(bad,))

    def test_time_ordered_earlier_broker_print(self):
        k='20261120103000'
        a=bar(k,102,103,102,103,2)
        earlier=bar(k,100,101,99,101,4)
        merged,bounds=merge_time_ordered_observed_minute_buckets(
            (a,),(earlier,),existing_bounds={k:('20261120103020','20261120103025')},
            observed_bounds=((k,'20261120103001','20261120103005'),))
        self.assertEqual(merged[0],bar(k,100,103,99,103,6))
        self.assertEqual(bounds[k],('20261120103001','20261120103025'))

    def test_same_day_pl(self):
        r=build_daily_session_display(trading_date='20261120',
            budget=Budget('20261120',1000000,'25000'))
        self.assertTrue(r.valid)
        self.assertEqual(r.rate_text,'+2.50%')

    def test_wrong_day_not_reported(self):
        r=build_daily_session_display(trading_date='20261120',
            budget=Budget('20261119',1000000,'25000'))
        self.assertFalse(r.valid)

    def test_oversized_seed_rejected(self):
        r=build_daily_session_display(trading_date='20261120',
            budget=Budget('20261120',20000000,'25000'))
        self.assertFalse(r.valid)

    def test_negative_pl(self):
        r=build_daily_session_display(trading_date='20261120',
            budget=Budget('20261120',1000000,-10000))
        self.assertEqual(r.rate_text,'-1.00%')

    def test_nan_rejected(self):
        r=build_daily_session_display(trading_date='20261120',
            budget=Budget('20261120',1000000,'NaN'))
        self.assertFalse(r.valid)

if __name__=='__main__': unittest.main()
