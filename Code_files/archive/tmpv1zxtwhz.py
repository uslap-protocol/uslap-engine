# -*- coding: utf-8 -*-
# Generated from أَمْر source
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from amr_runtime import *

اُكْتُبْ('بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ')
اُكْتُبْ('═══ مَسْح اللَّوْح — CONTAMINATION SCAN ═══')
اُكْتُبْ('')
مَحْظُورَات = صَفّ('semitic', 'loanword', 'cognate', 'prosthetic vowel', 'borrowed from greek', 'borrowed from latin', 'borrowed from persian', 'borrowed from french', 'borrowed from german', 'borrowed from sanskrit', 'proto-indo-european', 'proto-slavic', 'proto-germanic', 'proto-turkic', 'proto-uralic', 'greek origin', 'latin origin', 'greek source', 'latin source', 'greek root', 'latin root', 'derived from greek', 'derived from latin', 'derived from french', 'derived from old french', 'derived from sanskrit', 'native slavic', 'native european', 'european origin', 'just slavic', 'just european', 'pre-greek substrate', 'indo-european')
إِضَافِيَّة = صَفّ('proto-indo', 'borrowed from', 'derived from', 'cognate with', 'loan from', 'adoption from', 'loaned from')
for م in إِضَافِيَّة:
    if (not اِبْحَثْ(مَحْظُورَات, م)):
        مَحْظُورَات = (مَحْظُورَات + [م])
اُكْتُبْ(صِلْ('', ['Scanning for ', كَلِمَة(طُول(مَحْظُورَات)), ' banned terms...']))
اُكْتُبْ('')
جَدَاوِل = لَوْح("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
اُكْتُبْ(صِلْ('', ['Tables to scan: ', كَلِمَة(طُول(جَدَاوِل))]))
اُكْتُبْ('')
إِجْمَالِي = 0
جَدَاوِل_مُلَوَّثَة = 0
تَفَاصِيل = صَفّ()
for جَدْوَل in جَدَاوِل:
    اِسْم_جَدْوَل = خُذْ(جَدْوَل, 'name')
    أَعْمِدَة = لَوْح(صِلْ('', ['PRAGMA table_info(', اِسْم_جَدْوَل, ')']))
    أَعْمِدَة_نَصِّيَّة = صَفّ()
    for ع in أَعْمِدَة:
        نَوْع = خُذْ(ع, 'type', '')
        if اِبْحَثْ(كَلِمَة(نَوْع), 'TEXT'):
            أَعْمِدَة_نَصِّيَّة = (أَعْمِدَة_نَصِّيَّة + [خُذْ(ع, 'name')])
    if (طُول(أَعْمِدَة_نَصِّيَّة) == 0):
        pass
    else:
        أَجْزَاء = صَفّ()
        for عَمُود in أَعْمِدَة_نَصِّيَّة:
            أَجْزَاء = (أَجْزَاء + [صِلْ('', ['COALESCE([', عَمُود, "],'')"])])
        نَصّ_مُدْمَج = صِلْ(" || ' ' || ", أَجْزَاء)
        إِصَابَات_جَدْوَل = 0
        for مُصْطَلَح in مَحْظُورَات:
            اِسْتِعْلَام = صِلْ('', ['SELECT COUNT(*) as cnt FROM [', اِسْم_جَدْوَل, '] WHERE LOWER(', نَصّ_مُدْمَج, ") LIKE '%", مُصْطَلَح, "%'"])
            try:
                نَتِيجَة = لَوْح(اِسْتِعْلَام)
                مَجْمُوع = خُذْ(خُذْ(نَتِيجَة, 0), 'cnt', 0)
                if (مَجْمُوع > 0):
                    إِصَابَات_جَدْوَل = (إِصَابَات_جَدْوَل + مَجْمُوع)
                    إِجْمَالِي = (إِجْمَالِي + مَجْمُوع)
                    تَفَاصِيل = (تَفَاصِيل + [صِلْ(' | ', [اِسْم_جَدْوَل, مُصْطَلَح, كَلِمَة(مَجْمُوع)])])
            except Exception as خ:
                pass
        if (إِصَابَات_جَدْوَل > 0):
            جَدَاوِل_مُلَوَّثَة = (جَدَاوِل_مُلَوَّثَة + 1)
            اُكْتُبْ(صِلْ('', ['⛔ ', اِسْم_جَدْوَل, ': ', كَلِمَة(إِصَابَات_جَدْوَل), ' hits']))
اُكْتُبْ('')
اُكْتُبْ('═══════════════════════════════════════')
اُكْتُبْ('CONTAMINATION SCAN REPORT')
اُكْتُبْ('═══════════════════════════════════════')
اُكْتُبْ(صِلْ('', ['Tables scanned: ', كَلِمَة(طُول(جَدَاوِل))]))
اُكْتُبْ(صِلْ('', ['Tables contaminated: ', كَلِمَة(جَدَاوِل_مُلَوَّثَة)]))
اُكْتُبْ(صِلْ('', ['Total hits: ', كَلِمَة(إِجْمَالِي)]))
اُكْتُبْ('')
if (طُول(تَفَاصِيل) > 0):
    اُكْتُبْ('DETAIL (table | term | count):')
    for سَطْر in تَفَاصِيل:
        اُكْتُبْ(صِلْ('', ['  ', سَطْر]))
else:
    اُكْتُبْ('الْحَمْدُ لِلَّهِ — NO CONTAMINATION FOUND')