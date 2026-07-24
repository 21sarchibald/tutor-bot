def test_server_app_imports():
    import server.main as main

    assert main.app is not None
