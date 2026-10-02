# A web server that speaks HTTP/1.1 AND HTTP/2 (thanks to the hypercorn library).
# Three objects of different size: the bigger the file, the longer it takes to send it.
import asyncio
import logging
from hypercorn.asyncio import serve
from hypercorn.config import Config

SIZES = {                              # object -> seconds to send it
    '/large': 3,                       # a large file (a video)
    '/small': 1,                       # a small file (an image)
    '/tiny':  0,                       # a tiny file (an icon)
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s.%(msecs)03d  %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger('server')

async def app(scope, receive, send):  # called once per request
    if scope['type'] != 'http':
        return
    port, path, version = scope['client'][1], scope['path'], scope['http_version']
    log.info('[port %d]  HTTP/%-3s  %-6s arrived', port, version, path)
    await asyncio.sleep(SIZES.get(path, 0))    # "sending" the file takes time
    body = f'You asked for {path}\n'.encode()
    await send({'type': 'http.response.start', 'status': 200,
                'headers': [(b'content-length', str(len(body)).encode())]})
    await send({'type': 'http.response.body', 'body': body})
    log.info('[port %d]  HTTP/%-3s  %-6s answered', port, version, path)

config = Config()
config.bind = ['localhost:8000']
config.accesslog = None                # we print our own log lines
config.loglevel = 'WARNING'
log.info('Server on http://localhost:8000 (HTTP/1.1 and HTTP/2)')
asyncio.run(serve(app, config))
