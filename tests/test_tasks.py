from tools.tasks.dev import symlink_odoo


def test_symlink_odoo():
    symlink_odoo(clean=True)
