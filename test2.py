
# print('vavavar1', vavavar)

# def myFunc(v):
#     global vavavar
#     vavavar = v

# myFunc('hello')

# print('vavavar2', vavavar)

# if True:
#     test="good"

# print('test', test)

# import json
# data = {
#     "id": 1,
#     "name": "Andersen"
# }
# jsonData = json.dumps(data)
# print(jsonData)

import asyncio

async def hello(ser, val):
    print(f'{ser}, {val}')
    return f'{ser}, {val}'

async def r():
    l = ["apple", "pear", "banana"]
    to_get = [hello(idx, value) for idx, value in enumerate(l)]
    await asyncio.wait(to_get)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(r())
    loop.close()