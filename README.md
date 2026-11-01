# Kvekk

An audiobook app for browsing, comparing sources, downloading and listening. Previously named My Audiobooks.

This is the public home for Android releases, feedback and community source plugins. The app’s source code remains private. This repository contains documentation, a standalone plugin checker and a metadata-only example; it contains no Android app source.

## Install and update

No APK has been published in this repository yet. When an Android release is available, use [Releases](https://github.com/nixolas1/kvekk/releases). Release downloads will be free; a paid Play Store edition is being explored, with no promised date or final feature split.

Once the first release is published, you can add `https://github.com/nixolas1/kvekk` to [Obtainium](https://github.com/ImranR98/Obtainium) for update checks, or install the signed APK manually. Public release downloads need no GitHub token. Choose an APK compatible with your device. Android may ask you to allow installation and approve updates.

Compatible updates keep the same package and signing certificate and use a higher version code. Never uninstall an existing installation to solve a signing mismatch without first arranging how to preserve its books, accounts and settings.

## Get involved

- [Report a bug](https://github.com/nixolas1/kvekk/issues/new?template=bug_report.yml) or [suggest a feature](https://github.com/nixolas1/kvekk/issues/new?template=feature_request.yml).
- [Create a source plugin](docs/plugins.md), validate it locally and submit a plugin issue or pull request here.
- [Apply to contribute to the app](https://github.com/nixolas1/kvekk/issues/new?template=core_contributor.yml). Describe a focused improvement and relevant experience. Approved contributors may receive a separate, explicit invitation to the private app repository after scope and contribution rights are agreed. Applying does not grant access.

Keep passwords, tokens, account details, private URLs, personal files and unsanitized logs out of public issues. See [security reporting](SECURITY.md) for vulnerabilities.

## Why isn’t the app open source?

The app is being developed with a controlled contributor group while its provider integrations, licensing and distribution are worked through. Its own-code license is PolyForm Noncommercial 1.0.0, which is a source-available license with commercial-use restrictions, not an unrestricted open-source license. A private repository also means the source is not currently available to the public. Publishing APKs or this plugin toolkit does not change that.

The goal here is to make feedback and standalone plugins accessible without opening the whole app repository. This is the current arrangement, not a promise of a future source release. See [licensing](docs/licensing.md) and [contributing](CONTRIBUTING.md).
