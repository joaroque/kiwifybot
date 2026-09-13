import getpass
import os
import sys

from kiwify import Kiwibot


def main():
    email = os.environ.get("KIWIFY_EMAIL") or input("E-mail da Kiwify: ").strip()
    password = os.environ.get("KIWIFY_PASSWORD") or getpass.getpass("Senha: ")
    bot = Kiwibot()
    bot.login(email, password)
    totals = bot.download_all()
    print(
        "Resumo: "
        f"baixados={totals['downloaded']}, "
        f"já existentes={totals['skipped']}, "
        f"falhas={totals['failed']}"
    )
    return 1 if totals["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
