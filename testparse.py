import asbison


while True:
    try:
        s = input('[cmd] :')
    except EOFError:
        break
    if not s:
        continue
    result = asbison.parse(s, debug=True)
    print(result)
