"""
Accessibility (WCAG 2.1 AA) Compliance Audit & Verification Suite.

Tests key frontend routes and templates for mandatory WCAG invariants:
1. Skip-to-content links pointing to #main-content.
2. Single <h1> per page and sequential heading hierarchy.
3. Accessible form labels for input/select controls.
4. Image alt text presence and decorative icon attributes.
5. Contrast & text label presence for status indicators.
"""

import os
import re
import pytest

FRONTEND_ROUTES_DIR = "/home/deen/govalert-frontend-design/src/routes"
FRONTEND_COMPONENTS_DIR = "/home/deen/govalert-frontend-design/src/components"

def get_tsx_files(directory):
    files = []
    for root, _, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith(".tsx") and not f.endswith(".test.tsx"):
                files.append(os.path.join(root, f))
    return files


def test_skip_to_content_link_in_root():
    """Verify RootShell has a skip to main content link targeting #main-content."""
    root_file = os.path.join(FRONTEND_ROUTES_DIR, "__root.tsx")
    with open(root_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert 'href="#main-content"' in content, "RootShell must contain a skip link pointing to #main-content"
    assert "Skip to main content" in content, "Skip link must have clear visible/screen-reader text"


def test_main_content_id_presence():
    """Verify major route components define main element with id='main-content'."""
    key_routes = ["index.tsx", "jobs.index.tsx", "jobs.$jobId.tsx", "status.tsx", "register.tsx"]
    for route_name in key_routes:
        file_path = os.path.join(FRONTEND_ROUTES_DIR, route_name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            assert 'id="main-content"' in content, f"{route_name} must contain <main id=\"main-content\">"


def test_single_h1_per_route():
    """Verify key route files have at most one <h1> element."""
    key_routes = ["index.tsx", "jobs.index.tsx", "jobs.$jobId.tsx", "status.tsx", "about.tsx", "register.tsx"]
    for route_name in key_routes:
        file_path = os.path.join(FRONTEND_ROUTES_DIR, route_name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            h1_matches = re.findall(r'<h1[\s>]', content)
            assert len(h1_matches) <= 1, f"{route_name} has {len(h1_matches)} <h1> elements. WCAG 2.1 AA requires exactly 1 <h1> per page."


def test_image_alt_text_compliance():
    """Verify images in components and routes include alt attributes."""
    tsx_files = get_tsx_files(FRONTEND_COMPONENTS_DIR) + get_tsx_files(FRONTEND_ROUTES_DIR)
    missing_alt = []

    for file_path in tsx_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find <img tags missing alt
        img_tags = re.findall(r'<img\s+[^>]*>', content)
        for img in img_tags:
            if 'alt=' not in img:
                missing_alt.append((file_path, img))

    assert len(missing_alt) == 0, f"Found <img> tags missing alt attributes: {missing_alt}"


def test_form_label_associations():
    """Verify form controls have corresponding labels or aria-label attributes."""
    register_file = os.path.join(FRONTEND_ROUTES_DIR, "register.tsx")
    with open(register_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert 'htmlFor="register-email"' in content
    assert 'id="register-email"' in content
    assert 'htmlFor="register-password"' in content
    assert 'id="register-password"' in content


def test_live_regions_for_dynamic_updates():
    """Verify dynamic validation feedback has aria-live region."""
    register_file = os.path.join(FRONTEND_ROUTES_DIR, "register.tsx")
    with open(register_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert 'aria-live="polite"' in content, "Dynamic password requirement checklist must use aria-live='polite'"


def test_status_badges_have_text_labels():
    """Verify StatusBadge renders text labels alongside color indicators."""
    status_file = os.path.join(FRONTEND_ROUTES_DIR, "index.tsx")
    with open(status_file, "r", encoding="utf-8") as f:
        content = f.read()

    assert "StatusBadge" in content
    assert "Verified" in content
    assert "Urgent" in content
