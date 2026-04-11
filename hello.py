def hello(name: str = "John") -> str:
    """Say hello to `name`"""
    phrase: str = f"Hello {name}!"
    print(phrase)
    return phrase


def main() -> None:
    """Code Entrypoint"""
    if __name__ == "__main__":
        hello()


main()
