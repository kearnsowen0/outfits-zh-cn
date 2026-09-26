from pathlib import Path

# ---------- home_screen.dart ----------
p = Path("src/lib/home_screen.dart")
s = p.read_text(encoding="utf-8")
s = s.replace("import 'collections_tab.dart';\n", "")
s = s.replace("import 'outfit_tab.dart';\n", "import 'related_looks_tab.dart';\n")
old = """                      child: switch (store.screen) {
                        WardrobeTabKind.outfit => OutfitTab(
                          onPick: (zone) => openPickSheet(context, zone),
                          onOpenLayers: ({replaceIndex}) =>
                              openLayerSheet(context, replaceIndex: replaceIndex),
                          onOpenSave: () => openSaveOutfitSheet(context),
                        ),
                        WardrobeTabKind.wardrobe => WardrobeTab(onOpenItem: (item) => openItemSheet(context, item)),
                        WardrobeTabKind.collections => const CollectionsTab(),
                      },"""
new = """                      child: switch (store.screen) {
                        WardrobeTabKind.wardrobe => WardrobeTab(
                          onOpenItem: (item) => openItemSheet(context, item),
                        ),
                        WardrobeTabKind.outfit => const RelatedLooksTab(),
                        WardrobeTabKind.collections => const RelatedLooksTab(),
                      },"""
if old not in s:
    raise SystemExit("home switch not found")
s = s.replace(old, new)
old = """    final tabs = [
      (WardrobeTabKind.outfit, l10n.tabOutfit),
      (WardrobeTabKind.wardrobe, l10n.tabWardrobe),
      (WardrobeTabKind.collections, l10n.tabCollections),
    ];"""
new = """    final tabs = [
      (WardrobeTabKind.wardrobe, l10n.tabWardrobe),
      (WardrobeTabKind.outfit, l10n.tabOutfit),
    ];"""
if old not in s:
    raise SystemExit("bottom tabs not found")
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")

# ---------- wardrobe_store.dart: default to wardrobe ----------
p = Path("src/lib/wardrobe_store.dart")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "  WardrobeTabKind screen = WardrobeTabKind.outfit;",
    "  WardrobeTabKind screen = WardrobeTabKind.wardrobe;",
)
# On launch always land on wardrobe for the new two-tab information architecture.
old = """  void _applyFirstLaunchScreen() {
    if (items.isEmpty) screen = WardrobeTabKind.wardrobe;
  }"""
new = """  void _applyFirstLaunchScreen() {
    screen = WardrobeTabKind.wardrobe;
  }"""
if old in s:
    s = s.replace(old, new)
p.write_text(s, encoding="utf-8")

# ---------- wardrobe_tab.dart ----------
wardrobe = r'''import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'l10n/app_localizations.dart';
import 'models.dart';
import 'sheets.dart';
import 'theme.dart';
import 'wardrobe_store.dart';
import 'widgets.dart';

/// Wardrobe with a permanent left navigation rail. Top and bottom categories
/// expose user-managed second-level folders directly under the primary menu.
class WardrobeTab extends StatefulWidget {
  final void Function(ClothingItem item) onOpenItem;

  const WardrobeTab({super.key, required this.onOpenItem});

  @override
  State<WardrobeTab> createState() => _WardrobeTabState();
}

class _WardrobeTabState extends State<WardrobeTab> {
  String _cat = 'horni';
  String? _folder;

  bool get _usesSubFolders => _cat == 'horni' || _cat == 'dolni';

  @override
  Widget build(BuildContext context) {
    final store = context.watch<WardrobeStore>();
    final l10n = AppLocalizations.of(context)!;

    if (_usesSubFolders) {
      final folders = store.foldersFor(_cat);
      if (_folder == null || !folders.contains(_folder)) {
        _folder = folders.isNotEmpty ? folders.first : store.fallbackFolder;
      }
    } else {
      _folder = null;
    }

    final items = store.byCat(_cat).where((item) {
      if (!_usesSubFolders) return true;
      return item.folder == _folder;
    }).toList();

    return Row(
      children: [
        Container(
          width: 104,
          decoration: const BoxDecoration(
            color: Colors.white,
            border: Border(right: BorderSide(color: AppColors.hairline)),
          ),
          child: ListView(
            padding: const EdgeInsets.fromLTRB(8, 10, 8, 18),
            children: [
              _PrimaryMenuItem(
                label: l10n.categoryHorni,
                selected: _cat == 'horni',
                onTap: () => setState(() {
                  _cat = 'horni';
                  _folder = null;
                }),
              ),
              if (_cat == 'horni')
                _SubFolderMenu(
                  catKey: 'horni',
                  selectedFolder: _folder,
                  onSelect: (folder) => setState(() => _folder = folder),
                ),
              _PrimaryMenuItem(
                label: l10n.categoryDolni,
                selected: _cat == 'dolni',
                onTap: () => setState(() {
                  _cat = 'dolni';
                  _folder = null;
                }),
              ),
              if (_cat == 'dolni')
                _SubFolderMenu(
                  catKey: 'dolni',
                  selectedFolder: _folder,
                  onSelect: (folder) => setState(() => _folder = folder),
                ),
              _PrimaryMenuItem(
                label: l10n.categorySaty,
                selected: _cat == 'saty',
                onTap: () => setState(() {
                  _cat = 'saty';
                  _folder = null;
                }),
              ),
              _PrimaryMenuItem(
                label: l10n.categoryBoty,
                selected: _cat == 'boty',
                onTap: () => setState(() {
                  _cat = 'boty';
                  _folder = null;
                }),
              ),
            ],
          ),
        ),
        Expanded(
          child: Column(
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        _folder ?? categoryLabel(context, _cat),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: AppText.sans(
                          size: 18,
                          weight: FontWeight.w500,
                          color: AppColors.ink,
                        ),
                      ),
                    ),
                    Text(
                      l10n.itemCount(items.length),
                      style: AppText.mono(
                        size: 9.5,
                        color: AppColors.mutedSoft,
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: GridView.builder(
                  padding: const EdgeInsets.fromLTRB(14, 4, 14, 18),
                  gridDelegate:
                      const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        mainAxisSpacing: 10,
                        crossAxisSpacing: 10,
                        childAspectRatio: .78,
                      ),
                  itemCount: items.length + 1,
                  itemBuilder: (context, index) {
                    if (index == items.length) {
                      return AddTile(
                        label: l10n.add,
                        onTap: () => openAddItemSheet(
                          context,
                          presetCategory: _cat,
                          presetFolder:
                              _usesSubFolders ? _folder : store.fallbackFolder,
                        ),
                      );
                    }
                    final item = items[index];
                    return GarmentCard(
                      width: double.infinity,
                      height: double.infinity,
                      imagePath: item.imagePath,
                      caption: item.folder ?? '',
                      onTap: () => widget.onOpenItem(item),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _PrimaryMenuItem extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _PrimaryMenuItem({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 5),
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 12),
          decoration: BoxDecoration(
            color: selected ? AppColors.cardFill : Colors.transparent,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(
            label,
            style: AppText.sans(
              size: 13,
              weight: selected ? FontWeight.w600 : FontWeight.w400,
              color: selected ? AppColors.ink : AppColors.muted,
            ),
          ),
        ),
      ),
    );
  }
}

class _SubFolderMenu extends StatelessWidget {
  final String catKey;
  final String? selectedFolder;
  final ValueChanged<String> onSelect;

  const _SubFolderMenu({
    required this.catKey,
    required this.selectedFolder,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    final store = context.watch<WardrobeStore>();
    final l10n = AppLocalizations.of(context)!;
    final folders = store.foldersFor(catKey);

    return Padding(
      padding: const EdgeInsets.only(left: 8, bottom: 8),
      child: Column(
        children: [
          for (final folder in folders)
            GestureDetector(
              onTap: () => onSelect(folder),
              onLongPress: () => _manageFolder(context, store, catKey, folder),
              child: Container(
                width: double.infinity,
                margin: const EdgeInsets.only(bottom: 3),
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                decoration: BoxDecoration(
                  color: selectedFolder == folder
                      ? const Color(0xFFF2F0ED)
                      : Colors.transparent,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  folder,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: AppText.sans(
                    size: 11.5,
                    color: selectedFolder == folder
                        ? AppColors.ink
                        : AppColors.mutedSoft,
                  ),
                ),
              ),
            ),
          GestureDetector(
            onTap: () => _createFolder(context, store, catKey),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 7),
              child: Row(
                children: [
                  const Icon(
                    Icons.add,
                    size: 14,
                    color: AppColors.mutedSoft,
                  ),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      l10n.addSubcategory,
                      style: AppText.sans(
                        size: 10.5,
                        color: AppColors.mutedSoft,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

Future<void> _createFolder(
  BuildContext context,
  WardrobeStore store,
  String catKey,
) async {
  final l10n = AppLocalizations.of(context)!;
  final name = await promptTextDialog(
    context,
    title: l10n.addSubcategory,
    initialValue: '',
    hintText: l10n.subcategoryHint,
    confirmLabel: l10n.create,
  );
  if (name != null && name.trim().isNotEmpty) {
    await store.addFolder(catKey, name);
  }
}

Future<void> _manageFolder(
  BuildContext context,
  WardrobeStore store,
  String catKey,
  String folder,
) async {
  final l10n = AppLocalizations.of(context)!;
  final action = await showModalBottomSheet<String>(
    context: context,
    backgroundColor: Colors.white,
    builder: (context) => SafeArea(
      child: Wrap(
        children: [
          ListTile(
            leading: const Icon(Icons.edit_outlined),
            title: Text(l10n.rename),
            onTap: () => Navigator.of(context).pop('rename'),
          ),
          ListTile(
            leading: const Icon(Icons.delete_outline),
            title: Text(l10n.delete),
            onTap: () => Navigator.of(context).pop('delete'),
          ),
        ],
      ),
    ),
  );

  if (!context.mounted) return;
  if (action == 'rename') {
    final name = await promptTextDialog(
      context,
      title: l10n.renameFolderTitle,
      initialValue: folder,
      confirmLabel: l10n.save,
    );
    if (name != null) {
      await store.renameFolder(catKey, folder, name);
    }
  } else if (action == 'delete') {
    await store.deleteFolder(catKey, folder);
  }
}
'''
Path("src/lib/wardrobe_tab.dart").write_text(wardrobe, encoding="utf-8")

# ---------- related_looks.dart: expose detail ----------
p = Path("src/lib/related_looks.dart")
s = p.read_text(encoding="utf-8")
s = s.replace(
    "onTap: () => _openRelatedLookDetail(context, look),",
    "onTap: () => openRelatedLookDetail(context, look),",
)
s = s.replace(
    "Future<void> _openRelatedLookDetail(",
    "Future<void> openRelatedLookDetail(",
)
p.write_text(s, encoding="utf-8")

# ---------- related_looks_tab.dart ----------
looks_tab = r'''import 'dart:io';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'l10n/app_localizations.dart';
import 'models.dart';
import 'related_looks.dart';
import 'theme.dart';
import 'wardrobe_store.dart';
import 'widgets.dart';

class RelatedLooksTab extends StatefulWidget {
  const RelatedLooksTab({super.key});

  @override
  State<RelatedLooksTab> createState() => _RelatedLooksTabState();
}

class _RelatedLooksTabState extends State<RelatedLooksTab> {
  String? _filterItemId;

  @override
  Widget build(BuildContext context) {
    final store = context.watch<WardrobeStore>();
    final l10n = AppLocalizations.of(context)!;
    final filterItem =
        _filterItemId == null ? null : store.itemById(_filterItemId!);

    final looks = filterItem == null
        ? [...store.relatedLooks]
        : store.relatedLooksForItem(filterItem.id);
    looks.sort((a, b) => b.createdAt.compareTo(a.createdAt));

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 10),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  l10n.myLooksTitle,
                  style: AppText.sans(
                    size: 20,
                    weight: FontWeight.w500,
                    color: AppColors.ink,
                  ),
                ),
              ),
              FilledButton.icon(
                onPressed: () => openAddRelatedLookSheet(context),
                icon: const Icon(Icons.add, size: 18),
                label: Text(l10n.addRelatedLook),
              ),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 2, 16, 10),
          child: GestureDetector(
            onTap: () async {
              final id = await _pickFilterItem(context);
              if (id != null || context.mounted) {
                setState(() => _filterItemId = id);
              }
            },
            child: Container(
              height: 58,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              decoration: BoxDecoration(
                color: Colors.white,
                border: Border.all(color: AppColors.rowBorder),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(
                children: [
                  if (filterItem?.imagePath != null)
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.file(
                        File(filterItem!.imagePath!),
                        width: 38,
                        height: 44,
                        fit: BoxFit.cover,
                      ),
                    )
                  else
                    const Icon(
                      Icons.filter_alt_outlined,
                      size: 20,
                      color: AppColors.mutedSoft,
                    ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      filterItem == null
                          ? l10n.filterByClothing
                          : l10n.showingRelatedLooksFor(
                              filterItem.folder ??
                                  categoryLabel(context, filterItem.cat),
                            ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: AppText.sans(
                        size: 12.5,
                        color: AppColors.ink,
                      ),
                    ),
                  ),
                  if (filterItem != null)
                    IconButton(
                      onPressed: () => setState(() => _filterItemId = null),
                      icon: const Icon(Icons.close, size: 18),
                    )
                  else
                    const Icon(
                      Icons.chevron_right,
                      color: AppColors.mutedSoft,
                    ),
                ],
              ),
            ),
          ),
        ),
        Expanded(
          child: looks.isEmpty
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32),
                    child: Text(
                      filterItem == null
                          ? l10n.noLooksYet
                          : l10n.noLooksForSelectedItem,
                      textAlign: TextAlign.center,
                      style: AppText.sans(
                        size: 13,
                        color: AppColors.mutedTag,
                        height: 1.5,
                      ),
                    ),
                  ),
                )
              : GridView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 2, 16, 20),
                  itemCount: looks.length,
                  gridDelegate:
                      const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        mainAxisSpacing: 12,
                        crossAxisSpacing: 12,
                        childAspectRatio: .72,
                      ),
                  itemBuilder: (context, index) {
                    final look = looks[index];
                    final linkedCount = look.itemIds
                        .where((id) => store.itemById(id) != null)
                        .length;
                    return GestureDetector(
                      onTap: () => openRelatedLookDetail(context, look),
                      child: Container(
                        clipBehavior: Clip.antiAlias,
                        decoration: BoxDecoration(
                          color: Colors.white,
                          border: Border.all(color: AppColors.rowBorder),
                          borderRadius: BorderRadius.circular(16),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Expanded(
                              child: Image.file(
                                File(look.imagePath),
                                fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) =>
                                    const DiagonalStripes(),
                              ),
                            ),
                            Padding(
                              padding:
                                  const EdgeInsets.fromLTRB(10, 8, 10, 9),
                              child: Text(
                                l10n.linkedItemsCount(linkedCount),
                                style: AppText.sans(
                                  size: 11,
                                  color: AppColors.muted,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Future<String?> _pickFilterItem(BuildContext context) {
    return showModalBottomSheet<String?>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => const _ClothingFilterSheet(),
    );
  }
}

class _ClothingFilterSheet extends StatefulWidget {
  const _ClothingFilterSheet();

  @override
  State<_ClothingFilterSheet> createState() => _ClothingFilterSheetState();
}

class _ClothingFilterSheetState extends State<_ClothingFilterSheet> {
  String _cat = 'horni';

  @override
  Widget build(BuildContext context) {
    final store = context.watch<WardrobeStore>();
    final l10n = AppLocalizations.of(context)!;
    final items = store.byCat(_cat);

    return SafeArea(
      top: false,
      child: Container(
        height: MediaQuery.of(context).size.height * .78,
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(26)),
        ),
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(18, 16, 18, 10),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      l10n.chooseClothingToFilter,
                      style: AppText.sans(
                        size: 18,
                        weight: FontWeight.w500,
                        color: AppColors.ink,
                      ),
                    ),
                  ),
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(null),
                    child: Text(l10n.allLooks),
                  ),
                ],
              ),
            ),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 14),
              child: Row(
                children: [
                  for (final cat in ['horni', 'dolni', 'saty', 'boty'])
                    Padding(
                      padding: const EdgeInsets.only(right: 7),
                      child: ChoiceChip(
                        label: Text(categoryLabel(context, cat)),
                        selected: _cat == cat,
                        onSelected: (_) => setState(() => _cat = cat),
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            Expanded(
              child: GridView.builder(
                padding: const EdgeInsets.fromLTRB(14, 4, 14, 20),
                itemCount: items.length,
                gridDelegate:
                    const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 3,
                      mainAxisSpacing: 8,
                      crossAxisSpacing: 8,
                      childAspectRatio: .75,
                    ),
                itemBuilder: (context, index) {
                  final item = items[index];
                  return GestureDetector(
                    onTap: () => Navigator.of(context).pop(item.id),
                    child: Container(
                      decoration: BoxDecoration(
                        border: Border.all(color: AppColors.cardBorder),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      padding: const EdgeInsets.all(5),
                      child: Column(
                        children: [
                          Expanded(
                            child: GarmentCard(
                              width: double.infinity,
                              height: double.infinity,
                              imagePath: item.imagePath,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            item.folder ?? categoryLabel(context, item.cat),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: AppText.sans(
                              size: 9.5,
                              color: AppColors.muted,
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
'''
Path("src/lib/related_looks_tab.dart").write_text(looks_tab, encoding="utf-8")

# ---------- localization additions ----------
import json
translations = {
    "addSubcategory": {"en": "Add subcategory", "cs": "Přidat podkategorii", "zh": "添加二级分类"},
    "subcategoryHint": {"en": "e.g. T-shirts", "cs": "např. Trička", "zh": "例如：短袖"},
    "myLooksTitle": {"en": "My outfits", "cs": "Moje outfity", "zh": "我的穿搭"},
    "filterByClothing": {"en": "Filter by clothing", "cs": "Filtrovat podle oblečení", "zh": "按衣物筛选关联穿搭"},
    "showingRelatedLooksFor": {"en": "Showing outfits linked to {name}", "cs": "Outfity propojené s {name}", "zh": "正在查看“{name}”的关联穿搭"},
    "@showingRelatedLooksFor": {
        "en": {"placeholders": {"name": {"type": "String"}}},
        "cs": {"placeholders": {"name": {"type": "String"}}},
        "zh": {"placeholders": {"name": {"type": "String"}}},
    },
    "noLooksYet": {"en": "No outfit photos yet. Add your first full outfit photo.", "cs": "Zatím žádné fotky outfitů. Přidejte první.", "zh": "还没有穿搭照片，先上传一套你的整身穿搭吧。"},
    "noLooksForSelectedItem": {"en": "No saved outfits are linked to this item yet.", "cs": "K tomuto kusu zatím není propojen žádný outfit.", "zh": "这件衣物目前还没有关联任何已保存的整套穿搭。"},
    "chooseClothingToFilter": {"en": "Choose clothing", "cs": "Vyberte oblečení", "zh": "选择一件衣物"},
    "allLooks": {"en": "All", "cs": "Vše", "zh": "全部穿搭"},
}
for locale in ("en", "cs", "zh"):
    path = Path(f"src/lib/l10n/app_{locale}.arb")
    data = json.loads(path.read_text(encoding="utf-8"))
    for key, vals in translations.items():
        data[key] = vals[locale]
    if locale == "zh":
        data["tabWardrobe"] = "衣橱"
        data["tabOutfit"] = "穿搭"
        data["categorySaty"] = "整装"
        data["tabCollections"] = "收藏"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
