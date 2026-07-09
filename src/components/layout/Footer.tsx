import { useTranslations } from "next-intl";
import { Bot, Mail, MessageCircle, Send } from "lucide-react";
import { Link } from "@/i18n/navigation";

const NAV_ITEMS = [
  { key: "home", href: "/" },
  { key: "services", href: "/services" },
  { key: "solutions", href: "/solutions" },
  { key: "about", href: "/about" },
  { key: "contact", href: "/contact" },
] as const;

export default function Footer() {
  const t = useTranslations("footer");
  const tNav = useTranslations("nav");
  const tContact = useTranslations("contact");
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-border bg-surface/40">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 sm:px-6 md:grid-cols-3">
        <div>
          <Link href="/" className="flex items-center gap-2 text-lg font-bold">
            <Bot className="h-6 w-6 text-accent-bright" />
            <span>
              AI-<span className="text-accent-bright">Agentes</span>
            </span>
          </Link>
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted">
            {t("tagline")}
          </p>
        </div>

        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
            {t("navTitle")}
          </h3>
          <ul className="mt-4 space-y-2">
            {NAV_ITEMS.map(({ key, href }) => (
              <li key={key}>
                <Link
                  href={href}
                  className="text-sm text-muted transition-colors hover:text-foreground"
                >
                  {tNav(key)}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
            {t("contactTitle")}
          </h3>
          <ul className="mt-4 space-y-3">
            <li className="text-sm text-foreground">{tContact("person")}</li>
            <li>
              <a
                href="mailto:hello@ai-agentes.com"
                className="flex items-center gap-2 text-sm text-muted transition-colors hover:text-foreground"
              >
                <Mail className="h-4 w-4" />
                hello@ai-agentes.com
              </a>
            </li>
            <li>
              <a
                href="https://t.me/aiagentes"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-muted transition-colors hover:text-foreground"
              >
                <Send className="h-4 w-4" />
                Telegram
              </a>
            </li>
            <li>
              <a
                href="https://wa.me/0000000000"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-muted transition-colors hover:text-foreground"
              >
                <MessageCircle className="h-4 w-4" />
                WhatsApp
              </a>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-border">
        <div className="mx-auto max-w-6xl px-4 py-5 sm:px-6">
          <p className="text-xs text-muted">
            © {year} AI-Agentes. {t("rights")}
          </p>
        </div>
      </div>
    </footer>
  );
}
