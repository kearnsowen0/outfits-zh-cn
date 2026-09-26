from pathlib import Path
import json

# ---------- models.dart ----------
p = Path("src/lib/models.dart")
s = p.read_text(encoding="utf-8")
needle = "enum WardrobeTabKind { outfit, wardrobe, collections }"
insert = r'''
/// A user-uploaded full-body outfit photo linked to one or more wardrobe
/// items. It is separate from [SavedOutfit], which is a combination created
/// in the in-app outfit builder.
class RelatedLook {
  final String id;
  String imagePath;
  final List<String> itemIds;
  final int createdAt;

  RelatedLook({
    required this.id,
    required this.imagePath,
    required this.itemIds,
    required this.createdAt,
  });

  Map<String, dynamic> toJson() => {
    'id': id,
    'imagePath': imagePath,
    'itemIds': itemIds,
    'createdAt': createdAt,
  };

  factory RelatedLook.fromJson(Map<String, dynamic> json) => RelatedLook(
    id: json['id'] as String,
    imagePath: json['imagePath'] as String,
    itemIds: (json['itemIds'] as List<dynamic>? ?? [])
        .map((e) => e as String)
        .toList(),
    createdAt: json['createdAt'] as int? ?? 0,
  );
}

'''
if "class RelatedLook" not in s:
    if needle not in s:
        raise SystemExit("models insertion point not found")
    s = s.replace(needle, insert + needle)
p.write_text(s, encoding="utf-8")

# ---------- wardrobe_store.dart ----------
p = Path("src/lib/wardrobe_store.dart")
s = p.read_text(encoding="utf-8")

needle = "  Map<String, List<SavedOutfit>> saved = {};\n  String? folderFilter;"
replace = "  Map<String, List<SavedOutfit>> saved = {};\n\n  /// Full-body outfit photos uploaded by the user and linked to clothes.\n  List<RelatedLook> relatedLooks = [];\n\n  String? folderFilter;"
if "List<RelatedLook> relatedLooks" not in s:
    if needle not in s:
        raise SystemExit("store field insertion point not found")
    s = s.replace(needle, replace)

needle = "    try {\n      final rawKnownFolders = data['knownFolders'] as Map<String, dynamic>?;"
load_block = r'''    try {
      final docsPath = (await getApplicationDocumentsDirectory()).path;
      final rawRelatedLooks = data['relatedLooks'] as List<dynamic>? ?? [];
      final parsedRelatedLooks = <RelatedLook>[];
      for (final e in rawRelatedLooks) {
        try {
          final look = RelatedLook.fromJson(e as Map<String, dynamic>);
          look.imagePath = _resolveImagePath(look.imagePath, docsPath);
          parsedRelatedLooks.add(look);
        } catch (_) {}
      }
      relatedLooks = parsedRelatedLooks;
    } catch (_) {}

'''
if "final rawRelatedLooks = data['relatedLooks']" not in s:
    if needle not in s:
        raise SystemExit("store load insertion point not found")
    s = s.replace(needle, load_block + needle)

needle = "        'saved': saved.map(\n          (key, value) => MapEntry(key, value.map((e) => e.toJson()).toList()),\n        ),\n        'knownFolders': knownFolders,"
replace = "        'saved': saved.map(\n          (key, value) => MapEntry(key, value.map((e) => e.toJson()).toList()),\n        ),\n        'relatedLooks': relatedLooks.map((e) => e.toJson()).toList(),\n        'knownFolders': knownFolders,"
if "'relatedLooks': relatedLooks.map" not in s:
    if needle not in s:
        raise SystemExit("store persist insertion point not found")
    s = s.replace(needle, replace)

needle = "  Future<void> deleteItem(ClothingItem it) async {"
methods = r'''  List<RelatedLook> relatedLooksForItem(String itemId) {
    final result = relatedLooks
        .where((look) => look.itemIds.contains(itemId))
        .toList();
    result.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return result;
  }

  Future<RelatedLook> addRelatedLook({
    required String sourceImagePath,
    required List<String> itemIds,
  }) async {
    final imagePath = await _newImageCopy(sourceImagePath);
    final now = DateTime.now();
    final look = RelatedLook(
      id: 'related-look-${now.microsecondsSinceEpoch}',
      imagePath: imagePath,
      itemIds: itemIds.toSet().toList(),
      createdAt: now.millisecondsSinceEpoch,
    );
    relatedLooks = [...relatedLooks, look];
    notifyListeners();
    await _persist();
    return look;
  }

  Future<void> deleteRelatedLook(RelatedLook look) async {
    relatedLooks = relatedLooks.where((x) => x.id != look.id).toList();
    notifyListeners();
    await _persist();
    try {
      final file = File(look.imagePath);
      if (await file.exists()) await file.delete();
    } catch (_) {
      // Best-effort image cleanup.
    }
  }

'''
if "Future<RelatedLook> addRelatedLook" not in s:
    if needle not in s:
        raise SystemExit("store methods insertion point not found")
    s = s.replace(needle, methods + needle)

# Keep deleted clothing references out of future related-look displays.
old = """  Future<void> deleteItem(ClothingItem it) async {
    items = items.where((x) => x.id != it.id).toList();
    layers = layers.where((id) => id != it.id).toList();
    notifyListeners();"""
new = """  Future<void> deleteItem(ClothingItem it) async {
    items = items.where((x) => x.id != it.id).toList();
    layers = layers.where((id) => id != it.id).toList();
    relatedLooks = [
      for (final look in relatedLooks)
        if (look.itemIds.any((id) => id != it.id))
          RelatedLook(
            id: look.id,
            imagePath: look.imagePath,
            itemIds: look.itemIds.where((id) => id != it.id).toList(),
            createdAt: look.createdAt,
          ),
    ];
    notifyListeners();"""
if "look.itemIds.where((id) => id != it.id)" not in s:
    if old not in s:
        raise SystemExit("deleteItem patch point not found")
    s = s.replace(old, new)

p.write_text(s, encoding="utf-8")

# ---------- related_looks.dart ----------
related = r'''import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import 'l10n/app_localizations.dart';
import 'models.dart';
import 'theme.dart';
import 'wardrobe_store.dart';
import 'widgets.dart';

Future<void> openRelatedLooksSheet(BuildContext context, String itemId) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (ctx) => _RelatedLooksSheet(itemId: itemId),
  );
}

class _RelatedLooksSheet extends StatelessWidget {
  final String itemId;
  const _RelatedLooksSheet({required this.itemId});

  @override
  Widget build(BuildContext context) {
    final store = context.watch<WardrobeStore>();
    final l10n = AppLocalizations.of(context)!;
    final looks = store.relatedLooksForItem(itemId);

    return SafeArea(
      top: false,
      child: Container(
        constraints: BoxConstraints(
          maxHeight: MediaQuery.of(context).size.height * .88,
        ),
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(26)),
        ),
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 18, 14, 12),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      l10n.relatedLooksTitle,
                      style: AppText.sans(
                        size: 20,
                        weight: FontWeight.w300,
                        color: AppColors.ink,
                      ),
                    ),
                  ),
                  TextButton.icon(
                    onPressed: () => openAddRelatedLookSheet(
                      context,
                      presetItemId: itemId,
                    ),
                    icon: const Icon(Icons.add, size: 18),
                    label: Text(l10n.addRelatedLook),
                  ),
                ],
              ),
            ),
            Expanded(
              child: looks.isEmpty
                  ? Center(
                      child: Padding(
                        padding: const EdgeInsets.all(28),
                        child: Text(
                          l10n.noRelatedLooks,
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
                      padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
                      itemCount: looks.length,
                      gridDelegate:
                          const SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: 2,
                            mainAxisSpacing: 10,
                            crossAxisSpacing: 10,
                            childAspectRatio: .72,
                          ),
                      itemBuilder: (context, index) {
                        final look = looks[index];
                        return _RelatedLookTile(look: look);
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RelatedLookTile extends StatelessWidget {
  final RelatedLook look;
  const _RelatedLookTile({required this.look});

  @override
  Widget build(BuildContext context) {
    final store = context.watch<WardrobeStore>();
    final l10n = AppLocalizations.of(context)!;
    final linked = [
      for (final id in look.itemIds)
        if (store.itemById(id) case final item?) item,
    ];

    return GestureDetector(
      onTap: () => _openRelatedLookDetail(context, look),
      child: Container(
        clipBehavior: Clip.antiAlias,
        decoration: BoxDecoration(
          border: Border.all(color: AppColors.cardBorder),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: Image.file(
                File(look.imagePath),
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const DiagonalStripes(),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(9),
              child: Text(
                l10n.linkedItemsCount(linked.length),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: AppText.sans(size: 11.5, color: AppColors.muted),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

Future<void> _openRelatedLookDetail(
  BuildContext context,
  RelatedLook look,
) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (ctx) => _RelatedLookDetail(lookId: look.id),
  );
}

class _RelatedLookDetail extends StatelessWidget {
  final String lookId;
  const _RelatedLookDetail({required this.lookId});

  @override
  Widget build(BuildContext context) {
    final store = context.watch<WardrobeStore>();
    final l10n = AppLocalizations.of(context)!;
    RelatedLook? look;
    for (final x in store.relatedLooks) {
      if (x.id == lookId) {
        look = x;
        break;
      }
    }
    if (look == null) return const SizedBox.shrink();

    final linked = [
      for (final id in look.itemIds)
        if (store.itemById(id) case final item?) item,
    ];

    return SafeArea(
      top: false,
      child: Container(
        constraints: BoxConstraints(
          maxHeight: MediaQuery.of(context).size.height * .92,
        ),
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(26)),
        ),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 30),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                l10n.relatedLookDetailTitle,
                style: AppText.sans(
                  size: 20,
                  weight: FontWeight.w300,
                  color: AppColors.ink,
                ),
              ),
              const SizedBox(height: 14),
              ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Image.file(
                  File(look.imagePath),
                  width: double.infinity,
                  fit: BoxFit.fitWidth,
                  errorBuilder: (_, __, ___) => const SizedBox(
                    height: 260,
                    child: DiagonalStripes(),
                  ),
                ),
              ),
              const SizedBox(height: 18),
              Text(
                l10n.linkedClothes,
                style: AppText.sans(size: 13, color: AppColors.ink),
              ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final item in linked)
                    Container(
                      width: 72,
                      padding: const EdgeInsets.all(5),
                      decoration: BoxDecoration(
                        border: Border.all(color: AppColors.cardBorder),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(
                        children: [
                          SizedBox(
                            height: 82,
                            child: GarmentCard(
                              width: 62,
                              height: 82,
                              imagePath: item.imagePath,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            categoryLabel(context, item.cat),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: AppText.sans(
                              size: 10,
                              color: AppColors.muted,
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: () async {
                    await store.deleteRelatedLook(look!);
                    if (context.mounted) Navigator.of(context).pop();
                  },
                  child: Text(l10n.deleteRelatedLook),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

Future<void> openAddRelatedLookSheet(
  BuildContext context, {
  String? presetItemId,
}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (ctx) => _AddRelatedLookSheet(presetItemId: presetItemId),
  );
}

class _AddRelatedLookSheet extends StatefulWidget {
  final String? presetItemId;
  const _AddRelatedLookSheet({this.presetItemId});

  @override
  State<_AddRelatedLookSheet> createState() => _AddRelatedLookSheetState();
}

class _AddRelatedLookSheetState extends State<_AddRelatedLookSheet> {
  String? _imagePath;
  final Set<String> _selectedIds = {};
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    if (widget.presetItemId != null) {
      _selectedIds.add(widget.presetItemId!);
    }
  }

  Future<void> _pick(ImageSource source) async {
    final picker = ImagePicker();
    final file = await picker.pickImage(source: source, imageQuality: 88);
    if (file != null && mounted) setState(() => _imagePath = file.path);
  }

  Future<void> _save() async {
    if (_imagePath == null || _selectedIds.isEmpty || _saving) return;
    setState(() => _saving = true);
    try {
      final store = context.read<WardrobeStore>();
      await store.addRelatedLook(
        sourceImagePath: _imagePath!,
        itemIds: _selectedIds.toList(),
      );
      store.flash(AppLocalizations.of(context)!.relatedLookSaved);
      if (mounted) Navigator.of(context).pop();
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final store = context.watch<WardrobeStore>();
    final l10n = AppLocalizations.of(context)!;

    return SafeArea(
      top: false,
      child: Container(
        constraints: BoxConstraints(
          maxHeight: MediaQuery.of(context).size.height * .92,
        ),
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(26)),
        ),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 34),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                l10n.addRelatedLook,
                style: AppText.sans(
                  size: 20,
                  weight: FontWeight.w300,
                  color: AppColors.ink,
                ),
              ),
              const SizedBox(height: 16),
              if (_imagePath != null)
                ClipRRect(
                  borderRadius: BorderRadius.circular(14),
                  child: Image.file(
                    File(_imagePath!),
                    height: 250,
                    width: double.infinity,
                    fit: BoxFit.cover,
                  ),
                )
              else
                Container(
                  height: 180,
                  width: double.infinity,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: AppColors.cardFill,
                    border: Border.all(color: AppColors.cardBorder),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Text(
                    l10n.selectFullLookPhoto,
                    style: AppText.sans(
                      size: 13,
                      color: AppColors.mutedTag,
                    ),
                  ),
                ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => _pick(ImageSource.camera),
                      child: Text(l10n.takePhoto),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => _pick(ImageSource.gallery),
                      child: Text(l10n.fromGallery),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              Text(
                l10n.selectLinkedClothes,
                style: AppText.sans(size: 13, color: AppColors.ink),
              ),
              const SizedBox(height: 6),
              Text(
                l10n.selectLinkedClothesHint,
                style: AppText.sans(
                  size: 11.5,
                  color: AppColors.mutedTag,
                  height: 1.4,
                ),
              ),
              const SizedBox(height: 12),
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: store.items.length,
                gridDelegate:
                    const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 3,
                      mainAxisSpacing: 8,
                      crossAxisSpacing: 8,
                      childAspectRatio: .78,
                    ),
                itemBuilder: (context, index) {
                  final item = store.items[index];
                  final selected = _selectedIds.contains(item.id);
                  return GestureDetector(
                    onTap: () => setState(() {
                      if (selected) {
                        _selectedIds.remove(item.id);
                      } else {
                        _selectedIds.add(item.id);
                      }
                    }),
                    child: Container(
                      decoration: BoxDecoration(
                        border: Border.all(
                          color: selected ? AppColors.ink : AppColors.cardBorder,
                          width: selected ? 2 : 1,
                        ),
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
                              color: selected
                                  ? AppColors.ink
                                  : AppColors.muted,
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: _imagePath != null &&
                          _selectedIds.isNotEmpty &&
                          !_saving
                      ? _save
                      : null,
                  child: _saving
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Text(l10n.saveRelatedLook),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
'''
Path("src/lib/related_looks.dart").write_text(related, encoding="utf-8")

# ---------- sheets.dart ----------
p = Path("src/lib/sheets.dart")
s = p.read_text(encoding="utf-8")
if "import 'related_looks.dart';" not in s:
    s = s.replace("import 'models.dart';", "import 'models.dart';\nimport 'related_looks.dart';")

needle = """        const SizedBox(height: 18),
        Row(
          children: [
            Expanded(
              child: GestureDetector(
                onTap: () {
                  store.useItem(cur);"""
block = """        const SizedBox(height: 18),
        GestureDetector(
          onTap: () => openRelatedLooksSheet(context, cur.id),
          child: Container(
            height: 48,
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            decoration: BoxDecoration(
              border: Border.all(color: AppColors.cardBorder),
              borderRadius: BorderRadius.circular(24),
            ),
            child: Row(
              children: [
                const Icon(Icons.checkroom_outlined, size: 19),
                const SizedBox(width: 9),
                Expanded(
                  child: Text(
                    l10n.relatedLooksButton(
                      store.relatedLooksForItem(cur.id).length,
                    ),
                    style: AppText.sans(size: 13, color: AppColors.ink),
                  ),
                ),
                const Icon(Icons.chevron_right, size: 20),
              ],
            ),
          ),
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: GestureDetector(
                onTap: () {
                  store.useItem(cur);"""
if "l10n.relatedLooksButton(" not in s:
    if needle not in s:
        raise SystemExit("item detail UI insertion point not found")
    s = s.replace(needle, block)
p.write_text(s, encoding="utf-8")

# ---------- localizations ----------
translations = {
    "relatedLooksTitle": {
        "en": "Related outfits",
        "cs": "Propojené outfity",
        "zh": "关联穿搭",
    },
    "relatedLooksButton": {
        "en": "Related outfits ({count})",
        "cs": "Propojené outfity ({count})",
        "zh": "关联穿搭（{count}）",
    },
    "@relatedLooksButton": {
        "en": {"placeholders": {"count": {"type": "int"}}},
        "cs": {"placeholders": {"count": {"type": "int"}}},
        "zh": {"placeholders": {"count": {"type": "int"}}},
    },
    "addRelatedLook": {
        "en": "Add related outfit",
        "cs": "Přidat propojený outfit",
        "zh": "添加关联穿搭",
    },
    "noRelatedLooks": {
        "en": "No related outfits yet. Add a full-body outfit photo and link it to clothes in your wardrobe.",
        "cs": "Zatím žádné propojené outfity. Přidejte fotku celého outfitu a propojte ji s oblečením v šatníku.",
        "zh": "还没有关联穿搭。上传一张整身穿搭照片，并关联衣橱中已经添加的衣物。",
    },
    "relatedLookDetailTitle": {
        "en": "Related outfit",
        "cs": "Propojený outfit",
        "zh": "关联穿搭详情",
    },
    "linkedClothes": {
        "en": "Linked clothes",
        "cs": "Propojené oblečení",
        "zh": "已关联衣物",
    },
    "linkedItemsCount": {
        "en": "{count} linked items",
        "cs": "{count} propojených kusů",
        "zh": "关联 {count} 件衣物",
    },
    "@linkedItemsCount": {
        "en": {"placeholders": {"count": {"type": "int"}}},
        "cs": {"placeholders": {"count": {"type": "int"}}},
        "zh": {"placeholders": {"count": {"type": "int"}}},
    },
    "deleteRelatedLook": {
        "en": "Delete related outfit",
        "cs": "Smazat propojený outfit",
        "zh": "删除关联穿搭",
    },
    "selectFullLookPhoto": {
        "en": "Select a full-body outfit photo",
        "cs": "Vyberte fotku celého outfitu",
        "zh": "选择一张整身穿搭照片",
    },
    "selectLinkedClothes": {
        "en": "Select linked clothes",
        "cs": "Vyberte propojené oblečení",
        "zh": "选择要关联的衣物",
    },
    "selectLinkedClothesHint": {
        "en": "Choose every wardrobe item shown in this outfit photo.",
        "cs": "Vyberte všechny kusy ze šatníku, které jsou na této fotce outfitu.",
        "zh": "把这张穿搭照片中出现的上装、下装、鞋子等已有衣物全部勾选上。",
    },
    "saveRelatedLook": {
        "en": "Save related outfit",
        "cs": "Uložit propojený outfit",
        "zh": "保存关联穿搭",
    },
    "relatedLookSaved": {
        "en": "Related outfit saved",
        "cs": "Propojený outfit uložen",
        "zh": "关联穿搭已保存",
    },
}

for locale in ("en", "cs"):
    path = Path(f"src/lib/l10n/app_{locale}.arb")
    data = json.loads(path.read_text(encoding="utf-8"))
    for key, vals in translations.items():
        data[key] = vals[locale]
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

zh_path = Path("src/lib/l10n/app_zh.arb")
zh_data = json.loads(zh_path.read_text(encoding="utf-8"))
for key, vals in translations.items():
    zh_data[key] = vals["zh"]
zh_path.write_text(
    json.dumps(zh_data, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
