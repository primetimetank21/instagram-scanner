from hello import hello


def test_main():
    assert hello() == "Hello John!"
    assert hello("Jill") == "Hello Jill!"
    assert type(hello()) == str
