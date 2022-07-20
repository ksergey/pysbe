from app.schema import Schema

PATH = '/home/ksergey/dev/pysbe/resources/FixBinary.xml'

def main() -> None:
    schema = Schema.loadFromFile(PATH)
    print(schema)

if __name__ == '__main__':
    main()
