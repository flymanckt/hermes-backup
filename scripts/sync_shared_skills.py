#!/usr/bin/env python3
from pathlib import Path
import shutil
import json
import sys

BASE = Path('/home/kent/.hermes/profiles')
SHARED_ROOT = Path('/home/kent/.hermes/skills')
EXCLUDE = {'consulting', 'finance', 'a-share-stock-data-tencent'}


def iter_profiles():
    return sorted([p for p in BASE.iterdir() if p.is_dir()])


def iter_shared_categories():
    return sorted(
        [p for p in SHARED_ROOT.iterdir() if p.is_dir() and p.name not in EXCLUDE],
        key=lambda p: p.name,
    )


def copy_dir(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    shutil.copytree(src, dst, symlinks=False)


def ensure_shared_category_mirror(profile: Path, category: Path, stats: dict) -> None:
    profile_category = profile / 'skills' / category.name
    if profile_category.is_symlink():
        profile_category.unlink()
        profile_category.mkdir(parents=True, exist_ok=True)
        stats['converted_category_symlinks'] += 1
    else:
        profile_category.mkdir(parents=True, exist_ok=True)

    shared_skills = {p.name: p for p in category.iterdir() if p.is_dir()}

    # 清理旧的共享 skill 软链，改成真实目录镜像
    for entry in list(profile_category.iterdir()):
        if entry.name not in shared_skills:
            continue
        if entry.is_symlink():
            entry.unlink()
            stats['removed_skill_symlinks'] += 1

    for skill_name, shared_skill in sorted(shared_skills.items()):
        dst = profile_category / skill_name
        needs_copy = False
        if dst.is_symlink():
            dst.unlink()
            stats['removed_skill_symlinks'] += 1
            needs_copy = True
        elif not dst.exists():
            needs_copy = True
        elif (dst / 'SKILL.md').exists():
            src_skill = (shared_skill / 'SKILL.md').read_text(encoding='utf-8')
            dst_skill = (dst / 'SKILL.md').read_text(encoding='utf-8')
            if src_skill != dst_skill:
                needs_copy = True
        else:
            backup = dst.with_name(dst.name + '.local-backup')
            if backup.exists():
                if dst.is_dir():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
            else:
                dst.rename(backup)
            stats['backed_up_local_entries'] += 1
            needs_copy = True

        if needs_copy:
            copy_dir(shared_skill, dst)
            stats['copied_skills'] += 1


def main() -> int:
    if not BASE.exists() or not SHARED_ROOT.exists():
        print(json.dumps({'error': 'required path missing', 'base': str(BASE), 'shared_root': str(SHARED_ROOT)}, ensure_ascii=False))
        return 1

    stats = {
        'profiles': 0,
        'categories': 0,
        'copied_skills': 0,
        'converted_category_symlinks': 0,
        'removed_skill_symlinks': 0,
        'backed_up_local_entries': 0,
    }

    categories = list(iter_shared_categories())
    for profile in iter_profiles():
        stats['profiles'] += 1
        for category in categories:
            stats['categories'] += 1
            ensure_shared_category_mirror(profile, category, stats)

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
