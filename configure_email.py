from __future__ import annotations

from getpass import getpass
from pathlib import Path
import smtplib
import ssl


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"


def _ask_provider() -> tuple[str, int]:
    print("\nE-posta sağlayıcısını seçin:")
    print("  1) Gmail")
    print("  2) Outlook / Microsoft 365")

    choice = input("Seçim [1]: ").strip() or "1"

    if choice == "2":
        return "smtp.office365.com", 587

    return "smtp.gmail.com", 587


def _escape_env(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def main() -> None:
    print("TecJA gerçek PDF e-posta gönderimi kurulumu")
    print("Parolanız ekranda görünmez ve yalnızca yerel .env dosyasına yazılır.")

    host, port = _ask_provider()
    sender = input("Gönderen e-posta adresi: ").strip().lower()

    if "@" not in sender or "." not in sender.rsplit("@", 1)[-1]:
        raise SystemExit("Geçerli bir e-posta adresi girmelisiniz.")

    password = getpass(
        "Uygulama parolası (Gmail için 16 karakterli App Password): "
    ).replace(" ", "")

    if not password:
        raise SystemExit("Uygulama parolası boş bırakılamaz.")

    print("SMTP hesabı doğrulanıyor...")
    context = ssl.create_default_context()

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender, password)
    except (smtplib.SMTPException, OSError) as exc:
        raise SystemExit(
            "SMTP doğrulaması başarısız. E-posta adresini ve uygulama "
            "parolasını kontrol edin. Normal hesap parolası kullanmayın.\n"
            f"Teknik ayrıntı: {exc}"
        ) from exc

    content = "\n".join(
        [
            "# TecJA PDF report email delivery",
            f'TECJA_SMTP_HOST="{_escape_env(host)}"',
            f"TECJA_SMTP_PORT={port}",
            f'TECJA_SMTP_USERNAME="{_escape_env(sender)}"',
            f'TECJA_SMTP_PASSWORD="{_escape_env(password)}"',
            f'TECJA_SMTP_FROM_EMAIL="{_escape_env(sender)}"',
            'TECJA_SMTP_FROM_NAME="TecJA Analytics"',
            "TECJA_SMTP_USE_TLS=true",
            "TECJA_SMTP_USE_SSL=false",
            "",
        ]
    )

    temporary_path = ENV_PATH.with_suffix(".env.tmp")
    temporary_path.write_text(content, encoding="utf-8")
    temporary_path.replace(ENV_PATH)

    print(f"\nKurulum tamamlandı: {ENV_PATH}")
    print("Backend'i yeniden başlatın ve Reports sayfasından tekrar gönderin.")


if __name__ == "__main__":
    main()
