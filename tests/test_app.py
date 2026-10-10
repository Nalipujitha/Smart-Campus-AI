def test_app_creation(app):
    assert app is not None
    assert app.testing is True

def test_static_and_templates_configuration(app):
    assert app.template_folder is not None
    assert app.static_folder is not None
