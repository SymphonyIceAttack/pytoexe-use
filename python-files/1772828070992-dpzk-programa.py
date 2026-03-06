import collections
import re
import sys


class TextAnalyzer(object):

    def __init__(self, filename):
        self.filename = filename
        self.text = ""
        self.words = []
        self.word_count = 0
        self.line_count = 0
        self.char_count = 0
        self.frequency = {}

    def load_file(self):
        try:
            with open(self.filename, 'r') as f:
                self.text = f.read()
        except IOError:
            print("Erro ao abrir o arquivo.")
            sys.exit()

    def process_text(self):
        self.line_count = len(self.text.splitlines())
        self.char_count = len(self.text)

        self.words = re.findall(r'\b\w+\b', self.text.lower())
        self.word_count = len(self.words)

    def calculate_frequency(self):
        self.frequency = collections.Counter(self.words)

    def average_word_length(self):
        if not self.words:
            return 0
        total = sum(len(w) for w in self.words)
        return float(total) / len(self.words)

    def most_common_words(self, n=10):
        return self.frequency.most_common(n)

    def generate_report(self):

        report = []
        report.append("RELATORIO DE ANALISE DE TEXTO\n")
        report.append("Arquivo analisado: " + self.filename + "\n")

        report.append("Linhas: " + str(self.line_count))
        report.append("Palavras: " + str(self.word_count))
        report.append("Caracteres: " + str(self.char_count))
        report.append("Media do tamanho das palavras: %.2f" % self.average_word_length())

        report.append("\nPalavras mais comuns:")

        for word, count in self.most_common_words():
            report.append(word + " -> " + str(count))

        return "\n".join(report)

    def save_report(self, output="relatorio.txt"):
        report = self.generate_report()

        with open(output, "w") as f:
            f.write(report)

        print("Relatorio salvo em:", output)


def main():

    print("=== ANALISADOR DE TEXTO ===")

    filename = input("Digite o nome do arquivo: ")

    analyzer = TextAnalyzer(filename)

    analyzer.load_file()
    analyzer.process_text()
    analyzer.calculate_frequency()

    print("\nProcessamento concluido!\n")

    print(analyzer.generate_report())

    salvar = input("\nSalvar relatorio? (s/n): ")

    if salvar.lower() == "s":
        analyzer.save_report()


if __name__ == "__main__":
    main()