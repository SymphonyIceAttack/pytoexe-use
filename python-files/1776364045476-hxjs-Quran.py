# 1. We get the inputs and force them to lowercase immediately
sura = input("What sura you want read?: ").lower()
arab = input("In arab: ").lower()

# 2. Logic for TRANSCRIPTION (if they say "no" to Arabic)
if (sura == "al-fatiha") and (arab == "no"):
    print("""
[Opening]
A'udhu billahi minash-shaytanir-rajim

[Surah Al-Fatiha]
1. Bismillaahir-Rahmaanir-Raheem
2. Al-hamdu lillaahi Rabbil-'aalameen
3. Ar-Rahmaanir-Raheem
4. Maaliki Yawmid-Deen
5. Iyyaaka na'budu wa iyyaaka nasta'een
6. Ihdinas-Siraatal-Mustaqeem
7. Siraatal-ladheena an'amta 'alayhim ghayril-maghdoobi 'alayhim walad-daalleen
""")

# 3. Logic for ARABIC (if they say "yes" to Arabic)
elif (sura == "al-fatiha") and (arab == "yes"):
    print("""
[أعوذ بالله]
أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ

[سورة الفاتحة]
١. بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ
٢. الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ
٣. الرَّحْمَنِ الرَّحِيمِ
٤. مَالِكِ يَوْمِ الدِّينِ
٥. إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ
٦. اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ
٧. صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ
""")
elif (sura == "al-ikhlas") and (arab == "no"):
    print("""
[Opening]
A'udhu billahi minash-shaytanir-rajim

[Surah Al-Ikhlas]
1. Qul huwal-laahu ahad
2. Allaahus-samad
3. Lam yalid wa lam yoolad
4. Wa lam yakul-lahoo kufuwan ahad
""")
elif (sura == "al-ikhlas") and (arab == "yes"):
    print("""
[أعوذ بالله]
أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ

[سورة الإخلاص]
١. قُلْ هُوَ اللَّهُ أَحَدٌ
٢. اللَّهُ الصَّمَدُ
٣. لَمْ يَلِدْ وَلَمْ يُولَدْ
٤. وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ""")
elif (sura == "al-mulk") and (arab == "no"):
    print("""
[Opening]
A'udhu billahi minash-shaytanir-rajim

1. Tabaarakal-ladhee biyadihil-mulku wa huwa 'alaa kulli shay-in qadeer
2. Alladhee khalaqal-mawta wal-hayaata liyabluwakum ayyukum ahsanu 'amalaa, wa huwal-'azeezul-ghafoor
3. Alladhee khalaqa sab'a samaawaatin tibaaqaa, maa taraa fee khalqir-rahmaani min tafaawut, farji'il-basara hal taraa min futoor
4. Thummar-ji'il-basara karratayni yanqalib ilaykal-basaru khaasi-an wa huwa haseer
5. Wa laqad zayyannas-samaaa'ad-dunyaa bimasaabeeha wa ja'alnaaha rujoomal-lish-shayaateeni wa a'tadnaa lahum 'adhaabas-sa'eer
6. Wa lilladheena kafaroo bi-rabbihim 'adhaabu jahannama wa bi'sal-maseer
7. Idhaa ulqoo feehaa sami'oo lahaa shaheeqan wa hiya tafoor
8. Takaadu tamayyazu minal-ghaydh, kullamaaa ulqiya feehaa fawjun sa-alahum khazanatuhaaa alam ya'tikum nadheer
9. Qaaloo balaa qad jaaa'anaa nadheerun fakadh-dhabnaa wa qulnaa maa nazzalallaahu min shay-in in antum illaa fee dalaalin kabeer
10. Wa qaaloo law kunnaa nasma'u aw na'qilu maa kunnaa fee as-haabis-sa'eer
11. Fa'tarafoo bidhambihim fasuhqal-li-as-haabis-sa'eer
12. Innal-ladheena yakhshawna rabbahum bilghaybi lahum maghfiratuw-wa ajrun kabeer
13. Wa asirroo qawlakum awij-haroo bihee innahoo 'aleemum bidhaatis-sudoor
14. Alaa ya'lamu man khalaqa wa huwal-lateeful-khabeer
15. Huwal-ladhee ja'ala lakumul-arda dhaloolan famshoo fee manaakibihaa wa kuloo mir-rizqihee wa ilayhin-nushoor
16. A-amintum man fissamaaa'i ay-yakhsifa bikumul-arda fa-idhaa hiya tamoor
17. Am amintum man fissamaaa'i ay-yursila 'alaykum haasiban fasata'lamoona kayfa nadheer
18. Wa laqad kadh-dhabal-ladheena min qablihim fakayfa kaana nakeer
19. Awalam yaraw ilat-tayri fawqahum saaffaatiw-wa yaqbidna, maa yumsiku-hunna illar-rahmaan, innahoo bikulli shay-im baseer
20. Amman haadhal-ladhee huwa jundul-lakum yansurukum min doonir-rahmaan, inil-kaafiroona illaa fee ghuroor
21. Amman haadhal-ladhee yarzuqukum in amsaka rizqahoo bal-laj-joo fee 'utuwwiw-wa nufoor
22. Afaman yamshiee mukibban 'alaa wajhihee ahdaaa amman yamshiee sawiyyan 'alaa siraatim-mustaqeem
23. Qul huwal-ladhee ansha-akum wa ja'ala lakumus-sam'a wal-absaara wal-af-idata qaleelam-maa tashkuroon
24. Qul huwal-ladhee dhara-akum fil-ardi wa ilayhi tuhsharoon
25. Wa yaqooloona mataa haadhal-wa'du in kuntum saadi qeen
26. Qul innamal-'ilmu 'indallaahi wa innamaaa ana nadheerum mubeen
27. Falammaa ra-awhu zulfatan seee'at wujoohul-ladheena kafaroo wa qeela haadhal-ladhee kuntum bihee tadda'oon
28. Qul ara-aytum in ahlakaniyallaahu wa mam-ma'iya aw rahimanaa famay-yujeerul-kaafireena min 'adhaabin aleem
29. Qul huwar-rahmaanu aamannaa bihee wa 'alayhi tawakkalnaa fasata'lamoona man huwa fee dalaalim-mubeen
30. Qul ara-aytum in asbaha maaa'ukum ghawran famay-ya'teekum bimaaa'im-ma'een""")
elif (sura == "al-mulk") and (arab == "yes"):
    print("""
[أعوذ بالله]
أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ

[أعوذ بالله]
أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ

١. تَبَارَكَ الَّذِي بِيَدِهِ الْمُلْكُ وَهُوَ عَلَىٰ كُلِّ شَيْءٍ قَدِيرٌ
٣. الَّذِي خَلَقَ سَبْعَ سَمَاوَاتٍ طِبَاقًا ۖ مَّا تَرَىٰ فِي خَلْقِ الرَّحْمَٰنِ مِن تَفَاوُتٍ ۖ فَارْجِعِ الْبَصَرَ هَلْ تَرَىٰ مِن فُطُورٍ
٤. ثُمَّ ارْجِعِ الْبَصَرَ كَرَّتَيْنِ يَنقَلِبْ إِلَيْكَ الْبَصَرُ خَاسِئًا وَهُوَ حَسِيرٌ
٥. وَلَقَدْ زَيَّنَّا السَّمَاءَ الدُّنْيَا بِمَصَابِيحَ وَجَعَلْنَاهَا رُجُومًا لِّلشَّيَاطِينِ ۖ وَأَعْتَدْنَا لَهُمْ عَذَابَ السَّعِيرِ
٦. وَلِلَّذِينَ كَفَرُوا بِرَبِّهِمْ عَذَابُ جَهَنَّمَ ۖ وَبِئْسَ الْمَصِيرُ
٧. إِذَا أُلْقُوا فِيهَا سَمِيعُوا لَهَا شَهِيقًا وَهِيَ تَفُورُ
٨. تَكَادُ تَمَيَّزُ مِنَ الْغَيْظِ ۖ كُلَّمَا أُلْقِيَ فِيهَا فَوْجٌ سَأَلَهُمْ خَزَنَتُهَا أَلَمْ يَأْتِكُمْ نَذِيرٌ
٩. قَالُوا بَلَىٰ قَدْ جَاءَنَا نَذِيرٌ فَكَذَّبْنَا وَقُلْنَا مَا نَزَّلَ اللَّهُ مِن شَيْءٍ إِنْ أَنتُمْ إِلَّا فِي ضَلَالٍ كَبِيرٍ
١٠. وَقَالُوا لَوْ كُنَّا نَسْمَعُ أَوْ نَعْقِلُ مَا كُنَّا فِي أَصْحَابِ السَّعِيرِ""")
elif (sura == "al-nasr") and (arab == "no"):
    print("""
[Opening]
A'udhu billahi minash-shaytanir-rajim

[Surah Al-Nasr]
1. Idhaa jaaa'a nasrul-laahi wal-fath
2. Wa ra-aitan-naasa yadkhuloona fee deenil-laahi afwaajaa
3. Fasabbih bihamdi rabbika was-taghfirh, innahoo kaana tawwaabaa""")
elif (sura == "al-nasr") and (arab == "yes"):
    print("""
[أعوذ بالله]
أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ

[سورة النصر]
١. إِذَا جَاءَ نَصْرُ اللَّهِ وَالْفَتْحُ
٢. وَرَأَيْتَ النَّاسَ يَدْخُلُونَ فِي دِينِ اللَّهِ أَفْوَاجًا
٣. فَسَبِّحْ بِحَمْدِ رَبِّكَ وَاسْتَغْفِرْهُ ۚ إِنَّهُ كَانَ تَوَّابًا""")








    
