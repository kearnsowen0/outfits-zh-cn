from pathlib import Path

sheets = Path("src/lib/sheets.dart")
text = sheets.read_text(encoding="utf-8")
needle = """              SelectChip(
                label: 'English',
                active: store.localeCode == 'en',
                mono: false,
                height: 34,
                onTap: () => store.setLocale('en'),
              ),"""
addition = needle + """
              SelectChip(
                label: '简体中文',
                active: store.localeCode == 'zh',
                mono: false,
                height: 34,
                onTap: () => store.setLocale('zh'),
              ),"""
if "label: '简体中文'" not in text:
    if needle not in text:
        raise SystemExit("English language chip not found")
    text = text.replace(needle, addition)
    sheets.write_text(text, encoding="utf-8")

store = Path("src/lib/wardrobe_store.dart")
text = store.read_text(encoding="utf-8")
old = "return lookupAppLocalizations(Locale(code == 'en' ? 'en' : 'cs')).unsortedName;"
new = """final normalized = const {'cs', 'en', 'zh'}.contains(code) ? code : 'en';
    return lookupAppLocalizations(Locale(normalized)).unsortedName;"""
if old in text:
    text = text.replace(old, new)
    store.write_text(text, encoding="utf-8")
elif "const {'cs', 'en', 'zh'}.contains(code)" not in text:
    raise SystemExit("Locale fallback code not found")

Path("src/lib/l10n/app_zh.arb").write_text(
    Path("patches/app_zh.arb").read_text(encoding="utf-8"),
    encoding="utf-8",
)
