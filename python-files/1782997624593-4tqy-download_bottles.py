# -*- coding: utf-8 -*-
"""
Скачивает фото бутылок с карточек SimpleWine в папку ./bottles/<id>.jpg
Запуск (нужен Python 3 и интернет):
    pip install requests
    python download_bottles.py
Повторный запуск докачивает только недостающие. Потом папку bottles/ залей на сайт рядом с barnaya-karta.html
"""
import os, re, time, sys
try:
    import requests
except ImportError:
    print("Сначала выполните: pip install requests"); sys.exit(1)

os.makedirs("bottles", exist_ok=True)
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"}

ITEMS = [
    ("dassai_39_072_145325", "https://simplewine.ru/catalog/product/dassai_39_072_145325/"),
    ("dassai_45_junmai_daiginjo_072_146228", "https://simplewine.ru/catalog/product/dassai_45_junmai_daiginjo_072_146228/"),
    ("aizu_homare_daiginjo_072_gift_148683", "https://simplewine.ru/catalog/product/aizu_homare_daiginjo_072_gift_148683/"),
    ("hakushika_sparkling_sake_072_146227", "https://simplewine.ru/catalog/product/hakushika_sparkling_sake_072_146227/"),
    ("nonino_quintessentia_amaro_07_gift_1", "https://simplewine.ru/catalog/product/nonino_quintessentia_amaro_07_gift_1/"),
    ("nonino_botanical_drink_in_tube_07_gift_141142", "https://simplewine.ru/catalog/product/nonino_botanical_drink_in_tube_07_gift_141142/"),
    ("choya_yuzu_075_155429", "https://simplewine.ru/catalog/product/choya_yuzu_075_155429/"),
    ("griottini_1_147043", "https://simplewine.ru/catalog/product/griottini_1_147043/"),
    ("graham_s_the_tawny_port_075_155334", "https://simplewine.ru/catalog/product/graham_s_the_tawny_port_075_155334/"),
    ("graham_s_blend_n_12_ruby_port_075_155327", "https://simplewine.ru/catalog/product/graham_s_blend_n_12_ruby_port_075_155327/"),
    ("graham_s_blend_no_5_white_port_075_155333", "https://simplewine.ru/catalog/product/graham_s_blend_no_5_white_port_075_155333/"),
    ("warre_s_otima_20_year_old_tawny_port_05_gift_155331", "https://simplewine.ru/catalog/product/warre_s_otima_20_year_old_tawny_port_05_gift_155331/"),
    ("warre_s_otima_10_year_old_tawny_port_2017_05_gift_155336", "https://simplewine.ru/catalog/product/warre_s_otima_10_year_old_tawny_port_2017_05_gift_155336/"),
    ("valdespino_fino_inocente_075_132781", "https://simplewine.ru/catalog/product/valdespino_fino_inocente_075_132781/"),
    ("aberlour_aged_12_years_double_cask_matured_07_gift_157293", "https://simplewine.ru/catalog/product/aberlour_aged_12_years_double_cask_matured_07_gift_157293/"),
    ("chivas_regal_18_years_old_075_gift_146960", "https://simplewine.ru/catalog/product/chivas_regal_18_years_old_075_gift_146960/"),
    ("macallan_double_cask_matured_12_years_old_07_gift_159834", "https://simplewine.ru/catalog/product/macallan_double_cask_matured_12_years_old_07_gift_159834/"),
    ("mac_talla_terra_classic_islay_smoky_fresh_single_malt_nas_in_gift_box_07_gift_153147", "https://simplewine.ru/catalog/product/mac_talla_terra_classic_islay_smoky_fresh_single_malt_nas_in_gift_box_07_gift_153147/"),
    ("bushmills_single_malt_aged_10_years_07_gift_155655", "https://simplewine.ru/catalog/product/bushmills_single_malt_aged_10_years_07_gift_155655/"),
    ("bushmills_single_malt_aged_14_years_07_gift_155657", "https://simplewine.ru/catalog/product/bushmills_single_malt_aged_14_years_07_gift_155657/"),
    ("singleton_15_years_old_07_gift_145959", "https://simplewine.ru/catalog/product/singleton_15_years_old_07_gift_145959/"),
    ("togouchi_premium_in_gift_box_07_gift_142280", "https://simplewine.ru/catalog/product/togouchi_premium_in_gift_box_07_gift_142280/"),
    ("chateau_clement_pichon_2018_075_154184", "https://simplewine.ru/catalog/product/chateau_clement_pichon_2018_075_154184/"),
    ("finca_nueva_gran_reserva_2010_075_145918", "https://simplewine.ru/catalog/product/finca_nueva_gran_reserva_2010_075_145918/"),
    ("finca_nueva_reserva_2015_075_148708", "https://simplewine.ru/catalog/product/finca_nueva_reserva_2015_075_148708/"),
    ("tenuta_perano_chianti_classico_riserva_2021_075_149753", "https://simplewine.ru/catalog/product/tenuta_perano_chianti_classico_riserva_2021_075_149753/"),
    ("tenuta_frescobaldi_di_castiglioni_2022_075_151571", "https://simplewine.ru/catalog/product/tenuta_frescobaldi_di_castiglioni_2022_075_151571/"),
    ("clarendelle_by_haut_brion_medoc_2022_075_154466", "https://simplewine.ru/catalog/product/clarendelle_by_haut_brion_medoc_2022_075_154466/"),
    ("ripassa_della_valpolicella_superiore_2021_075_158491", "https://simplewine.ru/catalog/product/ripassa_della_valpolicella_superiore_2021_075_158491/"),
    ("montessu_2023_075_158572", "https://simplewine.ru/catalog/product/montessu_2023_075_158572/"),
    ("sancerre_pinot_noir_rouge_2022_075_156472", "https://simplewine.ru/catalog/product/sancerre_pinot_noir_rouge_2022_075_156472/"),
    ("clos_bertrand_2023_075_155271", "https://simplewine.ru/catalog/product/clos_bertrand_2023_075_155271/"),
    ("finca_resalso_2024_075_155691", "https://simplewine.ru/catalog/product/finca_resalso_2024_075_155691/"),
    ("gran_reserva_cabernet_sauvignon_2022_075_155463", "https://simplewine.ru/catalog/product/gran_reserva_cabernet_sauvignon_2022_075_155463/"),
    ("bell_assai_2023_075_154734", "https://simplewine.ru/catalog/product/bell_assai_2023_075_154734/"),
    ("lezer_2024_075_154431", "https://simplewine.ru/catalog/product/lezer_2024_075_154431/"),
    ("chianti_classico_2023_075_155775", "https://simplewine.ru/catalog/product/chianti_classico_2023_075_155775/"),
    ("prellenkirchen_samt_seide_2022_075_157006", "https://simplewine.ru/catalog/product/prellenkirchen_samt_seide_2022_075_157006/"),
    ("lighea_2025_075_160276", "https://simplewine.ru/catalog/product/lighea_2025_075_160276/"),
    ("chiaranda_2021_075_144258", "https://simplewine.ru/catalog/product/chiaranda_2021_075_144258/"),
    ("lumera_2024_075_153266", "https://simplewine.ru/catalog/product/lumera_2024_075_153266/"),
    ("gavi_dei_gavi_etichetta_nera_2024_075_155291", "https://simplewine.ru/catalog/product/gavi_dei_gavi_etichetta_nera_2024_075_155291/"),
    ("lafoa_sauvignon_2023_075_157305", "https://simplewine.ru/catalog/product/lafoa_sauvignon_2023_075_157305/"),
    ("lafoa_chardonnay_2023_075_157313", "https://simplewine.ru/catalog/product/lafoa_chardonnay_2023_075_157313/"),
    ("lafoa_chardonnay_2024_075_161233", "https://simplewine.ru/catalog/product/lafoa_chardonnay_2024_075_161233/"),
    ("sul_vulcano_etna_bianco_2022_075_154741", "https://simplewine.ru/catalog/product/sul_vulcano_etna_bianco_2022_075_154741/"),
    ("tenuta_tascante_buonora_2024_075_155096", "https://simplewine.ru/catalog/product/tenuta_tascante_buonora_2024_075_155096/"),
    ("piere_sauvignon_2023_075_156528", "https://simplewine.ru/catalog/product/piere_sauvignon_2023_075_156528/"),
    ("pinot_grigio_zuc_di_volpe_2021_075_155784", "https://simplewine.ru/catalog/product/pinot_grigio_zuc_di_volpe_2021_075_155784/"),
    ("chablis_premier_cru_vaudevey_2022_075_152744", "https://simplewine.ru/catalog/product/chablis_premier_cru_vaudevey_2022_075_152744/"),
    ("petit_bourgeois_sauvignon_2023_075_151517", "https://simplewine.ru/catalog/product/petit_bourgeois_sauvignon_2023_075_151517/"),
    ("la_fuga_chardonnay_2023_075_152590", "https://simplewine.ru/catalog/product/la_fuga_chardonnay_2023_075_152590/"),
    ("cotes_du_rhone_blanc_2023_075_148997", "https://simplewine.ru/catalog/product/cotes_du_rhone_blanc_2023_075_148997/"),
    ("chardonnay_heritage_an_1130_2025_075_159497", "https://simplewine.ru/catalog/product/chardonnay_heritage_an_1130_2025_075_159497/"),
    ("tokaj_late_harvest_2022_05_153664", "https://simplewine.ru/catalog/product/tokaj_late_harvest_2022_05_153664/"),
    ("gewurztraminer_2024_075_157307", "https://simplewine.ru/catalog/product/gewurztraminer_2024_075_157307/"),
    ("gewurztraminer_2020_075_150114", "https://simplewine.ru/catalog/product/gewurztraminer_2020_075_150114/"),
    ("riesling_trocken_2024_075_159294", "https://simplewine.ru/catalog/product/riesling_trocken_2024_075_159294/"),
    ("riesling_2022_075_150442", "https://simplewine.ru/catalog/product/riesling_2022_075_150442/"),
    ("dolce_gabbana_isolano_2022_075_gift_152852", "https://simplewine.ru/catalog/product/dolce_gabbana_isolano_2022_075_gift_152852/"),
    ("pais_carinena_phoenix_ferment_2022_075_153914", "https://simplewine.ru/catalog/product/pais_carinena_phoenix_ferment_2022_075_153914/"),

]

def og_image(html):
    for pat in [r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']']:
        m=re.search(pat, html, re.I)
        if m: return m.group(1)
    return None

ok=skip=fail=0
for i,(slug,url) in enumerate(ITEMS,1):
    out=os.path.join("bottles", slug+".jpg")
    if os.path.exists(out) and os.path.getsize(out)>1000:
        skip+=1; continue
    try:
        r=requests.get(url, headers=UA, timeout=25); r.raise_for_status()
        img=og_image(r.text)
        if not img:
            print(f"[{i}/61] ! не нашёл фото: {slug}"); fail+=1; continue
        if img.startswith("//"): img="https:"+img
        ir=requests.get(img, headers=UA, timeout=25); ir.raise_for_status()
        with open(out,"wb") as f: f.write(ir.content)
        print(f"[{i}/61] ✓ {slug}"); ok+=1
        time.sleep(0.7)
    except Exception as e:
        print(f"[{i}/61] ! ошибка {slug}: {e}"); fail+=1
print(f"\nГотово. Скачано: {ok}, уже было: {skip}, не вышло: {fail}")
print("Папку bottles/ загрузите на сайт рядом с barnaya-karta.html")
