# python -m unittest discover -s testing -p "test_*.py"
"""
TC07 – Boost systém (denní odměny a dočasné výhody)
====================================================

Tento soubor pokrývá kompletní testování validace boost systému:
typy boostů, hranice násobičů, časová razítka konce boostu,
kombinace boost polí a integrace s herním save payloadem.

Oblasti pokryté testy
---------------------
1.  boostType: povolené hodnoty (null, 'click', 'pps', 'all')
2.  boostType: zakázané hodnoty (neznámé řetězce, čísla, boolean)
3.  boostMult: hranice (1–10), odmítnutí mimo rozsah
4.  boostEnd: nula (žádný boost), budoucí timestamp, velký timestamp
5.  Kombinace boostType + boostMult + boostEnd – logicky konzistentní stavy
6.  Integrace do save payloadu – všechny kombinace boost polí
7.  Boost expirace – boostEnd v minulosti (validátor propustí, logika hry řeší)
8.  Spin wheel odměny – jednotlivé typy odměn mapované na boost konfiguraci
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from werkzeug.exceptions import BadRequest

from validation import validate_boost_type, validate_save_payload


# ---------------------------------------------------------------------------
# Pomocné funkce
# ---------------------------------------------------------------------------

# Referenční timestamp pro testovací běhy (2026-03-25T07:00:00 UTC v ms)
_NOW_MS = 1_743_063_600_000

# 30 minut v ms
_30_MIN_MS = 30 * 60 * 1000
# 20 minut v ms
_20_MIN_MS = 20 * 60 * 1000
# 15 minut v ms
_15_MIN_MS = 15 * 60 * 1000


def _boost_payload(boost_type=None, boost_mult=1, boost_end=0):
    """Vrátí kompletní save payload s danými boost hodnotami."""
    return {
        'pizzeriaName': 'Boost Lab',
        'money': 0,
        'totalEarned': 0,
        'clickValue': 1,
        'upgrades': {},
        'lastSave': _NOW_MS,
        'earnedAchievements': {},
        'totalClicks': 0,
        'streak': 1,
        'lastLoginDate': '2026-03-25',
        'prestigeLevel': 0,
        'lastSpinDate': '2026-03-25',
        'boostType': boost_type,
        'boostMult': boost_mult,
        'boostEnd': boost_end,
    }


# ---------------------------------------------------------------------------
# Testy validate_boost_type přímo
# ---------------------------------------------------------------------------

class TC07_BoostType_DirectValidation(unittest.TestCase):
    """Testy přímého volání validate_boost_type."""

    def test_none_is_accepted(self):
        """boostType = None signalizuje, že žádný boost není aktivní – musí projít."""
        result = validate_boost_type(None)
        self.assertIsNone(result)

    def test_click_is_accepted(self):
        """boostType = 'click' je platný typ boostu kliknutí."""
        result = validate_boost_type('click')
        self.assertEqual(result, 'click')

    def test_pps_is_accepted(self):
        """boostType = 'pps' je platný typ boostu pizz za sekundu."""
        result = validate_boost_type('pps')
        self.assertEqual(result, 'pps')

    def test_all_is_accepted(self):
        """boostType = 'all' je platný typ boostu pro klik i PPS zároveň."""
        result = validate_boost_type('all')
        self.assertEqual(result, 'all')

    def test_empty_string_is_rejected(self):
        """boostType = '' (prázdný řetězec) musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_boost_type('')
        self.assertIn('boostType must be null or one of', str(ctx.exception))

    def test_speed_is_rejected(self):
        """boostType = 'speed' není podporovaný typ boostu a musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_boost_type('speed')
        self.assertIn('boostType must be null or one of', str(ctx.exception))

    def test_money_is_rejected(self):
        """boostType = 'money' není podporovaný typ a musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_boost_type('money')
        self.assertIn('boostType must be null or one of', str(ctx.exception))

    def test_CLICK_uppercase_is_rejected(self):
        """boostType = 'CLICK' (velká písmena) musí být odmítnuto – porovnání je case-sensitive."""
        with self.assertRaises(BadRequest) as ctx:
            validate_boost_type('CLICK')
        self.assertIn('boostType must be null or one of', str(ctx.exception))

    def test_PPS_uppercase_is_rejected(self):
        """boostType = 'PPS' (velká písmena) musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_boost_type('PPS')
        self.assertIn('boostType must be null or one of', str(ctx.exception))

    def test_integer_is_rejected(self):
        """boostType = 1 (číslo) místo stringu musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_boost_type(1)
        self.assertIn('boostType must be null or one of', str(ctx.exception))

    def test_boolean_true_is_rejected(self):
        """boostType = True (boolean) musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_boost_type(True)
        self.assertIn('boostType must be null or one of', str(ctx.exception))

    def test_list_is_rejected(self):
        """boostType = ['click'] (seznam) musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_boost_type(['click'])
        self.assertIn('boostType must be null or one of', str(ctx.exception))


# ---------------------------------------------------------------------------
# Testy boostMult hranic (přes validate_save_payload)
# ---------------------------------------------------------------------------

class TC07_BoostMult_Boundaries(unittest.TestCase):
    """Testy hranic boostMult (minimum 1, maximum 10)."""

    def test_boost_mult_1_is_accepted(self):
        """boostMult = 1 je minimum – žádné zesílení nebo výchozí hodnota."""
        result = validate_save_payload(_boost_payload(None, 1, 0))
        self.assertEqual(result['boostMult'], 1)

    def test_boost_mult_2_click_boost_is_accepted(self):
        """boostMult = 2 s click boostem odpovídá 2× click odměně ze spin wheel."""
        result = validate_save_payload(_boost_payload('click', 2, _NOW_MS + _30_MIN_MS))
        self.assertEqual(result['boostMult'], 2)

    def test_boost_mult_3_pps_boost_is_accepted(self):
        """boostMult = 3 s pps boostem odpovídá odměně '3× PPS (15 min)' ze spin wheel."""
        result = validate_save_payload(_boost_payload('pps', 3, _NOW_MS + _15_MIN_MS))
        self.assertEqual(result['boostMult'], 3)

    def test_boost_mult_5_is_accepted(self):
        """boostMult = 5 je v povoleném rozsahu 1–10."""
        result = validate_save_payload(_boost_payload('all', 5, _NOW_MS + _20_MIN_MS))
        self.assertEqual(result['boostMult'], 5)

    def test_boost_mult_10_is_accepted(self):
        """boostMult = 10 je maximum – musí projít."""
        result = validate_save_payload(_boost_payload('click', 10, _NOW_MS + _30_MIN_MS))
        self.assertEqual(result['boostMult'], 10)

    def test_boost_mult_0_is_rejected(self):
        """boostMult = 0 je pod minimem 1 a musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(_boost_payload(None, 0, 0))
        self.assertIn('at least 1', str(ctx.exception))

    def test_boost_mult_negative_is_rejected(self):
        """boostMult = -1 je záporné a musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(_boost_payload(None, -1, 0))
        self.assertIn('at least 1', str(ctx.exception))

    def test_boost_mult_11_is_rejected(self):
        """boostMult = 11 překračuje maximum 10 a musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(_boost_payload('click', 11, _NOW_MS + _30_MIN_MS))
        self.assertIn('at most 10', str(ctx.exception))

    def test_boost_mult_100_is_rejected(self):
        """boostMult = 100 (extrémní hodnota) musí být odmítnuto."""
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(_boost_payload('all', 100, _NOW_MS + _30_MIN_MS))
        self.assertIn('at most 10', str(ctx.exception))


# ---------------------------------------------------------------------------
# Testy boostEnd časových razítek
# ---------------------------------------------------------------------------

class TC07_BoostEnd_Timestamps(unittest.TestCase):
    """Testy časového razítka konce boostu."""

    def test_boost_end_zero_no_active_boost(self):
        """boostEnd = 0 indikuje neaktivní boost – výchozí stav musí projít."""
        result = validate_save_payload(_boost_payload(None, 1, 0))
        self.assertEqual(result['boostEnd'], 0)

    def test_boost_end_future_timestamp_is_accepted(self):
        """boostEnd v budoucnosti (30 minut od teď) musí projít validací."""
        future_end = _NOW_MS + _30_MIN_MS
        result = validate_save_payload(_boost_payload('pps', 2, future_end))
        self.assertEqual(result['boostEnd'], future_end)

    def test_boost_end_past_timestamp_is_accepted(self):
        """boostEnd v minulosti musí validátorem projít – expiraci řeší herní logika, ne validátor."""
        past_end = _NOW_MS - _30_MIN_MS
        result = validate_save_payload(_boost_payload('click', 2, past_end))
        self.assertEqual(result['boostEnd'], past_end)

    def test_boost_end_large_timestamp_is_accepted(self):
        """boostEnd = 2e13 (vzdálená budoucnost) musí projít – validátor nekontroluje horní limit."""
        result = validate_save_payload(_boost_payload('all', 2, int(2e13)))
        self.assertGreater(result['boostEnd'], 0)

    def test_boost_end_float_whole_is_coerced_to_int(self):
        """boostEnd = 1.74e12 jako float musí být koercován na int."""
        p = _boost_payload('pps', 2, 0)
        p['boostEnd'] = 1_743_063_600_000.0
        result = validate_save_payload(p)
        self.assertIsInstance(result['boostEnd'], int)

    def test_boost_end_negative_is_rejected(self):
        """boostEnd = -1 musí být odmítnuto – záporný timestamp nedává smysl."""
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(_boost_payload(None, 1, -1))
        self.assertIn('at least 0', str(ctx.exception))


# ---------------------------------------------------------------------------
# Testy kombinací boost polí (spin wheel scénáře)
# ---------------------------------------------------------------------------

class TC07_BoostCombinations(unittest.TestCase):
    """Testy logicky konzistentních kombinací boost polí dle spin wheel odměn."""

    def test_spin_reward_2x_click_30min(self):
        """Odměna '2× klik (30 min)': boostType='click', mult=2, end=+30min."""
        end = _NOW_MS + _30_MIN_MS
        result = validate_save_payload(_boost_payload('click', 2, end))
        self.assertEqual(result['boostType'], 'click')
        self.assertEqual(result['boostMult'], 2)
        self.assertEqual(result['boostEnd'], end)

    def test_spin_reward_2x_pps_30min(self):
        """Odměna '2× PPS (30 min)': boostType='pps', mult=2, end=+30min."""
        end = _NOW_MS + _30_MIN_MS
        result = validate_save_payload(_boost_payload('pps', 2, end))
        self.assertEqual(result['boostType'], 'pps')
        self.assertEqual(result['boostMult'], 2)

    def test_spin_reward_3x_pps_15min(self):
        """Odměna '3× PPS (15 min)': boostType='pps', mult=3, end=+15min."""
        end = _NOW_MS + _15_MIN_MS
        result = validate_save_payload(_boost_payload('pps', 3, end))
        self.assertEqual(result['boostType'], 'pps')
        self.assertEqual(result['boostMult'], 3)

    def test_spin_reward_2x_all_20min(self):
        """Odměna '2× vše (20 min)': boostType='all', mult=2, end=+20min."""
        end = _NOW_MS + _20_MIN_MS
        result = validate_save_payload(_boost_payload('all', 2, end))
        self.assertEqual(result['boostType'], 'all')
        self.assertEqual(result['boostMult'], 2)

    def test_no_boost_active_null_type_mult_1_end_0(self):
        """Stav bez aktivního boostu: boostType=None, mult=1, end=0 musí projít."""
        result = validate_save_payload(_boost_payload(None, 1, 0))
        self.assertIsNone(result['boostType'])
        self.assertEqual(result['boostMult'], 1)
        self.assertEqual(result['boostEnd'], 0)

    def test_all_three_boost_types_in_separate_payloads(self):
        """Každý boost typ musí být uložitelný v samostatném payloadu."""
        for boost_type in ('click', 'pps', 'all'):
            with self.subTest(boost_type=boost_type):
                end = _NOW_MS + _30_MIN_MS
                result = validate_save_payload(_boost_payload(boost_type, 2, end))
                self.assertEqual(result['boostType'], boost_type)

    def test_boost_end_coercion_in_full_boost_payload(self):
        """boostEnd jako float v plném boost payloadu musí být koercován na int."""
        p = _boost_payload('pps', 2, 0)
        p['boostEnd'] = float(_NOW_MS + _30_MIN_MS)
        result = validate_save_payload(p)
        self.assertIsInstance(result['boostEnd'], int)
        self.assertIsInstance(result['boostMult'], (int, float))


# ---------------------------------------------------------------------------
# Testy neplatných typů boost polí
# ---------------------------------------------------------------------------

class TC07_BoostFields_InvalidTypes(unittest.TestCase):
    """Testy odmítnutí špatných datových typů pro boost pole."""

    def test_boost_mult_boolean_true_is_rejected(self):
        """boostMult = True (boolean) musí být odmítnuto – bool není číslo."""
        p = _boost_payload(None, 1, 0)
        p['boostMult'] = True
        with self.assertRaises(BadRequest):
            validate_save_payload(p)

    def test_boost_mult_string_is_rejected(self):
        """boostMult = '2' (řetězec) musí být odmítnuto."""
        p = _boost_payload(None, 1, 0)
        p['boostMult'] = '2'
        with self.assertRaises(BadRequest):
            validate_save_payload(p)

    def test_boost_end_string_is_rejected(self):
        """boostEnd = '1743000000000' (řetězec místo čísla) musí být odmítnuto."""
        p = _boost_payload(None, 1, 0)
        p['boostEnd'] = '1743000000000'
        with self.assertRaises(BadRequest):
            validate_save_payload(p)

    def test_boost_end_none_is_rejected(self):
        """boostEnd = None musí být odmítnuto – musí být číslo (0 pro neaktivní)."""
        p = _boost_payload(None, 1, 0)
        p['boostEnd'] = None
        with self.assertRaises(BadRequest):
            validate_save_payload(p)

    def test_boost_type_integer_in_payload_is_rejected(self):
        """boostType = 1 (int) v save payloadu musí být odmítnuto."""
        p = _boost_payload(None, 1, 0)
        p['boostType'] = 1
        with self.assertRaises(BadRequest):
            validate_save_payload(p)


if __name__ == '__main__':
    unittest.main()
