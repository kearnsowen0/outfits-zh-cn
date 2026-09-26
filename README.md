# Outfits 简体中文版

基于原 Outfits 项目增加简体中文本地化。应用数据保存在设备本地。

Android APK 可在 GitHub Actions 的 **Build Android APK** 工作流中自动构建。

---

# Outfits

A local-first wardrobe app for planning outfits: photograph what you own, mix tops, bottoms, shoes and layers into an outfit, and save the combinations you like into collections for later. Everything lives on your device — there's no account, no backend and no network access.

[Google Play](https://play.google.com/store/apps/details?id=eu.oscillator.outfits&pcampaignid=web_share) · [App Store](#)

## Features

- **Outfit builder** — swipe through your tops, bottoms and shoes (or pick one from a grid), stack up to two extra layers, and shuffle for a random combination.
- **Wardrobe** — add clothing with a camera photo or one from your gallery, sorted into categories.
- **Tags** — tag items freely and filter wardrobe/outfit choices.
- **Collections** — save outfits under named collections.
- **Offline, on-device storage** — wardrobe data and photos stay on the device.

## Tech stack

Flutter / Dart, provider, image_picker and path_provider.

## Android build

GitHub Actions 中运行 **Build Android APK**，完成后在该次运行的 Artifacts 中下载 `outfits-zh-release-apk`.

## License

MIT — see [LICENSE](LICENSE).
