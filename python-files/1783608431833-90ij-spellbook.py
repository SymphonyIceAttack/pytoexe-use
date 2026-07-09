import re
import random
from typing import List, Dict, Optional

class SpellBook:
    """Parses the Encyclopedia of 5000 Spells and provides random spells by category."""

    # Categories as they appear in the table of contents (Part Two)
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
        self.sections = self._split_into_sections()
        self.spells_by_category = self._extract_spells()

    def _split_into_sections(self) -> Dict[str, str]:
        """Split the full text into category sections using the TOC headings."""
        sections = {}
        # We'll locate each category heading in the text.
        # Headings appear as "Banishing Spells" etc. They are usually on their own line.
        # To be robust, we'll search for the category name followed by a newline or colon.
        for cat in self.CATEGORIES:
            # Create a pattern: category name, possibly followed by a colon or newline.
            # We'll find the start index of the category.
            # We need to handle variations like "Spell of Domination, Persuasion, and Influence"
            # We'll search case-insensitively.
            pattern = re.compile(re.escape(cat), re.IGNORECASE)
            match = pattern.search(self.text)
            if match:
                start = match.start()
                # Find the end: either the next category or the end of the text.
                # We'll find the next category heading.
                end = len(self.text)
                for other_cat in self.CATEGORIES:
                    if other_cat == cat:
                        continue
                    other_pattern = re.compile(re.escape(other_cat), re.IGNORECASE)
                    other_match = other_pattern.search(self.text, start + 1)
                    if other_match and other_match.start() < end:
                        end = other_match.start()
                sections[cat] = self.text[start:end].strip()
        return sections

    def _extract_spells(self) -> Dict[str, List[str]]:
        """For each category, extract individual spells (text blocks) and store them."""
        spells_by_category = {}
        for cat, section_text in self.sections.items():
            # Within a section, find spells.
            # Spells are often introduced by a heading like "Basil Spell (1)" or "Apple Binding"
            # We'll look for lines that contain "Spell" followed by a number in parentheses, or just "Spell".
            # Also look for "Spell:" or "Spell -"
            # We'll split the section into paragraphs by blank lines, then check if a paragraph starts with a spell header.
            paragraphs = re.split(r'\n\s*\n', section_text)
            spells = []
            current_spell = []
            in_spell = False
            spell_header_pattern = re.compile(r'^(.+?Spell\s*(?:\(?\d+\)?)?\s*[:.]?)', re.IGNORECASE)
            # Also catch headings like "Apple Binding" or "Basil Spell" without "Spell" word? We'll try to catch any heading that looks like a spell name.
            # We'll use a heuristic: if a line ends with "Spell" or contains "Spell (" or is a short phrase that appears to be a title.
            # For simplicity, we'll treat any line that starts with a capital letter and ends with a colon or is less than 50 chars as a potential spell title.
            # But we'll mainly rely on "Spell" word.
            for para in paragraphs:
                lines = para.split('\n')
                # Check if first line is a spell header
                first_line = lines[0].strip()
                if re.search(r'Spell\s*\(?\d*\)?\s*[:.]?', first_line, re.IGNORECASE):
                    if current_spell:
                        spells.append('\n'.join(current_spell).strip())
                        current_spell = []
                    current_spell.append(para)
                else:
                    # If we are already in a spell, append this paragraph to it
                    if current_spell:
                        current_spell.append(para)
                    # else ignore (maybe it's a subheading or intro)
            if current_spell:
                spells.append('\n'.join(current_spell).strip())
            spells_by_category[cat] = spells
        return spells_by_category

    def get_categories(self) -> List[str]:
        return self.CATEGORIES

    def get_random_spell(self, category: str) -> Optional[str]:
        """Return a random spell from the given category, or None if none found."""
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
    # The user must provide the book text in a file named "book.txt"
    try:
        with open("book.txt", "r", encoding="utf-8") as f:
            book_text = f.read()
    except FileNotFoundError:
        print("Error: Could not find 'book.txt'. Please place the book text in that file.")
        exit(1)

    spellbook = SpellBook(book_text)
    spellbook.interactive()