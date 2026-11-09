"""FR/EN command-line text shared by the local assembly tools.
FR : textes de ligne de commande partagés par les outils assembleur.
"""
import argparse
import sys


def pick(lang, fr, en):
    return fr if lang == "fr" else en


def requested_language(argv=None):
    args = sys.argv[1:] if argv is None else argv
    for index, value in enumerate(args):
        if value.startswith("--lang="):
            return "en" if value.split("=", 1)[1] == "en" else "fr"
        if value == "--lang" and index + 1 < len(args):
            return "en" if args[index + 1] == "en" else "fr"
    return "fr"


class Parser(argparse.ArgumentParser):
    def __init__(self, fr, en, **kwargs):
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure") and not stream.isatty():
                stream.reconfigure(encoding="utf-8")
        self.lang = requested_language()
        super().__init__(description=pick(self.lang, fr, en), add_help=False, **kwargs)
        self._positionals.title = pick(self.lang, "Arguments", "Positional arguments")
        self._optionals.title = "Options"
        self.add_argument("-h", "--help", action="help", help=pick(self.lang, "Afficher cette aide.", "Show this help."))
        self.add_argument("--lang", choices=("fr", "en"), default=self.lang,
                          help=pick(self.lang, "Langue des messages (défaut : fr).", "Message language (default: fr)."))

    def format_help(self):
        return self._translate(super().format_help())

    def format_usage(self):
        return self._translate(super().format_usage())

    def _translate(self, text):
        if self.lang == "fr":
            for old, new in (("usage:", "utilisation :"), ("unrecognized arguments:", "arguments inconnus :"),
                             ("the following arguments are required:", "arguments requis :"),
                             ("invalid choice:", "choix incorrect :"), ("choose from", "choisir parmi"),
                             ("expected one argument", "une valeur est attendue")):
                text = text.replace(old, new)
        return text

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: {pick(self.lang, 'erreur', 'error')}: {self._translate(message)}\n")
