from app.schema import Schema
from app.parser import Parser

PATH = '/home/ksergey/dev/pysbe/resources/FixBinary.xml'

def main() -> None:
    parser = Parser(PATH)
    schema = parser.schema
    print(schema)

if __name__ == '__main__':
    main()
