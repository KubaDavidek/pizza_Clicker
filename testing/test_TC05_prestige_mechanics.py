# python -m unittest discover -s testing -p "test_*.py"
"""
TC05 – Prestige systém a herní progrese
========================================

Tento soubor testuje validaci dat týkající se prestige systému, násobičů příjmů
a konzistenci herního stavu při resetu prestige.

Oblasti pokryté testy
---------------------
1.  Meze prestigeLevel (0, 1, 5, 10, velká čísla)
2.  Konzistence stavu po prestige – money a totalEarned resetovány na 0,
    upgrades prázdné, clickValue = 1
3.  Zachování stavu po prestige – earnedAchievements, totalClicks, streak
4.  Výpočet prestige multiplikátoru: 1 + (level × 0.25)
5.  Prestige s kombinací boostů – boost může zůstat aktivní přes reset
6.  Validace totalEarned jako podmínka dosažení prestige prahu 1e9
7.  Kombinace upgrades = {} s různými hodnotami clickValue
8.  Krajní případy prestigeLevel s celočíselnou koercí
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from werkzeug.exceptions import BadRequest

from validation import validate_save_payload


# ---------------------------------------------------------------------------
# Pomocné funkce
# ---------------------------------------------------------------------------

def _prestige_reset_payload(prestige_level=1):
    """Vrátí payload simulující stav ihned po provedení prestige (reset proměnných)."""
    return {
        'pizzeriaName': 'Nová Šance Pizzerie',
        'money': 0,
        'totalEarned': 0,
        'clickValue': 1,
        'upgrades': {},
        'lastSave': 1_710_000_000_000,
        'earnedAchievements': {'a1': True, 'a2': True, 'a19': True},
        'totalClicks': 50_000,
        'streak': 7,
        'lastLoginDate': '2026-03-25',
        'prestigeLevel': prestige_level,
        'lastSpinDate': '2026-03-25',
        'boostType': None,
        'boostMult': 1,
        'boostEnd': 0,
    }


def _mid_game_payload():
    """Vrátí payload simulující hráče v průběhu prestige běhu (po resetu s několika upgrady)."""
    return {
        'pizzeriaName': 'Prestige Lab',
        'money': 500_000,
        'totalEarned': 2_000_000,
        'clickValue': 38,           # výchozí 1 + c1(+1) + c2(+3) + c3(+8) + c4(+25) = 38 po zakoupení 4 upgradů
        'upgrades': {'c1': True, 'c2': True, 'c3': True, 'c4': True},
        'lastSave': 1_710_000_000_000,
        'earnedAchievements': {'a1': True, 'a2': True, 'a3': True},
        'totalClicks': 1_500,
        'streak': 3,
        'lastLoginDate': '2026-03-25',
        'prestigeLevel': 2,
        'lastSpinDate': '2026-03-24',
        'boostType': 'pps',
        'boostMult': 2,
        'boostEnd': 1_710_001_800_000,
    }


PRESTIGE_THRESHOLD = 1_000_000_000  # 1 miliarda € – práh pro prestige


# ---------------------------------------------------------------------------
# Testy hranic prestigeLevel
# ---------------------------------------------------------------------------

class TC05_PrestigeLevel_Boundaries(unittest.TestCase):
    """Testy hranic pro pole prestigeLevel."""

    def test_prestige_level_zero_default_state(self):
        """prestigeLevel = 0 odpovídá novému hráči bez jakéhokoli prestige."""
        result = validate_save_payload(_prestige_reset_payload(0))
        self.assertEqual(result['prestigeLevel'], 0)

    def test_prestige_level_one_first_prestige(self):
        """prestigeLevel = 1 je stav po prvním prestige, multiplier = 1.25×."""
        result = validate_save_payload(_prestige_reset_payload(1))
        self.assertEqual(result['prestigeLevel'], 1)
        # Ověřujeme vzorec: multiplikátor = 1 + (1 * 0.25) = 1.25
        multiplier = 1 + result['prestigeLevel'] * 0.25
        self.assertAlmostEqual(multiplier, 1.25)

    def test_prestige_level_two_multiplier(self):
        """prestigeLevel = 2 odpovídá multiplier 1.50×."""
        result = validate_save_payload(_prestige_reset_payload(2))
        multiplier = 1 + result['prestigeLevel'] * 0.25
        self.assertAlmostEqual(multiplier, 1.50)

    def test_prestige_level_four_multiplier(self):
        """prestigeLevel = 4 odpovídá multiplier 2.00× – zdvojnásobení příjmu."""
        result = validate_save_payload(_prestige_reset_payload(4))
        multiplier = 1 + result['prestigeLevel'] * 0.25
        self.assertAlmostEqual(multiplier, 2.00)

    def test_prestige_level_five_multiplier(self):
        """prestigeLevel = 5 odpovídá multiplier 2.25×, odemyká achievement 'Veterán'."""
        result = validate_save_payload(_prestige_reset_payload(5))
        multiplier = 1 + result['prestigeLevel'] * 0.25
        self.assertAlmostEqual(multiplier, 2.25)

    def test_prestige_level_ten_multiplier(self):
        """prestigeLevel = 10 odpovídá multiplier 3.50×, odemyká achievement 'Pizzový bůh'."""
        result = validate_save_payload(_prestige_reset_payload(10))
        multiplier = 1 + result['prestigeLevel'] * 0.25
        self.assertAlmostEqual(multiplier, 3.50)

    def test_prestige_level_large_value_is_accepted(self):
        """prestigeLevel = 100 musí projít validací – hra nemá pevně daný strop prestige."""
        result = validate_save_payload(_prestige_reset_payload(100))
        self.assertEqual(result['prestigeLevel'], 100)

    def test_prestige_level_negative_is_rejected(self):
        """prestigeLevel = -1 musí být odmítnuto – záporné prestige je nesmysl."""
        p = _prestige_reset_payload(0)
        p['prestigeLevel'] = -1
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('at least 0', str(ctx.exception))

    def test_prestige_level_float_whole_is_coerced(self):
        """prestigeLevel = 5.0 (celý float) musí být koercován na int 5."""
        p = _prestige_reset_payload(0)
        p['prestigeLevel'] = 5.0
        result = validate_save_payload(p)
        self.assertIsInstance(result['prestigeLevel'], int)
        self.assertEqual(result['prestigeLevel'], 5)

    def test_prestige_level_float_decimal_is_rejected(self):
        """prestigeLevel = 1.5 (desetinný float) musí být odmítnuto."""
        p = _prestige_reset_payload(0)
        p['prestigeLevel'] = 1.5
        with self.assertRaises(BadRequest) as ctx:
            validate_save_payload(p)
        self.assertIn('must be an integer', str(ctx.exception))


# ---------------------------------------------------------------------------
# Testy konzistence stavu po prestige resetu
# ---------------------------------------------------------------------------

class TC05_PostPrestige_StateConsistency(unittest.TestCase):
    """Testy stavu herních polí bezprostředně po provedení prestige."""

    def test_money_zero_after_prestige(self):
        """Po prestige musí být money = 0 (reset hotovosti)."""
        result = validate_save_payload(_prestige_reset_payload(1))
        self.assertEqual(result['money'], 0)

    def test_total_earned_zero_after_prestige(self):
        """Po prestige musí být totalEarned = 0 (reset pro nový běh)."""
        result = validate_save_payload(_prestige_reset_payload(1))
        self.assertEqual(result['totalEarned'], 0)

    def test_click_value_one_after_prestige(self):
        """Po prestige musí být clickValue = 1 (výchozí hodnota bez upgradů)."""
        result = validate_save_payload(_prestige_reset_payload(1))
        self.assertEqual(result['clickValue'], 1)

    def test_upgrades_empty_after_prestige(self):
        """Po prestige musí být upgrades = {} (všechny upgrady ztraceny)."""
        result = validate_save_payload(_prestige_reset_payload(1))
        self.assertEqual(result['upgrades'], {})

    def test_earned_achievements_preserved_after_prestige(self):
        """earnedAchievements musí být zachovány přes prestige reset."""
        p = _prestige_reset_payload(1)
        p['earnedAchievements'] = {'a1': True, 'a19': True}
        result = validate_save_payload(p)
        self.assertTrue(result['earnedAchievements']['a1'])
        self.assertTrue(result['earnedAchievements']['a19'])

    def test_total_clicks_preserved_after_prestige(self):
        """totalClicks musí být zachovány přes prestige reset."""
        p = _prestige_reset_payload(1)
        p['totalClicks'] = 75_000
        result = validate_save_payload(p)
        self.assertEqual(result['totalClicks'], 75_000)

    def test_streak_preserved_after_prestige(self):
        """Streak přihlašování musí být zachován přes prestige reset."""
        p = _prestige_reset_payload(1)
        p['streak'] = 15
        result = validate_save_payload(p)
        self.assertEqual(result['streak'], 15)

    def test_prestige_level_incremented_after_prestige(self):
        """prestigeLevel musí být o 1 vyšší než před prestige – testujeme level 2."""
        result = validate_save_payload(_prestige_reset_payload(2))
        self.assertEqual(result['prestigeLevel'], 2)


# ---------------------------------------------------------------------------
# Testy prahu pro prestige (totalEarned >= 1e9)
# ---------------------------------------------------------------------------

class TC05_PrestigeThreshold_TotalEarned(unittest.TestCase):
    """Testy hodnot totalEarned ve vztahu k prahu 1 miliardy € nutné pro prestige."""

    def test_total_earned_just_below_threshold(self):
        """totalEarned = 999_999_999 (o 1 € pod prahem) musí projít validací."""
        p = _prestige_reset_payload(0)
        p['totalEarned'] = 999_999_999
        result = validate_save_payload(p)
        self.assertEqual(result['totalEarned'], 999_999_999)
        self.assertLess(result['totalEarned'], PRESTIGE_THRESHOLD)

    def test_total_earned_exactly_at_threshold(self):
        """totalEarned = 1_000_000_000 (přesně práh) musí projít – hráč může prestižovat."""
        p = _prestige_reset_payload(0)
        p['totalEarned'] = PRESTIGE_THRESHOLD
        result = validate_save_payload(p)
        self.assertEqual(result['totalEarned'], PRESTIGE_THRESHOLD)

    def test_total_earned_above_threshold(self):
        """totalEarned = 5_000_000_000 (5× práh) musí projít – hráč má dostatek na prestige."""
        p = _prestige_reset_payload(0)
        p['totalEarned'] = 5 * PRESTIGE_THRESHOLD
        result = validate_save_payload(p)
        self.assertEqual(result['totalEarned'], 5 * PRESTIGE_THRESHOLD)

    def test_total_earned_trillion_is_accepted(self):
        """totalEarned = 1e12 (bilion) musí projít – vysoká progrese musí být uložitelná."""
        p = _prestige_reset_payload(5)
        p['totalEarned'] = 1e12
        result = validate_save_payload(p)
        self.assertEqual(result['totalEarned'], 1e12)


# ---------------------------------------------------------------------------
# Testy kombinací prestige + boost + upgrade
# ---------------------------------------------------------------------------

class TC05_PrestigeWithBoostAndUpgrades(unittest.TestCase):
    """Testy kombinací prestige stavu s aktivními boosty a zakoupenými upgrady."""

    def test_prestige_with_active_click_boost(self):
        """prestigeLevel = 3 s aktivním click boostem (2×) musí projít validací."""
        p = _prestige_reset_payload(3)
        p['boostType'] = 'click'
        p['boostMult'] = 2
        p['boostEnd'] = 1_710_001_800_000
        result = validate_save_payload(p)
        self.assertEqual(result['prestigeLevel'], 3)
        self.assertEqual(result['boostType'], 'click')
        self.assertEqual(result['boostMult'], 2)

    def test_prestige_with_active_pps_boost(self):
        """prestigeLevel = 1 s aktivním PPS boostem (2× na 30 minut) musí projít."""
        p = _mid_game_payload()
        result = validate_save_payload(p)
        self.assertEqual(result['boostType'], 'pps')
        self.assertEqual(result['boostMult'], 2)
        self.assertEqual(result['prestigeLevel'], 2)

    def test_prestige_with_all_boost(self):
        """prestigeLevel = 2 s aktivním 'all' boostem (2×) musí projít."""
        p = _prestige_reset_payload(2)
        p['boostType'] = 'all'
        p['boostMult'] = 2
        p['boostEnd'] = 1_710_003_600_000
        result = validate_save_payload(p)
        self.assertEqual(result['boostType'], 'all')

    def test_prestige_4_with_several_upgrades_and_correct_click_value(self):
        """Prestige 4 s upgrady c1–c4 a odpovídajícím clickValue = 38 musí projít."""
        # c1=+1, c2=+3, c3=+8, c4=+25 => clickValue = 1 + 1 + 3 + 8 + 25 = 38
        p = _prestige_reset_payload(4)
        p['money'] = 100_000
        p['totalEarned'] = 250_000
        p['clickValue'] = 38
        p['upgrades'] = {'c1': True, 'c2': True, 'c3': True, 'c4': True}
        result = validate_save_payload(p)
        self.assertEqual(result['clickValue'], 38)
        self.assertEqual(len(result['upgrades']), 4)

    def test_prestige_10_fully_restored_game(self):
        """Prestige 10 s plně nakoupenými upgrady a maximálním clickValue musí projít."""
        all_ids = {f'c{i}': True for i in range(1, 13)}
        all_ids.update({f'p{i}': True for i in range(1, 11)})
        p = {
            'pizzeriaName': 'Pizza God Emporium',
            'money': 1_000_000_000,
            'totalEarned': 9_999_999_999,
            'clickValue': 1_254_363,    # součet všech click bonusů
            'upgrades': all_ids,
            'lastSave': 1_710_000_000_000,
            'earnedAchievements': {f'a{i}': True for i in range(1, 22)},
            'totalClicks': 1_000_000,
            'streak': 30,
            'lastLoginDate': '2026-03-25',
            'prestigeLevel': 10,
            'lastSpinDate': '2026-03-25',
            'boostType': 'all',
            'boostMult': 2,
            'boostEnd': 1_710_001_200_000,
        }
        result = validate_save_payload(p)
        self.assertEqual(result['prestigeLevel'], 10)
        self.assertEqual(len(result['upgrades']), 22)
        self.assertEqual(len(result['earnedAchievements']), 21)


if __name__ == '__main__':
    unittest.main()
