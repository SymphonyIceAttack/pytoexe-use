import random

class BiteMarkForensicsQuiz:
    def __init__(self):
        self.score = 0
        self.total_questions = 0
        self.questions = []
        self.setup_questions()
    
    def setup_questions(self):
        """Initialize all quiz questions - COMPREHENSIVE coverage of ALL document content"""
        
        # ============================================================================
        # SECTION 1: GENERAL DEFINITION AND NATURE (Questions 1-15)
        # ============================================================================
        self.questions.extend([
            {
                "question": "According to the document, what is the complete definition of a bite mark?",
                "options": [
                    "A. Any injury near the mouth area",
                    "B. A patterned injury or physical impression created when teeth and jaws exert force on a surface",
                    "C. A bruise caused by blunt force trauma to the face",
                    "D. A scratch mark from teeth scraping skin"
                ],
                "correct": 1,
                "explanation": "A bite mark is defined as a patterned injury or physical impression created when teeth and jaws exert force on a surface, most commonly human skin."
            },
            {
                "question": "What aspects of teeth do bite mark patterns reflect?",
                "options": [
                    "A. Only the number of teeth",
                    "B. Size, shape, arrangement, and condition of teeth involved",
                    "C. Only the color of teeth",
                    "D. Only the age of teeth"
                ],
                "correct": 1,
                "explanation": "The pattern reflects the size, shape, arrangement, and condition of the teeth involved in the biting action."
            },
            {
                "question": "What information may bite marks provide in forensic odontology?",
                "options": [
                    "A. Only the time of death",
                    "B. Identity of biter, nature of assault, and circumstances of crime",
                    "C. Only the victim's age",
                    "D. Only the location of crime"
                ],
                "correct": 1,
                "explanation": "Bite marks may provide information about the identity of the biter, nature of assault, and circumstances of crime."
            },
            {
                "question": "What is the underlying principle behind bite mark identification?",
                "options": [
                    "A. All humans have identical teeth",
                    "B. Human dentition exhibits variations in morphology and alignment",
                    "C. Teeth never change over time",
                    "D. Bite marks are always perfectly preserved"
                ],
                "correct": 1,
                "explanation": "The underlying principle is that human dentition exhibits variations in morphology and alignment, producing distinctive patterns."
            },
            {
                "question": "What does modern forensic science emphasize about bite mark interpretation?",
                "options": [
                    "A. It can uniquely identify anyone",
                    "B. It must be interpreted with caution due to biological variability and distortion",
                    "C. It is more reliable than DNA",
                    "D. It never needs supporting evidence"
                ],
                "correct": 1,
                "explanation": "Modern forensic science emphasizes that bite mark evidence must be interpreted with caution due to biological variability and potential distortion."
            },
            {
                "question": "Which of the following is NOT listed as an example of a patterned injury in the document?",
                "options": [
                    "A. Tire tread marks",
                    "B. Weapon impressions",
                    "C. Fingerprint patterns",
                    "D. Ligature marks"
                ],
                "correct": 2,
                "explanation": "The document lists tire tread marks, weapon impressions, ligature marks, and tool marks as examples of patterned injuries. Fingerprints are a different category."
            },
            {
                "question": "How does a typical human bite mark present?",
                "options": [
                    "A. As a straight line of punctures",
                    "B. As a circular or elliptical pattern with two opposing semicircular arches",
                    "C. As a random pattern of bruises",
                    "D. As a single arch only"
                ],
                "correct": 1,
                "explanation": "A typical human bite mark presents as a circular or elliptical pattern composed of two opposing semicircular arches representing upper and lower dental arches."
            },
            {
                "question": "What type of marks do canines typically produce?",
                "options": [
                    "A. Rectangular marks",
                    "B. Linear scratches",
                    "C. Deeper puncture or triangular marks",
                    "D. Circular impressions"
                ],
                "correct": 2,
                "explanation": "Canines produce deeper puncture or triangular marks, while incisors produce rectangular or linear marks."
            },
            {
                "question": "What are the three types of biting force described in the document?",
                "options": [
                    "A. Light, medium, heavy",
                    "B. Pressure bites, drag bites, avulsive bites",
                    "C. Fast, slow, moderate",
                    "D. Incisal, canine, molar"
                ],
                "correct": 1,
                "explanation": "The three types are pressure bites (teeth pressing without movement), drag bites (teeth moving across skin), and avulsive bites (tearing/removal of tissue)."
            },
            {
                "question": "Greater biting force may result in:",
                "options": [
                    "A. Only superficial redness",
                    "B. Bruising, skin tearing, and tissue removal",
                    "C. Only swelling",
                    "D. Only discoloration"
                ],
                "correct": 1,
                "explanation": "Greater force may result in bruising, skin tearing, and tissue removal."
            },
            {
                "question": "Which food items are mentioned as preserving clearer dental impressions?",
                "options": [
                    "A. Bread, rice, pasta",
                    "B. Cheese, chocolate, apples, gum",
                    "C. Meat, vegetables, soup",
                    "D. Liquid foods only"
                ],
                "correct": 1,
                "explanation": "The document mentions cheese, chocolate, apples, and gum as food materials that preserve clearer dental impressions."
            },
            {
                "question": "What properties of human skin affect bite mark appearance?",
                "options": [
                    "A. Only color",
                    "B. Elastic, flexible, easily distorted, changes over time",
                    "C. Only thickness",
                    "D. Only hair coverage"
                ],
                "correct": 1,
                "explanation": "Human skin is elastic and flexible, easily distorted, and changes over time due to swelling or healing."
            },
            {
                "question": "How can bite marks serve as associative evidence?",
                "options": [
                    "A. By proving guilt beyond doubt",
                    "B. By linking a suspect to a victim or object",
                    "C. By determining exact time of crime",
                    "D. By establishing motive"
                ],
                "correct": 1,
                "explanation": "Bite marks may serve as associative evidence, linking a suspect to a victim or object through bites on victims or objects at crime scenes."
            },
            {
                "question": "Bite marks on breasts or thighs are often associated with:",
                "options": [
                    "A. Sports injuries",
                    "B. Sexual assault",
                    "C. Accidental falls",
                    "D. Medical procedures"
                ],
                "correct": 1,
                "explanation": "Bite marks on breasts or thighs are often associated with sexual assault."
            },
            {
                "question": "In which types of crimes do bite marks frequently appear?",
                "options": [
                    "A. Property crimes only",
                    "B. Crimes involving close physical contact",
                    "C. Financial crimes",
                    "D. Cyber crimes"
                ],
                "correct": 1,
                "explanation": "Bite marks frequently appear in crimes involving close physical contact between offender and victim."
            },
            
            # ============================================================================
            # SECTION 2: CRIME-SPECIFIC BITE MARK LOCATIONS (Questions 16-25)
            # ============================================================================
            {
                "question": "In homicide cases, where may bite marks appear?",
                "options": [
                    "A. Only on hands",
                    "B. Face, neck, breasts, arms",
                    "C. Only on legs",
                    "D. Only on back"
                ],
                "correct": 1,
                "explanation": "In homicide cases, bite marks may appear on face, neck, breasts, and arms."
            },
            {
                "question": "In homicide cases, bite marks may result from:",
                "options": [
                    "A. Only self-defense",
                    "B. Aggression, control of victim, sexual motives",
                    "C. Only accident",
                    "D. Only medical treatment"
                ],
                "correct": 1,
                "explanation": "These marks may result from aggression, control of the victim, or sexual motives."
            },
            {
                "question": "Typical bite mark locations in sexual assault cases include:",
                "options": [
                    "A. Hands and feet",
                    "B. Breasts, abdomen, thighs, genital areas",
                    "C. Back and shoulders",
                    "D. Face only"
                ],
                "correct": 1,
                "explanation": "Typical locations include breasts, abdomen, thighs, and genital areas."
            },
            {
                "question": "Bite marks in sexual assault may indicate:",
                "options": [
                    "A. Accidental contact",
                    "B. Sexual aggression, dominance behavior, attempt to restrain",
                    "C. Medical examination",
                    "D. Self-inflicted injury"
                ],
                "correct": 1,
                "explanation": "They may indicate sexual aggression, dominance behavior, or attempt to restrain the victim."
            },
            {
                "question": "In child abuse cases, where are bite marks commonly found?",
                "options": [
                    "A. Only on face",
                    "B. Arms, cheeks, back, buttocks",
                    "C. Only on legs",
                    "D. Only on abdomen"
                ],
                "correct": 1,
                "explanation": "In child abuse cases, bite marks may be found on arms, cheeks, back, and buttocks."
            },
            {
                "question": "Bite marks on children may be inflicted by:",
                "options": [
                    "A. Only strangers",
                    "B. Adults or other children",
                    "C. Only other children",
                    "D. Only caregivers"
                ],
                "correct": 1,
                "explanation": "Bite marks on children may be inflicted by adults or other children."
            },
            {
                "question": "What helps distinguish adult bites from child bites?",
                "options": [
                    "A. Tooth color",
                    "B. Measurement of bite marks",
                    "C. Bite location",
                    "D. Time of day"
                ],
                "correct": 1,
                "explanation": "Measurement of bite marks can sometimes help distinguish adult bites from child bites."
            },
            {
                "question": "In domestic violence, bite marks are often found on:",
                "options": [
                    "A. Back and chest",
                    "B. Arms, shoulders, hands",
                    "C. Feet and ankles",
                    "D. Head only"
                ],
                "correct": 1,
                "explanation": "These injuries are often found on arms, shoulders, and hands."
            },
            {
                "question": "Bite marks in domestic violence may represent:",
                "options": [
                    "A. Aggression by the abuser",
                    "B. Defensive biting by the victim",
                    "C. Accidental injuries",
                    "D. Self-harm"
                ],
                "correct": 1,
                "explanation": "They may represent defensive biting by the victim during physical fights."
            },
            {
                "question": "According to the document, what percentage of abused children may have bite marks?",
                "options": [
                    "A. Less than 1%",
                    "B. The document doesn't specify a percentage, but emphasizes they are significant findings",
                    "C. 50%",
                    "D. 100%"
                ],
                "correct": 1,
                "explanation": "The document doesn't specify a percentage, but emphasizes bite marks as significant findings in abuse cases."
            },
            
            # ============================================================================
            # SECTION 3: DENTAL CHARACTERISTICS (Questions 26-35)
            # ============================================================================
            {
                "question": "How do larger incisors affect bite marks?",
                "options": [
                    "A. They leave no marks",
                    "B. They may produce broader marks",
                    "C. They produce deeper punctures only",
                    "D. They produce triangular marks"
                ],
                "correct": 1,
                "explanation": "Larger incisors may produce broader marks, while smaller teeth may leave narrow impressions."
            },
            {
                "question": "What are examples of irregular alignment that affect bite marks?",
                "options": [
                    "A. Perfectly straight teeth",
                    "B. Crowded teeth, protruding teeth, rotated teeth",
                    "C. Evenly spaced teeth",
                    "D. Identical tooth sizes"
                ],
                "correct": 1,
                "explanation": "Examples include crowded teeth, protruding teeth, and rotated teeth, which influence shape and spacing of the bite mark pattern."
            },
            {
                "question": "What is the definition of diastema?",
                "options": [
                    "A. Tooth decay",
                    "B. Spacing or gap between teeth",
                    "C. Dental restoration",
                    "D. Tooth fracture"
                ],
                "correct": 1,
                "explanation": "Diastema is spacing or a gap between teeth, which may create gaps in the bite mark pattern."
            },
            {
                "question": "A gap between central incisors may appear as what in a bite mark?",
                "options": [
                    "A. Deeper puncture",
                    "B. Space in the bite impression",
                    "C. Darker bruise",
                    "D. Multiple marks"
                ],
                "correct": 1,
                "explanation": "A gap between central incisors (diastema) may appear as a space in the bite impression."
            },
            {
                "question": "How does a missing tooth affect the bite mark pattern?",
                "options": [
                    "A. Creates deeper marks",
                    "B. Shows absence of corresponding tooth mark and asymmetry",
                    "C. Has no effect",
                    "D. Creates additional marks"
                ],
                "correct": 1,
                "explanation": "The bite mark pattern may show absence of a corresponding tooth mark and asymmetry in the dental arch pattern."
            },
            {
                "question": "Which are examples of dental restorations mentioned?",
                "options": [
                    "A. Tooth brushing and flossing",
                    "B. Fillings, crowns, bridges",
                    "C. Fluoride treatment",
                    "D. Teeth whitening"
                ],
                "correct": 1,
                "explanation": "Examples include fillings, crowns, bridges, fractured teeth, and chipped enamel."
            },
            {
                "question": "How do dental restorations affect bite marks?",
                "options": [
                    "A. They have no effect",
                    "B. They may create irregularities in the bite mark",
                    "C. They always make marks clearer",
                    "D. They prevent bite marks"
                ],
                "correct": 1,
                "explanation": "Dental restorations can alter tooth shape and may create irregularities in the bite mark."
            },
            {
                "question": "What did forensic odontologists historically believe about bite marks?",
                "options": [
                    "A. They were useless for identification",
                    "B. They could uniquely identify individuals due to dentition variability",
                    "C. They were only useful for age estimation",
                    "D. They were less reliable than shoe prints"
                ],
                "correct": 1,
                "explanation": "Historically, forensic odontologists believed bite marks could uniquely identify individuals due to the variability of dentition."
            },
            {
                "question": "What has current scientific research shown about bite marks?",
                "options": [
                    "A. They are 100% reliable",
                    "B. Skin distortion may alter pattern, marks change over time, different individuals may produce similar patterns",
                    "C. They are more reliable than fingerprints",
                    "D. They never change"
                ],
                "correct": 1,
                "explanation": "Current research shows skin distortion may alter the pattern, bite marks may change over time, and different individuals may produce similar patterns."
            },
            {
                "question": "How do most modern experts consider bite mark analysis?",
                "options": [
                    "A. As definitive evidence",
                    "B. As supportive rather than definitive evidence",
                    "C. As completely useless",
                    "D. As the gold standard"
                ],
                "correct": 1,
                "explanation": "Most modern experts consider bite mark analysis to be supportive rather than definitive evidence."
            },
            
            # ============================================================================
            # SECTION 4: LIMITATIONS (Questions 36-45)
            # ============================================================================
            {
                "question": "How does skin elasticity affect bite marks?",
                "options": [
                    "A. It preserves marks perfectly",
                    "B. It can stretch and distort the original bite pattern",
                    "C. It has no effect",
                    "D. It makes marks deeper"
                ],
                "correct": 1,
                "explanation": "Human skin can stretch and distort the original bite pattern due to its elasticity."
            },
            {
                "question": "How can movement during biting affect the bite mark?",
                "options": [
                    "A. It always improves clarity",
                    "B. Victim or attacker movement may distort the mark",
                    "C. It has no effect",
                    "D. It prevents bruising"
                ],
                "correct": 1,
                "explanation": "Victim or attacker movement during the bite may distort the mark."
            },
            {
                "question": "Bite marks may evolve over time due to:",
                "options": [
                    "A. Only weather",
                    "B. Swelling, bruising, tissue repair",
                    "C. Only victim age",
                    "D. Only suspect actions"
                ],
                "correct": 1,
                "explanation": "Bite marks may evolve due to swelling, bruising, and tissue repair over time."
            },
            {
                "question": "What environmental factors can alter bite mark appearance?",
                "options": [
                    "A. Only rain",
                    "B. Temperature, decomposition, postmortem changes",
                    "C. Only sunlight",
                    "D. Only humidity"
                ],
                "correct": 1,
                "explanation": "Temperature, decomposition, and postmortem changes can alter the appearance of bite marks."
            },
            {
                "question": "Complete this sentence from the document: 'A bite mark is a ______ injury produced by the contact of teeth with skin or other materials.'",
                "options": [
                    "A. random",
                    "B. patterned",
                    "C. deep",
                    "D. superficial"
                ],
                "correct": 1,
                "explanation": "The document states: 'A bite mark is a patterned injury produced by the contact of teeth with skin or other materials.'"
            },
            {
                "question": "What elements are compared in bite mark analysis?",
                "options": [
                    "A. Victim and suspect height",
                    "B. Bite marks with suspect's dentition including tooth size, alignment, spacing, missing teeth, restorations",
                    "C. Time of injury and suspect alibi",
                    "D. Location and weather"
                ],
                "correct": 1,
                "explanation": "Comparison involves evaluating arch width, tooth position, tooth rotation, spacing patterns, and individual characteristics."
            },
            {
                "question": "What additional forensic evidence should support bite mark interpretation?",
                "options": [
                    "A. No additional evidence needed",
                    "B. DNA analysis",
                    "C. Only witness statements",
                    "D. Only suspect confession"
                ],
                "correct": 1,
                "explanation": "Bite mark interpretation must be supported by additional forensic evidence such as DNA analysis."
            },
            {
                "question": "How many categories of limitations are listed in the document?",
                "options": [
                    "A. 2",
                    "B. 4 (Skin elasticity, movement, healing, environmental)",
                    "C. 6",
                    "D. 10"
                ],
                "correct": 1,
                "explanation": "The document lists four main limitations: skin elasticity, movement during bite, healing changes, and environmental factors."
            },
            {
                "question": "How does decomposition affect bite marks?",
                "options": [
                    "A. Preserves them permanently",
                    "B. Can alter the appearance of bite marks",
                    "C. Makes them more visible",
                    "D. Has no effect"
                ],
                "correct": 1,
                "explanation": "Decomposition and postmortem changes can alter the appearance of bite marks."
            },
            {
                "question": "What effect does swelling have on bite marks?",
                "options": [
                    "A. Makes patterns clearer",
                    "B. Can distort the original bite pattern",
                    "C. Has no effect",
                    "D. Prevents bruising"
                ],
                "correct": 1,
                "explanation": "Soft tissue swelling may distort the original bite pattern."
            },
            
            # ============================================================================
            # SECTION 5: CLASSIFICATION BY INJURY TYPE (Questions 46-60)
            # ============================================================================
            {
                "question": "What are the characteristics of an abrasion bite mark?",
                "options": [
                    "A. Deep puncture wounds",
                    "B. Reddish scrape, superficial, follows tooth outline",
                    "C. Missing tissue",
                    "D. Clean cut edges"
                ],
                "correct": 1,
                "explanation": "Abrasion appears as a reddish scrape or superficial mark, often following the outline of teeth."
            },
            {
                "question": "How does an abrasion bite mark occur?",
                "options": [
                    "A. Teeth penetrate deeply",
                    "B. Teeth slide across skin surface, scraping away epidermis",
                    "C. Tissue is torn away",
                    "D. Blood vessels rupture beneath skin"
                ],
                "correct": 1,
                "explanation": "Abrasion occurs when teeth slide across the skin surface, scraping away the epidermis."
            },
            {
                "question": "What are the characteristics of a contusion bite mark?",
                "options": [
                    "A. Open wound with bleeding",
                    "B. Bluish, reddish, or purple discoloration with intact skin",
                    "C. Missing tissue",
                    "D. Clean cut edges"
                ],
                "correct": 1,
                "explanation": "Contusion shows bluish, reddish, or purple discoloration with skin remaining intact."
            },
            {
                "question": "How does a contusion bite mark occur?",
                "options": [
                    "A. Teeth cut the skin",
                    "B. Pressure compresses tissue, rupturing blood vessels beneath skin",
                    "C. Tissue is torn away",
                    "D. Teeth scrape the surface"
                ],
                "correct": 1,
                "explanation": "Pressure from teeth compresses tissue, causing blood vessels to rupture and leak into surrounding tissue."
            },
            {
                "question": "What are the characteristics of a laceration bite mark?",
                "options": [
                    "A. Superficial redness",
                    "B. Irregular wound edges, bleeding, possible deep tissue damage",
                    "C. Only discoloration",
                    "D. Smooth edges"
                ],
                "correct": 1,
                "explanation": "Laceration shows irregular wound edges, bleeding, and possible deep tissue damage."
            },
            {
                "question": "When do laceration bite marks occur?",
                "options": [
                    "A. Light pressure",
                    "B. Teeth penetrate or tear skin due to excessive biting force",
                    "C. Sliding movement only",
                    "D. No force applied"
                ],
                "correct": 1,
                "explanation": "Laceration occurs when teeth penetrate or tear the skin due to excessive biting force."
            },
            {
                "question": "What are the characteristics of an incised bite wound?",
                "options": [
                    "A. Ragged edges",
                    "B. Relatively clean wound margins following shape of incisors",
                    "C. Bruising only",
                    "D. Missing tissue"
                ],
                "correct": 1,
                "explanation": "Incised wounds show relatively clean wound margins that may follow the shape of incisors."
            },
            {
                "question": "Where are avulsion injuries commonly located?",
                "options": [
                    "A. Back and chest",
                    "B. Ear, nose, lips, fingers",
                    "C. Arms only",
                    "D. Legs only"
                ],
                "correct": 1,
                "explanation": "Common locations for avulsion injuries include ear, nose, lips, and fingers."
            },
            {
                "question": "How do avulsion injuries occur?",
                "options": [
                    "A. Light pressure",
                    "B. Strong bite force combined with pulling or tearing motion",
                    "C. Static pressure only",
                    "D. Gradual pressure"
                ],
                "correct": 1,
                "explanation": "Avulsion occurs from strong bite force combined with pulling or tearing motion."
            },
            {
                "question": "What is the forensic significance of avulsion injuries?",
                "options": [
                    "A. They are not significant",
                    "B. Often associated with extreme violence, tissue may contain saliva for DNA",
                    "C. Always self-inflicted",
                    "D. Easy to analyze"
                ],
                "correct": 1,
                "explanation": "Avulsion injuries are often associated with extreme violence and the removed tissue may contain saliva for DNA analysis."
            },
            {
                "question": "What are the three classifications based on mechanism of biting?",
                "options": [
                    "A. Light, medium, heavy",
                    "B. Pressure bite, drag bite, avulsive bite",
                    "C. Fast, slow, moderate",
                    "D. Upper, lower, both"
                ],
                "correct": 1,
                "explanation": "The three types are pressure bite, drag bite, and avulsive bite."
            },
            {
                "question": "What are the characteristics of a pressure bite?",
                "options": [
                    "A. Distorted patterns",
                    "B. Clear tooth impressions, minimal distortion, often symmetrical",
                    "C. Missing tissue",
                    "D. Smearing of marks"
                ],
                "correct": 1,
                "explanation": "Pressure bite shows clear tooth impressions, minimal distortion, and is often symmetrical."
            },
            {
                "question": "What are the characteristics of a drag bite?",
                "options": [
                    "A. Clear impressions",
                    "B. Smearing or dragging of tooth marks, distorted patterns, elongated abrasions",
                    "C. Perfect patterns",
                    "D. Deep punctures only"
                ],
                "correct": 1,
                "explanation": "Drag bite shows smearing or dragging of tooth marks, distorted patterns, and elongated abrasions."
            },
            {
                "question": "What causes a drag bite?",
                "options": [
                    "A. Static pressure",
                    "B. Movement of victim or attacker during biting",
                    "C. Tearing motion only",
                    "D. Biting hard objects"
                ],
                "correct": 1,
                "explanation": "Drag bite occurs due to movement of the victim or attacker during biting."
            },
            {
                "question": "What characterizes an avulsive bite?",
                "options": [
                    "A. Superficial marks",
                    "B. Missing tissue and deep injuries from pulling action",
                    "C. Clear impressions",
                    "D. Symmetrical patterns"
                ],
                "correct": 1,
                "explanation": "Avulsive bite involves missing tissue and deep injuries due to pulling action."
            },
            
            # ============================================================================
            # SECTION 6: CLASSIFICATION BY CLARITY AND SOURCE (Questions 61-70)
            # ============================================================================
            {
                "question": "What features does a definite bite mark demonstrate?",
                "options": [
                    "A. Partial pattern only",
                    "B. Circular/oval pattern, two opposing arches, individual tooth impressions visible",
                    "C. Bruise only",
                    "D. Single arch only"
                ],
                "correct": 1,
                "explanation": "A definite bite mark clearly shows circular/oval pattern, two opposing arches, and individual tooth impressions."
            },
            {
                "question": "What does a possible bite mark show?",
                "options": [
                    "A. Complete pattern",
                    "B. Some features consistent with biting, but incomplete pattern",
                    "C. No dental features",
                    "D. Perfect tooth impressions"
                ],
                "correct": 1,
                "explanation": "A possible bite mark shows some features consistent with biting, but the pattern is incomplete."
            },
            {
                "question": "What is a questionable bite mark?",
                "options": [
                    "A. Clear bite pattern",
                    "B. Injury that may resemble a bite but lacks clear dental characteristics",
                    "C. Animal bite",
                    "D. Fresh bite"
                ],
                "correct": 1,
                "explanation": "A questionable bite mark is an injury that may resemble a bite but lacks clear dental characteristics."
            },
            {
                "question": "What are examples of questionable bite marks?",
                "options": [
                    "A. Clear tooth impressions",
                    "B. Bruises resembling bite patterns, injuries caused by objects",
                    "C. Two opposing arches",
                    "D. Individual tooth marks"
                ],
                "correct": 1,
                "explanation": "Examples include bruises resembling bite patterns and injuries caused by objects."
            },
            {
                "question": "What pattern do human bites usually show?",
                "options": [
                    "A. Random punctures",
                    "B. Oval/circular pattern with two semicircular arches from incisors and canines",
                    "C. Single line of marks",
                    "D. Deep tears only"
                ],
                "correct": 1,
                "explanation": "Human bites usually show oval/circular pattern with two semicircular arches from incisors and canines."
            },
            {
                "question": "What is the forensic importance of distinguishing human from animal bites?",
                "options": [
                    "A. Not important",
                    "B. Must distinguish animal bites from human bite marks for proper investigation",
                    "C. Only for curiosity",
                    "D. Only for medical treatment"
                ],
                "correct": 1,
                "explanation": "It is forensically important to distinguish animal bites from human bite marks."
            },
            {
                "question": "What are the classifications based on material bitten?",
                "options": [
                    "A. Only skin",
                    "B. Skin, food, inanimate objects",
                    "C. Only food",
                    "D. Only objects"
                ],
                "correct": 1,
                "explanation": "Classifications include bite marks on skin, on food, and on inanimate objects."
            },
            {
                "question": "What advantage do food bite marks have over skin bite marks?",
                "options": [
                    "A. They are less common",
                    "B. Less distortion than skin, clearer tooth impressions",
                    "C. They last longer",
                    "D. They are easier to photograph"
                ],
                "correct": 1,
                "explanation": "Food bite marks have less distortion than skin and provide clearer tooth impressions."
            },
            {
                "question": "What are examples of inanimate objects that may retain bite marks?",
                "options": [
                    "A. Only metal objects",
                    "B. Pencils, plastic cups, pens, Styrofoam containers",
                    "C. Only paper",
                    "D. Only glass"
                ],
                "correct": 1,
                "explanation": "Examples include pencils, plastic cups, pens, and Styrofoam containers."
            },
            {
                "question": "What are the classifications based on age of bite mark?",
                "options": [
                    "A. New and old only",
                    "B. Fresh, healing, old",
                    "C. Recent and ancient",
                    "D. Modern and historic"
                ],
                "correct": 1,
                "explanation": "Classifications based on age include fresh, healing, and old bite marks."
            },
            
            # ============================================================================
            # SECTION 7: DOCUMENTATION (Questions 71-85)
            # ============================================================================
            {
                "question": "Why is proper bite mark documentation one of the most important steps?",
                "options": [
                    "A. Because it's required by law",
                    "B. Because bite marks can fade or distort within hours",
                    "C. Because it's easy to do",
                    "D. Because suspects always leave marks"
                ],
                "correct": 1,
                "explanation": "Proper documentation preserves the original appearance of the injury, which may change rapidly due to biological processes."
            },
            {
                "question": "When must bite mark documentation be performed?",
                "options": [
                    "A. Within one week",
                    "B. As soon as possible after discovery",
                    "C. After suspect is caught",
                    "D. Before trial"
                ],
                "correct": 1,
                "explanation": "Documentation must be performed as soon as possible after discovery because bite marks can fade or distort within hours."
            },
            {
                "question": "Which organization provides professional guidelines for bite mark documentation?",
                "options": [
                    "A. FBI",
                    "B. American Board of Forensic Odontology (ABFO)",
                    "C. World Health Organization",
                    "D. American Medical Association"
                ],
                "correct": 1,
                "explanation": "Professional guidelines are commonly provided by the American Board of Forensic Odontology (ABFO)."
            },
            {
                "question": "How many forensic purposes of documentation are listed?",
                "options": [
                    "A. 2",
                    "B. 4 (preservation, comparison, courtroom evidence, scientific analysis)",
                    "C. 6",
                    "D. 8"
                ],
                "correct": 1,
                "explanation": "The four purposes are preservation of evidence, facilitating forensic comparison, courtroom evidence, and scientific analysis."
            },
            {
                "question": "What is the typical bruise color progression?",
                "options": [
                    "A. Blue, green, yellow, red",
                    "B. Red, blue/purple, green, yellow, brown",
                    "C. Yellow, green, blue, purple",
                    "D. Purple, blue, green, yellow"
                ],
                "correct": 1,
                "explanation": "Typical progression: red, blue/purple, green, yellow, then brown due to breakdown of blood pigments."
            },
            {
                "question": "What are the main components of bite mark documentation?",
                "options": [
                    "A. Only photographs",
                    "B. Photography, impression taking, DNA collection, recording suspect dentition",
                    "C. Only DNA",
                    "D. Only impressions"
                ],
                "correct": 1,
                "explanation": "Proper documentation includes photography, impression taking, DNA collection, and recording suspect dentition."
            },
            {
                "question": "What is the purpose of overall photographs?",
                "options": [
                    "A. Show tooth details",
                    "B. Show location of bite mark on the body with anatomical context",
                    "C. Show bruise color",
                    "D. Show measurement only"
                ],
                "correct": 1,
                "explanation": "Overall photographs show the location of the bite mark on the body with surrounding anatomical structures visible."
            },
            {
                "question": "What is the purpose of close-up photographs?",
                "options": [
                    "A. Show entire body",
                    "B. Capture fine details of bite mark pattern with individual tooth marks visible",
                    "C. Show suspect only",
                    "D. Show crime scene"
                ],
                "correct": 1,
                "explanation": "Close-up photographs capture fine details of the bite mark pattern with individual tooth marks visible."
            },
            {
                "question": "What does the ABFO No. 2 scale include?",
                "options": [
                    "A. Only numbers",
                    "B. Metric markings, right-angle reference markers, color calibration markers",
                    "C. Only colors",
                    "D. Only measurements"
                ],
                "correct": 1,
                "explanation": "The ABFO No. 2 scale includes metric measurement markings, right-angle reference markers, and color calibration markers."
            },
            {
                "question": "Why must the camera be perpendicular to the bite mark?",
                "options": [
                    "A. For better lighting",
                    "B. To prevent distortion and ensure accurate measurements",
                    "C. For easier photography",
                    "D. To show color better"
                ],
                "correct": 1,
                "explanation": "The camera must be perpendicular (90°) to prevent distortion and ensure accurate measurements."
            },
            {
                "question": "What lighting methods are mentioned for bite mark photography?",
                "options": [
                    "A. Only natural light",
                    "B. Direct lighting, oblique lighting, alternate light sources",
                    "C. Only flash",
                    "D. Only room light"
                ],
                "correct": 1,
                "explanation": "Methods include direct lighting, oblique lighting (angled light), and alternate light sources."
            },
            {
                "question": "Why should bite marks be photographed multiple times over several days?",
                "options": [
                    "A. For practice",
                    "B. To monitor changes in bruising and capture evolving patterns",
                    "C. Because cameras fail",
                    "D. For artistic purposes"
                ],
                "correct": 1,
                "explanation": "Repeated photography monitors changes in bruising and captures evolving patterns over time."
            },
            {
                "question": "What are the two main impression materials mentioned?",
                "options": [
                    "A. Clay and wax",
                    "B. Silicone impression material and dental alginate",
                    "C. Plaster and cement",
                    "D. Rubber and plastic"
                ],
                "correct": 1,
                "explanation": "The main materials are silicone impression material and dental alginate."
            },
            {
                "question": "What is the limitation of dental alginate?",
                "options": [
                    "A. It's too expensive",
                    "B. It must be cast quickly because it can shrink over time",
                    "C. It's not accurate",
                    "D. It's difficult to use"
                ],
                "correct": 1,
                "explanation": "Alginate must be cast quickly because it can shrink over time."
            },
            {
                "question": "What are the general steps for impression taking?",
                "options": [
                    "A. Only apply material",
                    "B. Clean area, apply material, allow to set, remove gently, create cast",
                    "C. Only create cast",
                    "D. Only remove material"
                ],
                "correct": 1,
                "explanation": "Steps: clean area, apply material, allow to set, remove gently, create plaster or dental stone cast."
            },
            
            # ============================================================================
            # SECTION 8: DNA AND ADDITIONAL METHODS (Questions 86-95)
            # ============================================================================
            {
                "question": "What is the standard DNA collection procedure?",
                "options": [
                    "A. Use dry swab only",
                    "B. Sterile cotton swabs, slightly moisten with sterile water, swab area, collect control swabs, air-dry, package sterile",
                    "C. Use any swab available",
                    "D. Collect only visible saliva"
                ],
                "correct": 1,
                "explanation": "Standard procedure: sterile cotton swabs slightly moistened with sterile water, swab area, collect control swabs, air-dry, package sterile."
            },
            {
                "question": "What DNA analysis methods are mentioned?",
                "options": [
                    "A. Only microscope",
                    "B. Polymerase Chain Reaction (PCR) and DNA profiling techniques",
                    "C. Only blood typing",
                    "D. Only visual inspection"
                ],
                "correct": 1,
                "explanation": "DNA can be analyzed using Polymerase Chain Reaction (PCR) and DNA profiling techniques."
            },
            {
                "question": "How does DNA analysis compare to bite mark analysis?",
                "options": [
                    "A. Less accurate",
                    "B. More reliable with high scientific accuracy",
                    "C. Same accuracy",
                    "D. Not useful"
                ],
                "correct": 1,
                "explanation": "DNA analysis may identify or exclude a suspect with high scientific accuracy."
            },
            {
                "question": "What materials are used for suspect dental impressions?",
                "options": [
                    "A. Only wax",
                    "B. Dental alginate and silicone impression materials",
                    "C. Only clay",
                    "D. Only plaster"
                ],
                "correct": 1,
                "explanation": "Materials include dental alginate and silicone impression materials."
            },
            {
                "question": "What modern technologies may be used in forensic dentistry?",
                "options": [
                    "A. Only photographs",
                    "B. 3D scanning, digital dental models, computer-assisted comparisons",
                    "C. Only hand tracing",
                    "D. Only microscopes"
                ],
                "correct": 1,
                "explanation": "Modern methods may use 3D scanning, digital dental models, and computer-assisted comparisons."
            },
            {
                "question": "What can ultraviolet photography reveal?",
                "options": [
                    "A. Only surface details",
                    "B. Bite marks not visible under normal lighting",
                    "C. Only tooth color",
                    "D. Only age of bite"
                ],
                "correct": 1,
                "explanation": "UV light may reveal bite marks not visible under normal lighting."
            },
            {
                "question": "What can infrared photography help detect?",
                "options": [
                    "A. Only surface injuries",
                    "B. Subsurface bruising",
                    "C. Only tooth marks",
                    "D. Only saliva"
                ],
                "correct": 1,
                "explanation": "Infrared imaging may help detect subsurface bruising."
            },
            {
                "question": "What can alternate light sources enhance visibility of?",
                "options": [
                    "A. Only tooth marks",
                    "B. Bruising, saliva stains, surface injuries",
                    "C. Only bite pattern",
                    "D. Only swelling"
                ],
                "correct": 1,
                "explanation": "ALS may enhance visibility of bruising, saliva stains, and surface injuries."
            },
            {
                "question": "What do chain of custody records include?",
                "options": [
                    "A. Only date",
                    "B. Date collected, person collecting, storage details, transfers",
                    "C. Only suspect name",
                    "D. Only case number"
                ],
                "correct": 1,
                "explanation": "Chain of custody includes date of evidence collection, person collecting, storage details, and transfer of evidence."
            },
            {
                "question": "Why is chain of custody important?",
                "options": [
                    "A. For organization only",
                    "B. Ensures evidence is admissible in court",
                    "C. For police records only",
                    "D. For laboratory use only"
                ],
                "correct": 1,
                "explanation": "Chain of custody ensures evidence is admissible in court by maintaining legal integrity."
            },
            
            # ============================================================================
            # SECTION 9: ANALYSIS METHODS AND OVERLAYS (Questions 96-105)
            # ============================================================================
            {
                "question": "What are the objectives of bite mark analysis?",
                "options": [
                    "A. Only identify suspect",
                    "B. Determine if injury is bite mark, distinguish human/animal, adult/child, compare with suspect, evaluate likelihood",
                    "C. Only document injury",
                    "D. Only take photographs"
                ],
                "correct": 1,
                "explanation": "Objectives include determining if injury is bite mark, distinguishing human/animal, adult/child, comparing with suspect, and evaluating likelihood."
            },
            {
                "question": "What are possible conclusions from bite mark analysis?",
                "options": [
                    "A. Only guilty or not guilty",
                    "B. Exclusion of suspect, possible association, inconclusive findings",
                    "C. Only match or no match",
                    "D. Only positive identification"
                ],
                "correct": 1,
                "explanation": "Conclusions may include exclusion of suspect, possible association, or inconclusive findings."
            },
            {
                "question": "What does visual inspection evaluate?",
                "options": [
                    "A. Only bite location",
                    "B. Shape, pattern of tooth impressions, number of teeth, presence of two arches, tissue damage severity",
                    "C. Only bite size",
                    "D. Only victim age"
                ],
                "correct": 1,
                "explanation": "Visual inspection evaluates shape, pattern of tooth impressions, number of teeth, presence of two arches, and tissue damage severity."
            },
            {
                "question": "Why is intercanine distance measurement important?",
                "options": [
                    "A. Not important",
                    "B. Helps distinguish adult vs child bites and human vs animal bites",
                    "C. Only for documentation",
                    "D. Only for suspect comparison"
                ],
                "correct": 1,
                "explanation": "Intercanine distance helps distinguish adult vs child bites and human vs animal bites."
            },
            {
                "question": "What is the typical adult human intercanine distance range?",
                "options": [
                    "A. 20-25 mm",
                    "B. 30-45 mm",
                    "C. 50-60 mm",
                    "D. 10-15 mm"
                ],
                "correct": 1,
                "explanation": "Typical adult human intercanine distance is 30-45 mm."
            },
            {
                "question": "What is the typical child intercanine distance?",
                "options": [
                    "A. More than 40 mm",
                    "B. Less than 30 mm",
                    "C. 30-35 mm",
                    "D. 35-40 mm"
                ],
                "correct": 1,
                "explanation": "Child bites typically have intercanine distance less than 30 mm."
            },
            {
                "question": "What are the possible shapes of human dental arches?",
                "options": [
                    "A. Round, square, triangle",
                    "B. U-shaped, parabolic, V-shaped",
                    "C. Oval, circular, rectangular",
                    "D. Straight, curved, angled"
                ],
                "correct": 1,
                "explanation": "Human dental arches may be U-shaped, parabolic, or V-shaped."
            },
            {
                "question": "What is an overlay in bite mark comparison?",
                "options": [
                    "A. Photograph of bite",
                    "B. Representation of biting surfaces of suspect's teeth placed over bite mark photograph",
                    "C. Dental cast",
                    "D. Impression material"
                ],
                "correct": 1,
                "explanation": "An overlay is a representation of the biting surfaces of a suspect's teeth placed over a photograph of the bite mark."
            },
            {
                "question": "What is the hand tracing method procedure?",
                "options": [
                    "A. Draw on skin",
                    "B. Place acetate over dental cast, trace biting edges, superimpose on bite photograph",
                    "C. Use computer only",
                    "D. Photocopy cast"
                ],
                "correct": 1,
                "explanation": "Hand tracing: acetate sheet placed over cast, biting edges traced manually, tracing superimposed on bite photograph."
            },
            {
                "question": "What are advantages of computer-generated overlays?",
                "options": [
                    "A. Cheaper only",
                    "B. Higher precision, reproducibility, reduced human error",
                    "C. Faster only",
                    "D. Easier to use only"
                ],
                "correct": 1,
                "explanation": "Computer overlays offer higher precision, reproducibility, and reduced human error."
            },
            
            # ============================================================================
            # SECTION 10: CLASS VS INDIVIDUAL CHARACTERISTICS (Questions 106-112)
            # ============================================================================
            {
                "question": "What are class characteristics?",
                "options": [
                    "A. Features unique to one person",
                    "B. Features common among groups of individuals",
                    "C. Features that change daily",
                    "D. Features only in children"
                ],
                "correct": 1,
                "explanation": "Class characteristics are features common among groups of individuals."
            },
            {
                "question": "What are examples of class characteristics?",
                "options": [
                    "A. Chipped teeth",
                    "B. Arch shape and general tooth size",
                    "C. Rotated teeth",
                    "D. Missing teeth"
                ],
                "correct": 1,
                "explanation": "Class characteristics include arch shape (rounded, U-shaped) and general tooth size."
            },
            {
                "question": "What are individual characteristics?",
                "options": [
                    "A. Features common to all",
                    "B. Unique features of a person's dentition from natural variations, disease, trauma, or treatment",
                    "C. Features that never vary",
                    "D. Features only in adults"
                ],
                "correct": 1,
                "explanation": "Individual characteristics are unique features arising from natural variations, dental disease, trauma, or dental treatment."
            },
            {
                "question": "Which are examples of individual characteristics?",
                "options": [
                    "A. General arch shape",
                    "B. Missing teeth, rotated teeth, chipped/fractured teeth, dental restorations",
                    "C. Average tooth size",
                    "D. Typical incisor shape"
                ],
                "correct": 1,
                "explanation": "Individual characteristics include missing teeth, rotated teeth, chipped/fractured teeth, and dental restorations."
            },
            {
                "question": "How do rotated teeth affect bite marks?",
                "options": [
                    "A. No effect",
                    "B. May produce angled bite marks and irregular spacing patterns",
                    "C. Always produce clearer marks",
                    "D. Always produce deeper marks"
                ],
                "correct": 1,
                "explanation": "Rotated teeth may produce angled bite marks and irregular spacing patterns."
            },
            {
                "question": "How do chipped or fractured teeth affect bite marks?",
                "options": [
                    "A. No effect",
                    "B. May create irregular edge marks and distinctive bite patterns",
                    "C. Always make marks smaller",
                    "D. Always make marks deeper"
                ],
                "correct": 1,
                "explanation": "Chipped or fractured teeth may create irregular edge marks and distinctive bite patterns."
            },
            {
                "question": "How can dental restorations affect bite marks?",
                "options": [
                    "A. No effect",
                    "B. May produce distinctive bite patterns by modifying tooth shape",
                    "C. Always prevent bite marks",
                    "D. Only affect color"
                ],
                "correct": 1,
                "explanation": "Dental restorations like crowns, fillings, and bridges can modify tooth shape and produce distinctive bite patterns."
            },
            
            # ============================================================================
            # SECTION 11: CONTROVERSIES AND SCIENTIFIC REVIEWS (Questions 113-125)
            # ============================================================================
            {
                "question": "During what period was bite mark evidence widely used in criminal trials?",
                "options": [
                    "A. 1950s-1960s",
                    "B. 1970s-1990s",
                    "C. 2000s-present",
                    "D. 1920s-1940s"
                ],
                "correct": 1,
                "explanation": "During the 1970s-1990s, bite mark evidence was widely used in criminal trials."
            },
            {
                "question": "What did forensic odontologists often testify in the past?",
                "options": [
                    "A. Bite marks were useless",
                    "B. Bite marks could uniquely identify an individual, similar to fingerprints",
                    "C. Bite marks only showed animal bites",
                    "D. Bite marks never matched anyone"
                ],
                "correct": 1,
                "explanation": "Forensic odontologists often testified that bite marks could uniquely identify an individual, similar to fingerprints."
            },
            {
                "question": "What questions did later scientific reviews raise?",
                "options": [
                    "A. Only about cost",
                    "B. Whether dentition is truly unique, whether skin reliably records tooth patterns, whether experts consistently interpret",
                    "C. Only about time required",
                    "D. Only about equipment"
                ],
                "correct": 1,
                "explanation": "Reviews questioned whether dentition is truly unique, whether skin can reliably record tooth patterns, and whether experts can consistently interpret."
            },
            {
                "question": "What factors cause skin distortion?",
                "options": [
                    "A. Only victim movement",
                    "B. Body movement, skin elasticity, swelling, healing processes, angle of bite",
                    "C. Only attacker movement",
                    "D. Only time of day"
                ],
                "correct": 1,
                "explanation": "Factors include body movement, skin elasticity, swelling, healing processes, and angle of the bite."
            },
            {
                "question": "How does swelling affect bite marks?",
                "options": [
                    "A. Makes patterns clearer",
                    "B. May distort pattern, expand distance between marks, obscure tooth details",
                    "C. No effect",
                    "D. Preserves marks permanently"
                ],
                "correct": 1,
                "explanation": "Swelling may distort the bite mark pattern, expand distance between marks, and obscure tooth details."
            },
            {
                "question": "How does the angle of bite affect the pattern?",
                "options": [
                    "A. No effect",
                    "B. Marks may be compressed, elongated, or distorted",
                    "C. Always improves clarity",
                    "D. Only affects color"
                ],
                "correct": 1,
                "explanation": "If the bite occurs at an angle, resulting marks may be compressed, elongated, or distorted."
            },
            {
                "question": "What is confirmation bias?",
                "options": [
                    "A. Confirming DNA results",
                    "B. Expert unconsciously interpreting evidence to support expected conclusion",
                    "C. Confirming with other experts",
                    "D. Confirming suspect guilt"
                ],
                "correct": 1,
                "explanation": "Confirmation bias occurs when an expert unconsciously interprets evidence in a way that supports an expected conclusion."
            },
            {
                "question": "What year was the National Academy of Sciences report published?",
                "options": [
                    "A. 1999",
                    "B. 2009",
                    "C. 2019",
                    "D. 1989"
                ],
                "correct": 1,
                "explanation": "The National Academy of Sciences (NAS) published its landmark report in 2009."
            },
            {
                "question": "What was the title of the 2009 NAS report?",
                "options": [
                    "A. Forensic Science in America",
                    "B. Strengthening Forensic Science in the United States: A Path Forward",
                    "C. The Future of Forensics",
                    "D. Science and Justice"
                ],
                "correct": 1,
                "explanation": "The report was titled 'Strengthening Forensic Science in the United States: A Path Forward.'"
            },
            {
                "question": "What did the NAS report conclude about bite mark analysis?",
                "options": [
                    "A. It is highly reliable",
                    "B. Lacks sufficient scientific validation, uniqueness not proven, limited evidence for reliable comparison",
                    "C. Should be used exclusively",
                    "D. No issues identified"
                ],
                "correct": 1,
                "explanation": "The NAS report concluded bite mark analysis lacks sufficient scientific validation, uniqueness not proven, and limited evidence supports reliable comparison."
            },
            {
                "question": "What year was the President's Council of Advisors on Science and Technology (PCAST) report published?",
                "options": [
                    "A. 2009",
                    "B. 2016",
                    "C. 2010",
                    "D. 2020"
                ],
                "correct": 1,
                "explanation": "The PCAST report was published in 2016."
            },
            {
                "question": "What did the PCAST report conclude about bite mark analysis?",
                "options": [
                    "A. Meets scientific standards",
                    "B. Does not meet scientific standards for validity, no reliable evidence experts can consistently identify source, error rates unacceptably high",
                    "C. Should be expanded",
                    "D. Is more reliable than DNA"
                ],
                "correct": 1,
                "explanation": "PCAST concluded bite mark analysis does not meet scientific standards for validity, lacks reliable evidence for consistent identification, and has unacceptably high error rates."
            },
            {
                "question": "What is the current scientific perspective on bite mark evidence?",
                "options": [
                    "A. Use as sole evidence",
                    "B. Use with extreme caution, not as sole evidence, support with DNA, avoid absolute identification claims",
                    "C. Never use",
                    "D. Use for all cases"
                ],
                "correct": 1,
                "explanation": "Modern perspective: use with extreme caution, not as sole evidence, support with DNA, avoid claims of absolute identification."
            },
            
            # ============================================================================
            # SECTION 12: ABUSE RECOGNITION (Questions 126-135)
            # ============================================================================
            {
                "question": "What is the significance of a torn labial frenum in infants?",
                "options": [
                    "A. Normal finding",
                    "B. Highly suspicious for physical abuse, may indicate force-feeding or blunt trauma",
                    "C. Always accidental",
                    "D. Caused by teething"
                ],
                "correct": 1,
                "explanation": "Torn labial frenum in infants is highly suspicious for physical abuse, indicating force-feeding or blunt trauma."
            },
            {
                "question": "Lip lacerations and bruising are often associated with:",
                "options": [
                    "A. Normal childhood activity",
                    "B. Slapping or blunt facial trauma",
                    "C. Teething",
                    "D. Eating"
                ],
                "correct": 1,
                "explanation": "Lip lacerations/bruising are often associated with slapping or blunt facial trauma."
            },
            {
                "question": "Palatal bruising or burns may result from:",
                "options": [
                    "A. Hot food only",
                    "B. Forced feeding, hot objects, or abuse",
                    "C. Normal eating",
                    "D. Dental procedures"
                ],
                "correct": 1,
                "explanation": "Palatal injuries may result from forced feeding, hot objects, or abuse."
            },
            {
                "question": "Multiple oral injuries in different healing stages suggest:",
                "options": [
                    "A. Normal variation",
                    "B. Repeated trauma",
                    "C. Accident",
                    "D. Medical condition"
                ],
                "correct": 1,
                "explanation": "Multiple oral injuries in different healing stages suggest repeated trauma."
            },
            {
                "question": "Untreated rampant caries may indicate:",
                "options": [
                    "A. Good dental care",
                    "B. Possible indicator of dental neglect",
                    "C. Normal finding",
                    "D. Genetic condition"
                ],
                "correct": 1,
                "explanation": "Untreated rampant caries is a possible indicator of dental neglect."
            },
            {
                "question": "What are 'protected areas' rarely injured accidentally?",
                "options": [
                    "A. Hands and feet",
                    "B. Ears, neck, or inner mouth",
                    "C. Arms and legs",
                    "D. Chest and back"
                ],
                "correct": 1,
                "explanation": "Bruises on ears, neck, or inner mouth are 'protected areas' rarely injured accidentally."
            },
            {
                "question": "What is the key principle in abuse recognition?",
                "options": [
                    "A. Always believe patient",
                    "B. If history does not match clinical findings, abuse should be suspected",
                    "C. Never report without proof",
                    "D. Only report with witness"
                ],
                "correct": 1,
                "explanation": "Key principle: If the history does not match clinical findings, abuse should be suspected."
            },
            {
                "question": "How should patient statements be recorded in documentation?",
                "options": [
                    "A. Paraphrase",
                    "B. Use quotation marks",
                    "C. Summarize",
                    "D. Ignore"
                ],
                "correct": 1,
                "explanation": "Patient statements should be recorded using quotation marks for accuracy."
            },
            {
                "question": "How should injuries be described?",
                "options": [
                    "A. With assumptions",
                    "B. Objectively, e.g., '2 cm circular bruise on left cheek'",
                    "C. With blame",
                    "D. With speculation"
                ],
                "correct": 1,
                "explanation": "Injuries should be described objectively without assumptions, e.g., '2 cm circular bruise on left cheek'."
            },
            {
                "question": "What is required for reporting suspected abuse?",
                "options": [
                    "A. Proof beyond doubt",
                    "B. Reasonable suspicion, not proof",
                    "C. Witness statement",
                    "D. Confession"
                ],
                "correct": 1,
                "explanation": "Reporting requires reasonable suspicion, not proof."
            },
            
            # ============================================================================
            # SECTION 13: DISASTER VICTIM IDENTIFICATION (Questions 136-145)
            # ============================================================================
            {
                "question": "What is Disaster Victim Identification (DVI)?",
                "options": [
                    "A. Identifying criminals",
                    "B. Systematic process of identifying victims of mass fatality incidents using scientific methods",
                    "C. Treating disaster victims",
                    "D. Preventing disasters"
                ],
                "correct": 1,
                "explanation": "DVI is the systematic process of identifying victims of mass fatality incidents using scientific methods."
            },
            {
                "question": "What types of disasters are mentioned for DVI?",
                "options": [
                    "A. Only plane crashes",
                    "B. Natural disasters, transportation accidents, terrorist attacks, fires/explosions, armed conflict",
                    "C. Only fires",
                    "D. Only earthquakes"
                ],
                "correct": 1,
                "explanation": "Disasters include natural disasters, transportation accidents, terrorist attacks, fires/explosions, and armed conflict."
            },
            {
                "question": "Why is identification important in DVI?",
                "options": [
                    "A. For curiosity",
                    "B. Legal documentation of death, return of remains to families, criminal investigation, insurance and civil matters",
                    "C. For media",
                    "D. For records only"
                ],
                "correct": 1,
                "explanation": "Identification is essential for legal documentation, return of remains to families, criminal investigation, and insurance matters."
            },
            {
                "question": "Why are teeth extremely durable in disasters?",
                "options": [
                    "A. They are soft",
                    "B. Resistant to heat, trauma, and decomposition",
                    "C. They are small",
                    "D. They are protected"
                ],
                "correct": 1,
                "explanation": "Teeth are extremely durable and resistant to heat, trauma, and decomposition."
            },
            {
                "question": "What dental features can be used for identification?",
                "options": [
                    "A. Only fillings",
                    "B. Fillings, crowns, bridges, root canal treatments, tooth alignment, implants, dentures",
                    "C. Only crowns",
                    "D. Only missing teeth"
                ],
                "correct": 1,
                "explanation": "Features include fillings, crowns, bridges, root canal treatments, tooth alignment, implants, and dentures."
            },
            {
                "question": "What are the four INTERPOL DVI phases in correct order?",
                "options": [
                    "A. Postmortem, Antemortem, Scene, Reconciliation",
                    "B. Scene, Postmortem, Antemortem, Reconciliation",
                    "C. Antemortem, Postmortem, Scene, Reconciliation",
                    "D. Reconciliation, Scene, Postmortem, Antemortem"
                ],
                "correct": 1,
                "explanation": "The four phases are: Scene, Postmortem (PM), Antemortem (AM), and Reconciliation."
            },
            {
                "question": "What occurs during the Scene phase?",
                "options": [
                    "A. DNA analysis",
                    "B. Recovery of remains, labeling/tagging bodies, scene documentation, preservation of evidence",
                    "C. Dental examination",
                    "D. Record comparison"
                ],
                "correct": 1,
                "explanation": "Scene phase includes recovery of remains, labeling bodies, scene documentation, and evidence preservation."
            },
            {
                "question": "What occurs during the Postmortem phase?",
                "options": [
                    "A. Collecting dental records",
                    "B. Dental examination, charting, radiographs, photography at mortuary",
                    "C. Scene investigation",
                    "D. Family interviews"
                ],
                "correct": 1,
                "explanation": "Postmortem phase includes dental examination, charting, radiographic imaging, and photographic documentation at the mortuary."
            },
            {
                "question": "What are sources of antemortem dental records?",
                "options": [
                    "A. Only hospitals",
                    "B. Dental clinics, hospitals, orthodontic offices, insurance records, family-provided documents",
                    "C. Only dental clinics",
                    "D. Only insurance"
                ],
                "correct": 1,
                "explanation": "Sources include dental clinics, hospitals, orthodontic offices, insurance records, and family-provided documents."
            },
            {
                "question": "What are the possible outcomes of the Reconciliation phase?",
                "options": [
                    "A. Match or no match",
                    "B. Positive identification, possible identification, insufficient evidence, exclusion",
                    "C. Guilty or not guilty",
                    "D. Admit or exclude"
                ],
                "correct": 1,
                "explanation": "Outcomes are positive identification, possible identification, insufficient evidence, or exclusion."
            },
            
            # ============================================================================
            # SECTION 14: LEGAL ASPECTS AND EXPERT TESTIMONY (Questions 146-155)
            # ============================================================================
            {
                "question": "What is forensic dentistry?",
                "options": [
                    "A. General dental practice",
                    "B. Application of dental science to legal investigations and court proceedings",
                    "C. Cosmetic dentistry",
                    "D. Pediatric dentistry"
                ],
                "correct": 1,
                "explanation": "Forensic dentistry involves application of dental science to legal investigations and court proceedings."
            },
            {
                "question": "What is an expert witness?",
                "options": [
                    "A. Any witness",
                    "B. Person with specialized knowledge, education, training, or experience who assists court in understanding technical evidence",
                    "C. Police officer",
                    "D. Lawyer"
                ],
                "correct": 1,
                "explanation": "An expert witness has specialized knowledge to assist the court in understanding technical evidence."
            },
            {
                "question": "What can expert witnesses do that fact witnesses cannot?",
                "options": [
                    "A. Testify",
                    "B. Provide professional opinions and interpret scientific evidence",
                    "C. Speak in court",
                    "D. Meet with judge"
                ],
                "correct": 1,
                "explanation": "Expert witnesses can provide professional opinions and interpret scientific evidence, unlike fact witnesses who only describe observations."
            },
            {
                "question": "Who oversees legal proceedings in court?",
                "options": [
                    "A. Jury",
                    "B. Judge",
                    "C. Prosecutor",
                    "D. Defense attorney"
                ],
                "correct": 1,
                "explanation": "The judge oversees legal proceedings in court."
            },
            {
                "question": "What is the role of the jury?",
                "options": [
                    "A. Oversee proceedings",
                    "B. Determine facts and verdict in some cases",
                    "C. Represent government",
                    "D. Represent accused"
                ],
                "correct": 1,
                "explanation": "The jury determines facts and verdict in some cases."
            },
            {
                "question": "What occurs during direct examination?",
                "options": [
                    "A. Opposing attorney questions",
                    "B. Lawyer who called expert asks questions to present findings",
                    "C. Judge questions",
                    "D. Jury questions"
                ],
                "correct": 1,
                "explanation": "Direct examination is when the lawyer who called the expert witness asks questions to present findings."
            },
            {
                "question": "What is the purpose of cross-examination?",
                "options": [
                    "A. Present findings",
                    "B. Challenge credibility and test reliability of conclusions",
                    "C. Clarify issues",
                    "D. Open the case"
                ],
                "correct": 1,
                "explanation": "Cross-examination challenges credibility and tests reliability of conclusions."
            },
            {
                "question": "What is the purpose of re-direct examination?",
                "options": [
                    "A. Challenge witness",
                    "B. Clarify issues raised during cross-examination",
                    "C. Present new evidence",
                    "D. Close case"
                ],
                "correct": 1,
                "explanation": "Re-direct examination clarifies issues raised during cross-examination."
            },
            {
                "question": "What must a forensic report include?",
                "options": [
                    "A. Only conclusion",
                    "B. Case information, background, methods, findings, interpretation, conclusion",
                    "C. Only photographs",
                    "D. Only measurements"
                ],
                "correct": 1,
                "explanation": "A forensic report must include case information, background, methods, findings, interpretation, and conclusion."
            },
            {
                "question": "What is the expert witness's primary duty?",
                "options": [
                    "A. To prosecution",
                    "B. To court and justice system, not to either legal party",
                    "C. To defense",
                    "D. To themselves"
                ],
                "correct": 1,
                "explanation": "The expert's duty is to the court and justice system, not to either legal party."
            }
        ])
        
        self.total_questions = len(self.questions)
        print(f"Total questions loaded: {self.total_questions}")
    
    def run_quiz(self):
        """Run the interactive quiz"""
        print("\n" + "="*70)
        print(" ULTIMATE FORENSIC BITE MARK ANALYSIS QUIZ")
        print("="*70)
        print(f"\nThis comprehensive quiz contains {self.total_questions} questions covering:")
        print("\n📌 Section 1: General Definition & Nature (15 questions)")
        print("📌 Section 2: Crime-Specific Locations (10 questions)")
        print("📌 Section 3: Dental Characteristics (10 questions)")
        print("📌 Section 4: Limitations (10 questions)")
        print("📌 Section 5: Classification by Injury Type (15 questions)")
        print("📌 Section 6: Classification by Clarity & Source (10 questions)")
        print("📌 Section 7: Documentation Procedures (15 questions)")
        print("📌 Section 8: DNA & Additional Methods (10 questions)")
        print("📌 Section 9: Analysis Methods & Overlays (10 questions)")
        print("📌 Section 10: Class vs Individual Characteristics (7 questions)")
        print("📌 Section 11: Controversies & Scientific Reviews (13 questions)")
        print("📌 Section 12: Abuse Recognition (10 questions)")
        print("📌 Section 13: Disaster Victim Identification (10 questions)")
        print("📌 Section 14: Legal Aspects & Expert Testimony (10 questions)")
        print("-"*70)
        print(f"TOTAL: {self.total_questions} questions")
        print("-"*70)
        
        input("\nPress Enter to start the quiz...")
        
        # Shuffle questions for variety
        random.shuffle(self.questions)
        
        for i, q in enumerate(self.questions, 1):
            print(f"\n\n{'='*70}")
            print(f"QUESTION {i} of {self.total_questions}")
            print('='*70)
            print(f"\n{q['question']}\n")
            
            for option in q["options"]:
                print(option)
            
            while True:
                try:
                    answer = input("\nEnter your answer (1-4): ").strip()
                    if answer in ['1', '2', '3', '4']:
                        answer = int(answer) - 1
                        break
                    elif answer.lower() == 'quit':
                        self.show_results()
                        return
                    else:
                        print("Please enter a number between 1 and 4, or 'quit' to end.")
                except ValueError:
                    print("Please enter a valid number.")
            
            if answer == q["correct"]:
                print("\n✅ CORRECT! +1 point")
                self.score += 1
            else:
                print(f"\n❌ INCORRECT.")
                print(f"The correct answer is: {q['options'][q['correct']]}")
            
            print(f"\n📝 EXPLANATION: {q['explanation']}")
            
            # Show progress
            percentage = (self.score / i) * 100
            print(f"\n📊 Progress: {i}/{self.total_questions} | Current Score: {self.score}/{i} ({percentage:.1f}%)")
            
            if i < self.total_questions:
                input("\nPress Enter for next question...")
        
        self.show_results()
    
    def show_results(self):
        """Display detailed quiz results"""
        percentage = (self.score / self.total_questions) * 100
        
        print("\n" + "="*70)
        print(" FINAL RESULTS")
        print("="*70)
        print(f"\nTotal Questions: {self.total_questions}")
        print(f"Correct Answers: {self.score}")
        print(f"Incorrect Answers: {self.total_questions - self.score}")
        print(f"Final Score: {percentage:.1f}%")
        print("-"*70)
        
        # Performance categories
        if percentage >= 90:
            print("\n🌟 FORENSIC ODONTOLOGY EXPERT! (90-100%)")
            print("You have mastered virtually all aspects of bite mark")
            print("forensics. Your knowledge is comprehensive!")
        elif percentage >= 80:
            print("\n👍 ADVANCED LEVEL (80-89%)")
            print("Excellent understanding of most concepts. You're well")
            print("prepared for forensic applications.")
        elif percentage >= 70:
            print("\n📚 INTERMEDIATE LEVEL (70-79%)")
            print("Good foundation in bite mark forensics. Review the")
            print("areas where you made errors to strengthen your knowledge.")
        elif percentage >= 60:
            print("\n📖 BASIC LEVEL (60-69%)")
            print("You understand fundamental concepts but need more")
            print("comprehensive review of the material.")
        elif percentage >= 50:
            print("\n🔰 NOVICE LEVEL (50-59%)")
            print("You have basic awareness. Consider studying the")
            print("document more thoroughly.")
        else:
            print("\n📋 INTRODUCTORY LEVEL (Below 50%)")
            print("This is a complex subject. Review all sections")
            print("systematically and try again.")
        
        # Topic-specific recommendations based on score
        print("\n" + "-"*70)
        print("RECOMMENDATIONS FOR IMPROVEMENT:")
        print("-"*70)
        
        if percentage < 80:
            print("• Review classification systems (injury types, clarity, source)")
            print("• Study documentation procedures and photography standards")
            print("• Focus on DNA collection and chain of custody")
        if percentage < 70:
            print("• Pay special attention to limitations and controversies")
            print("• Review abuse recognition signs and mandatory reporting")
            print("• Study DVI phases and INTERPOL protocols")
        if percentage < 60:
            print("• Master basic definitions and terminology")
            print("• Understand mechanism of bite mark formation")
            print("• Learn class vs individual characteristics")
        if percentage < 50:
            print("• Start with Section 1: General Definition and Nature")
            print("• Focus on key terminology and basic concepts")
            print("• Review the document chapter by chapter")
        
        print("\n" + "="*70)
        print(" Thank you for completing the comprehensive quiz!")
        print("="*70)


class BiteMarkStudyGuide:
    """Quick reference study guide"""
    
    def display_study_guide(self):
        """Display key study points"""
        print("\n" + "="*70)
        print(" QUICK STUDY GUIDE: KEY POINTS TO REMEMBER")
        print("="*70)
        
        study_points = [
            ("📌 DEFINITION", "Bite mark: Patterned injury from teeth exerting force on surface"),
            ("📌 KEY TEETH", "Incisors (rectangular marks) and canines (triangular/puncture marks)"),
            ("📌 BITE TYPES", "Pressure (static), Drag (movement), Avulsive (tearing)"),
            ("📌 INJURY TYPES", "Abrasion (scrape), Contusion (bruise), Laceration (tear), Incised (cut), Avulsion (removal)"),
            ("📌 CLARITY LEVELS", "Definite (clear pattern), Possible (partial), Questionable (unclear)"),
            ("📌 MEASUREMENTS", "Adult intercanine: 30-45mm, Child: <30mm, Arch width: 3-5cm"),
            ("📌 DOCUMENTATION", "Photography (with ABFO scale), Impressions, DNA swabbing"),
            ("📌 PHOTOGRAPHY", "Overall, medium, close-up; perpendicular angle; oblique lighting"),
            ("📌 DNA PROCEDURE", "Sterile swabs, moisten with sterile water, air-dry, control swabs"),
            ("📌 CLASS CHARACTERISTICS", "Common features: arch shape, general tooth size"),
            ("📌 INDIVIDUAL CHARACTERISTICS", "Unique features: rotations, gaps, chips, restorations, missing teeth"),
            ("📌 LIMITATIONS", "Skin distortion, movement, healing changes, environmental factors"),
            ("📌 NAS 2009", "Lacks sufficient scientific validation"),
            ("📌 PCAST 2016", "Does not meet scientific standards for validity"),
            ("📌 ABUSE RED FLAGS", "Torn labial frenum (infants), protected areas (ears/neck/inner mouth), history mismatch"),
            ("📌 DVI PHASES", "Scene → Postmortem (PM) → Antemortem (AM) → Reconciliation"),
            ("📌 DVI OUTCOMES", "Positive ID, Possible ID, Insufficient evidence, Exclusion"),
            ("📌 EXPERT WITNESS", "Provides opinions, interprets evidence, duty to court not party"),
            ("📌 COURT TESTIMONY", "Direct exam → Cross-exam → Re-direct exam"),
            ("📌 MODERN VIEW", "Supporting evidence only, not definitive identification")
        ]
        
        for i, (title, point) in enumerate(study_points, 1):
            print(f"\n{title}")
            print(f"   {point}")
        
        print("\n" + "="*70)
        print(" Study guide complete - review these key points regularly!")
        print("="*70)


def main():
    """Main menu for the forensic quiz application"""
    while True:
        print("\n" + "="*70)
        print(" FORENSIC BITE MARK ANALYSIS - COMPREHENSIVE STUDY TOOL")
        print("="*70)
        print("\n1. Take the FULL QUIZ (155 questions)")
        print("2. View Quick Study Guide")
        print("3. Exit")
        print("-"*70)
        print("This tool covers ALL content from the forensic odontology document")
        print("-"*70)
        
        choice = input("Select an option (1-3): ").strip()
        
        if choice == "1":
            quiz = BiteMarkForensicsQuiz()
            quiz.run_quiz()
        elif choice == "2":
            guide = BiteMarkStudyGuide()
            guide.display_study_guide()
        elif choice == "3":
            print("\nThank you for studying forensic bite mark analysis!")
            print("Remember: In forensics, knowledge and caution save lives.\n")
            break
        else:
            print("\n❌ Invalid option. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
