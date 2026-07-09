import re
import random
import os
from typing import Dict, List, Optional, Tuple

class SpellBook:
    """
    An entertaining program that provides users with instructions to perform
    spells from "The Encyclopedia of 5000 Spells".
    
    The program organizes spells into categories such as love spells,
    protection spells, etc. Users can browse categories, read spell
    instructions, get random spells, and search for specific spells.
    """
    
    def __init__(self, filepath: str):
        """
        Initialize the SpellBook by loading spells from the given text file.
        """
        self.filepath = filepath
        self.categories = {}  # category_name -> list of (spell_title, instructions)
        self.all_spells = []   # list of (category, spell_title, instructions)
        self._load_spells()
    
    def _load_spells(self):
        """
        Parse the encyclopedia text file and extract spells organized by category.
        
        This method uses regex patterns to find:
        - Category headers (e.g., "Love Magic:", "Protection Spells")
        - Spell titles (lines ending with ":")
        - Spell instructions (paragraphs following a title)
        """
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: Could not find file '{self.filepath}'.")
            print("Please ensure the file is in the correct location.")
            return
        
        # Find the table of contents to identify categories
        toc_match = re.search(r"PART TWO[:\s]+The Spells\n-+\n(.*?)\n\n", content, re.DOTALL)
        categories_from_toc = []
        if toc_match:
            toc_text = toc_match.group(1)
            # Extract lines that look like category entries from TOC
            toc_lines = toc_text.split('\n')
            for line in toc_lines:
                # Remove page numbers and trim
                clean = re.sub(r'\d+$', '', line).strip()
                if clean and not clean.startswith('-') and not clean.startswith('—'):
                    categories_from_toc.append(clean)
        
        # If we found categories in TOC, use them to guide parsing
        if categories_from_toc:
            # Build a regex to find each category section
            for i, cat in enumerate(categories_from_toc):
                # Skip if it's too generic or just a separator
                if not cat or cat.startswith('—'):
                    continue
                    
                # Find the section for this category
                pattern = rf"\b{re.escape(cat)}\b[:\s]*\n-+\n(.*?)(?=\n\s*\b{'|'.join(re.escape(c) for c in categories_from_toc[i+1:])}\b[:\s]*\n-+|\Z)"
                # Try both with and without newline variations
                if i < len(categories_from_toc) - 1:
                    next_cat = categories_from_toc[i+1]
                    # Simpler approach: find content between category headers
                    start_pattern = rf"\b{re.escape(cat)}\b[:\s]*\n-+"
                    end_pattern = rf"(?=\b{re.escape(next_cat)}\b[:\s]*\n-+)"
                else:
                    start_pattern = rf"\b{re.escape(cat)}\b[:\s]*\n-+"
                    end_pattern = r"(?=\Z)"
                
                start_match = re.search(start_pattern, content, re.DOTALL)
                if start_match:
                    start_pos = start_match.end()
                    if i < len(categories_from_toc) - 1:
                        end_match = re.search(end_pattern, content[start_pos:], re.DOTALL)
                        if end_match:
                            section_content = content[start_pos:start_pos + end_match.start()]
                        else:
                            section_content = content[start_pos:]
                    else:
                        section_content = content[start_pos:]
                    
                    # Extract spells from this section
                    spells = self._extract_spells_from_section(section_content)
                    if spells:
                        self.categories[cat] = spells
                        for title, instr in spells:
                            self.all_spells.append((cat, title, instr))
        
        # If no spells were found with TOC method, try a more aggressive approach
        if not self.all_spells:
            self._fallback_parse(content)
    
    def _fallback_parse(self, content: str):
        """
        Fallback method to parse spells without relying on TOC structure.
        Uses common patterns to identify spell sections.
        """
        # Look for common category patterns
        category_patterns = [
            (r"Love Spells\b|Love Magic\b|Love and Romance", "Love Spells"),
            (r"Protection Spells\b|Protection Magic", "Protection Spells"),
            (r"Money Spells\b|Wealth", "Money Spells"),
            (r"Healing Spells\b|Healing Magic", "Healing Spells"),
            (r"Banishing Spells\b|Banish", "Banishing Spells"),
            (r"Cleansing Spells\b|Cleansing", "Cleansing Spells"),
            (r"Luck and Success\b|Fortune", "Luck Spells"),
            (r"Divination\b|Oracle", "Divination Spells"),
            (r"Dream Spells\b|Dream Magic", "Dream Spells"),
            (r"Fertility\b", "Fertility Spells"),
            (r"Marriage\b|Wedding", "Marriage Spells"),
            (r"Hexes\b|Curses", "Hex Spells"),
            (r"Evil Eye\b", "Evil Eye Spells"),
            (r"Traveler", "Travel Spells"),
        ]
        
        # Find all potential category sections
        for pattern, cat_name in category_patterns:
            sections = re.finditer(rf"(?<!\w)({pattern})[:\s]*\n-+\s*\n(.*?)(?=\n\s*\b[A-Z][a-z]+\s+Spells\b|\n\s*\b[A-Z][a-z]+\s+Magic\b|\Z)", 
                                 content, re.DOTALL | re.IGNORECASE)
            for match in sections:
                section_content = match.group(2)
                spells = self._extract_spells_from_section(section_content)
                if spells:
                    if cat_name not in self.categories:
                        self.categories[cat_name] = []
                    self.categories[cat_name].extend(spells)
                    for title, instr in spells:
                        self.all_spells.append((cat_name, title, instr))
        
        # If we still have no spells, try to find ANY spells in the content
        if not self.all_spells:
            self._extract_any_spells(content)
    
    def _extract_spells_from_section(self, section_content: str) -> List[Tuple[str, str]]:
        """
        Extract spell titles and instructions from a section of text.
        """
        spells = []
        
        # Find patterns like "Spell Title:" followed by instructions
        # This handles various formats: bold, numbered, etc.
        lines = section_content.split('\n')
        current_title = None
        current_instructions = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line is a spell title (ends with ":" or is in all caps)
            title_match = re.match(r'^([^:]+):\s*$', line)
            if title_match:
                # Save previous spell
                if current_title and current_instructions:
                    instr_text = ' '.join(current_instructions).strip()
                    if instr_text:
                        spells.append((current_title, instr_text))
                
                current_title = title_match.group(1).strip()
                current_instructions = []
            elif current_title:
                # Check for numbered spell variants: "Spell Title (1)" or "Spell Title (2)"
                numbered_title = re.match(r'^([^:]+)\s*\(([0-9]+)\):\s*$', line)
                if numbered_title:
                    if current_title and current_instructions:
                        instr_text = ' '.join(current_instructions).strip()
                        if instr_text:
                            spells.append((current_title, instr_text))
                    current_title = f"{numbered_title.group(1)} ({numbered_title.group(2)})"
                    current_instructions = []
                else:
                    # This is likely an instruction line
                    # Remove any leading dashes, bullets, or numbers
                    cleaned = re.sub(r'^[•\-0-9.()]+\s*', '', line).strip()
                    if cleaned:
                        current_instructions.append(cleaned)
            else:
                # No current title, maybe we can find a title in this line
                # Look for patterns like "To cast a spell, ..." but skip these
                pass
        
        # Don't forget the last spell
        if current_title and current_instructions:
            instr_text = ' '.join(current_instructions).strip()
            if instr_text:
                spells.append((current_title, instr_text))
        
        return spells
    
    def _extract_any_spells(self, content: str):
        """
        Last resort: try to extract any spells from the entire text.
        """
        # Look for patterns like "Spell Title: instructions"
        pattern = r'([A-Z][A-Za-z\s]+Spell)\s*[:\-]\s*(.*?)(?=(?:[A-Z][A-Za-z\s]+Spell)\s*[:\-]|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            for title, instr in matches:
                title = title.strip()
                instr = instr.strip()
                # Clean up the instructions
                instr = re.sub(r'\s+', ' ', instr)
                if len(instr) > 20:  # Only keep spells with meaningful instructions
                    self.categories["General Spells"] = self.categories.get("General Spells", [])
                    self.categories["General Spells"].append((title, instr))
                    self.all_spells.append(("General Spells", title, instr))
        
        # If still nothing, extract from the "The Spells" part directly
        if not self.all_spells:
            # Look for the main spells section
            spell_section = re.search(r'PART TWO\s+The Spells\s*.*?(?=PART THREE|\Z)', content, re.DOTALL)
            if spell_section:
                section = spell_section.group(0)
                # Try to find spells in this section
                pattern = r'\n([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*Spell[s]?)\s*[:\-]\s*\n(.*?)\n\n'
                matches = re.findall(pattern, section, re.DOTALL)
                for title, instr in matches:
                    title = title.strip()
                    instr = instr.strip()
                    if len(instr) > 20:
                        self.categories["General Spells"] = self.categories.get("General Spells", [])
                        self.categories["General Spells"].append((title, instr))
                        self.all_spells.append(("General Spells", title, instr))
    
    def get_categories(self) -> List[str]:
        """Return a sorted list of available categories."""
        return sorted(self.categories.keys())
    
    def get_spells_in_category(self, category: str) -> List[Tuple[str, str]]:
        """Return all spells in a given category."""
        return self.categories.get(category, [])
    
    def get_random_spell(self) -> Optional[Tuple[str, str, str]]:
        """Return a random spell as (category, title, instructions)."""
        if not self.all_spells:
            return None
        return random.choice(self.all_spells)
    
    def search_spells(self, query: str) -> List[Tuple[str, str, str]]:
        """Search for spells containing the query in title or instructions."""
        query = query.lower()
        results = []
        for category, title, instr in self.all_spells:
            if query in title.lower() or query in instr.lower():
                results.append((category, title, instr))
        return results
    
    def display_spell(self, category: str, title: str, instructions: str):
        """Display a spell in a formatted, entertaining way."""
        print("\n" + "=" * 70)
        print(f"✨ {category} ✨")
        print("=" * 70)
        print(f"\n📜 {title}\n")
        print("-" * 50)
        # Split instructions into paragraphs for better readability
        paragraphs = instructions.split('. ')
        for p in paragraphs:
            if p.strip():
                print(f"   {p.strip()}.")
        print("\n" + "=" * 70)
        print("May the magic be with you!")
    
    def run(self):
        """Main interactive loop for the program."""
        if not self.all_spells:
            print("\n⚠️  Sorry, I couldn't find any spells in the book.")
            print("   Please make sure the text file is in the correct location.")
            print(f"   Looking for: {self.filepath}")
            return
        
        print("\n" + "=" * 70)
        print("🧙 Welcome to the Encyclopedia of 5000 Spells! 🧙")
        print("=" * 70)
        print(f"\n📖 Loaded {len(self.all_spells)} spells from {len(self.categories)} categories.")
        
        while True:
            print("\n" + "-" * 50)
            print("What would you like to do?")
            print("  1. Browse spells by category")
            print("  2. Get a random spell")
            print("  3. Search for a spell")
            print("  4. Show spell count")
            print("  5. Exit")
            print("-" * 50)
            
            choice = input("Enter your choice (1-5): ").strip()
            
            if choice == '1':
                self._browse_categories()
            elif choice == '2':
                self._show_random_spell()
            elif choice == '3':
                self._search_spells()
            elif choice == '4':
                print(f"\n📊 Total spells: {len(self.all_spells)}")
                print(f"   Categories: {len(self.categories)}")
                for cat, spells in self.categories.items():
                    print(f"   • {cat}: {len(spells)} spells")
            elif choice == '5':
                print("\n✨ May your spells always work! Farewell! ✨")
                break
            else:
                print("❌ Invalid choice. Please try again.")
    
    def _browse_categories(self):
        """Browse spells by category."""
        categories = self.get_categories()
        if not categories:
            print("⚠️  No categories available.")
            return
        
        print("\n📚 Available Categories:")
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat} ({len(self.categories[cat])} spells)")
        print("  0. Back to main menu")
        
        choice = input("\nSelect a category (number): ").strip()
        if choice == '0':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(categories):
                category = categories[idx]
                spells = self.get_spells_in_category(category)
                self._browse_spells_in_category(category, spells)
            else:
                print("❌ Invalid category number.")
        except ValueError:
            print("❌ Please enter a number.")
    
    def _browse_spells_in_category(self, category: str, spells: List[Tuple[str, str]]):
        """Browse spells within a specific category."""
        while True:
            print(f"\n📖 {category}:")
            for i, (title, instr) in enumerate(spells, 1):
                # Show first 60 characters of the title and instructions
                title_display = title[:60] + "..." if len(title) > 60 else title
                print(f"  {i}. {title_display}")
            print("  0. Back to categories")
            
            choice = input(f"\nSelect a spell to read (1-{len(spells)}, or 0): ").strip()
            if choice == '0':
                return
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(spells):
                    title, instr = spells[idx]
                    self.display_spell(category, title, instr)
                    input("\nPress Enter to continue...")
                else:
                    print("❌ Invalid spell number.")
            except ValueError:
                print("❌ Please enter a number.")
    
    def _show_random_spell(self):
        """Show a random spell."""
        spell = self.get_random_spell()
        if spell:
            category, title, instr = spell
            self.display_spell(category, title, instr)
            input("\nPress Enter to continue...")
        else:
            print("⚠️  No spells found.")
    
    def _search_spells(self):
        """Search for spells by keyword."""
        query = input("\n🔍 Enter a keyword to search for: ").strip()
        if not query:
            print("❌ Please enter a search term.")
            return
        
        results = self.search_spells(query)
        if not results:
            print(f"⚠️  No spells found containing '{query}'.")
            return
        
        print(f"\n📋 Found {len(results)} spells matching '{query}':")
        for i, (category, title, instr) in enumerate(results, 1):
            title_display = title[:60] + "..." if len(title) > 60 else title
            print(f"  {i}. {title_display} [{category}]")
        
        if len(results) > 0:
            choice = input(f"\nSelect a spell to read (1-{len(results)}, or 0 to skip): ").strip()
            if choice != '0':
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(results):
                        category, title, instr = results[idx]
                        self.display_spell(category, title, instr)
                        input("\nPress Enter to continue...")
                    else:
                        print("❌ Invalid spell number.")
                except ValueError:
                    print("❌ Please enter a number.")


def main():
    # Update this path to point to your text file location
    filepath = "book.txt"
    
    # Check if file exists in current directory, if not try to find it
    if not os.path.exists(filepath):
        # Try to find it in common locations
        possible_paths = [
            "book.txt",
            "./book.txt",
            "../book.txt",
            os.path.expanduser("~/Downloads/book.txt"),
            os.path.expanduser("~/Desktop/book.txt"),
        ]
        found = False
        for path in possible_paths:
            if os.path.exists(path):
                filepath = path
                found = True
                break
        if not found:
            print("⚠️  Could not find 'book.txt'.")
            print("   Please make sure the file is in the current directory.")
            print(f"   Looking for: {os.path.abspath('book.txt')}")
            return
    
    spell_book = SpellBook(filepath)
    spell_book.run()


if __name__ == "__main__":
    main()