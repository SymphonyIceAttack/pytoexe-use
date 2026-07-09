import re
import random
from typing import List, Dict, Optional

class SpellBook:
    CATEGORIES = [
        "Animal Spells",
        "Banishing Spells",
        "Better Business and Professional Success Spells",
        "Cleansing Spells",
        "Courtcase Spells: Legal Spells and Spells for Justice",
        "Death Spells: Death, Ghosts, Necromancy, and Vampires",
        "Divination Spells",
        "Spell of Domination, Persuasion, and Influence",
        "Dream Spells: Dreams, Insomnia, Nightmares, Astral Projection, and Witches' Flying Potions",
        "The Evil Eye",
        "Fertility: Spells for Conception and Contraception",
        "Fire Safety Spells",
        "Gamblers' Spells and Charms",
        "Happy Home Spells",
        "Healing Spells",
        "Hexes and their Antidotes",
        "Invisibility and Transformation Spells",
        "Love Magic: Spells for Romance, True Love, Seduction, and Sex",
        "Luck and Success Spells",
        "Marriage and Divorce Spells",
        "Money Spells: Spells for Wealth, Prosperity, and Financial Stability",
        "Pregnancy and Childbirth Spells: Spells to Protect Mothers and Infants",
        "Protection Spells",
        "Psychic Power Spells",
        "Spells for Travelers",
        "Spirit Summoning Spells",
        "Theft, Lost Objects, and Missing Persons",
        "Unblocking Spells",
        "Weather Spells",
        "Youth, Beauty, and Longevity Spells"
    ]

    def __init__(self, text: str):
        self.text = text
        self.spells_by_category = self._extract_spells()

    def _find_start_of_spells(self) -> int:
        """Find where the actual spell sections begin (after 'PART TWO' or 'The Spells')."""
        # Look for "PART TWO" or "The Spells" to skip the TOC.
        patterns = [r"PART TWO", r"The Spells"]
        for pat in patterns:
            match = re.search(pat, self.text, re.IGNORECASE)
            if match:
                # Return the index after that line
                return match.end()
        # Fallback: just start at the beginning
        return 0

    def _extract_spells(self) -> Dict[str, List[str]]:
        """Extract spells from each category section, starting after the TOC."""
        start_pos = self._find_start_of_spells()
        # Work with the text after the TOC
        text_after_toc = self.text[start_pos:]

        spells_by_category = {}
        for idx, cat in enumerate(self.CATEGORIES):
            # Find this category heading
            pattern = re.compile(re.escape(cat), re.IGNORECASE)
            match = pattern.search(text_after_toc)
            if not match:
                print(f"Warning: Category '{cat}' not found.")
                continue
            cat_start = match.start()
            # Determine the end: either the next category or end of text
            cat_end = len(text_after_toc)
            for other_cat in self.CATEGORIES[idx+1:]:
                other_match = re.search(re.escape(other_cat), text_after_toc[cat_start+1:], re.IGNORECASE)
                if other_match:
                    cat_end = cat_start + 1 + other_match.start()
                    break
            section_text = text_after_toc[cat_start:cat_end].strip()

            # Now split this section into individual spells
            # We'll look for paragraphs that start with a spell heading (contains "Spell" or a colon)
            paragraphs = re.split(r'\n\s*\n', section_text)
            spells = []
            current_spell = []
            for para in paragraphs:
                lines = para.split('\n')
                first_line = lines[0].strip()
                # Check if this paragraph starts a new spell
                if re.search(r'Spell\s*\(?\d*\)?\s*[:.]?', first_line, re.IGNORECASE) or \
                   re.search(r'^[A-Z][a-z]+ [A-Z][a-z]+ Spell', first_line) or \
                   re.search(r'^[A-Z][a-z]+ Spell', first_line):
                    if current_spell:
                        spells.append('\n'.join(current_spell).strip())
                        current_spell = []
                    current_spell.append(para)
                else:
                    if current_spell:
                        current_spell.append(para)
            if current_spell:
                spells.append('\n'.join(current_spell).strip())

            spells_by_category[cat] = spells

        return spells_by_category

    def get_categories(self) -> List[str]:
        return self.CATEGORIES

    def get_random_spell(self, category: str) -> Optional[str]:
        spells = self.spells_by_category.get(category, [])
        if not spells:
            return None
        return random.choice(spells)

    def list_categories(self):
        for i, cat in enumerate(self.CATEGORIES, 1):
            print(f"{i}. {cat}")

    def interactive(self):
        print("Welcome to the Encyclopedia of 5,000 Spells!")
        print("Choose a category to get a random spell.\n")
        while True:
            self.list_categories()
            print("\nEnter the number of your choice (or 'q' to quit):")
            choice = input("> ").strip()
            if choice.lower() == 'q':
                break
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self.CATEGORIES):
                    cat = self.CATEGORIES[idx]
                    spell = self.get_random_spell(cat)
                    if spell:
                        print(f"\n--- {cat} ---\n")
                        print(spell)
                        print("\n" + "-"*50 + "\n")
                    else:
                        print("No spells found in this category. Try another.")
                else:
                    print("Invalid number. Please try again.")
            except ValueError:
                print("Please enter a number or 'q'.")


if __name__ == "__main__":
    try:
        with open("book.txt", "r", encoding="utf-8") as f:
            book_text = f.read()
    except FileNotFoundError:
        print("Error: Could not find 'book.txt'. Please place the book text in that file.")
        exit(1)

    spellbook = SpellBook(book_text)
    spellbook.interactive()